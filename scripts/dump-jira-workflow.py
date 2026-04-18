#!/usr/bin/env python3
"""Dump the SPE Jira workflow to workspaces/patch/jira-workflow.yaml.

Why this exists
    Jira transition IDs are workflow-local and mutable. Hardcoding them in
    templates means every workflow edit silently breaks automation. This
    script treats the IDs as derived data: it queries Jira, writes them to
    a single YAML file, and templates reference the IDs by symbolic name.

Usage
    op run --env-file=.op.env -- python3 scripts/dump-jira-workflow.py

    or set env vars directly:

    JIRA_CLIENT_ID=... \
    JIRA_CLIENT_SECRET=... \
    JIRA_CLOUD_ID=... \
    python3 scripts/dump-jira-workflow.py

Env vars
    JIRA_CLIENT_ID       — OAuth client ID (1Password: Patch/Jira OAuth)
    JIRA_CLIENT_SECRET   — OAuth client secret
    JIRA_CLOUD_ID        — sc0red.atlassian.net cloud UUID
    PROJECT_KEY          — defaults to SPE

When to re-run
    - After any Jira workflow edit (statuses added / renamed, transitions changed)
    - When a template starts getting 400 "transition not valid" errors
    - Nightly on EC2 via cron for drift detection

Field options
    Field option IDs (Risk=Low=10025, etc.) are hand-maintained in the
    FIELD_OPTIONS and USER_IDS dicts below — they rarely change. If Jira's
    field configuration changes, edit these dicts and re-run.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


PROJECT_KEY = os.environ.get("PROJECT_KEY", "SPE")
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "workspaces" / "patch" / "jira-workflow.yaml"


FIELD_OPTIONS: dict[str, dict[str, str]] = {
    "risk": {
        "no_risk": "10024",
        "low":     "10025",
        "medium":  "10026",
        "high":    "10027",
    },
    "intensity": {
        "no_intensity": "10028",
        "low":          "10029",
        "medium":       "10030",
        "high":         "10031",
    },
    "velocity_impact": {
        "neutral":         "10041",
        "weak_positive":   "10042",
        "strong_positive": "10043",
        "negative":        "10044",
    },
}


USER_IDS: dict[str, str] = {
    "patch": "712020:2fbdb38e-012b-43a6-b286-4339c24baabc",
}


WANTED_CUSTOM_FIELDS: dict[str, str] = {
    "Risk":            "risk",
    "Intensity":       "intensity",
    "Business Value":  "business_value",
    "Velocity Impact": "velocity_impact",
    "Story Points":    "story_points",
}


def main() -> int:
    client_id = os.environ["JIRA_CLIENT_ID"]
    client_secret = os.environ["JIRA_CLIENT_SECRET"]
    cloud_id = os.environ["JIRA_CLOUD_ID"]

    token = fetch_oauth_token(client_id, client_secret)
    base = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3"

    statuses = fetch_project_statuses(base, token)
    sample_key = find_sample_issue_key(base, token)
    transitions = fetch_transitions(base, token, sample_key)
    custom_fields = fetch_custom_fields(base, token)

    write_yaml(
        path=OUTPUT_PATH,
        cloud_id=cloud_id,
        sample_issue=sample_key,
        statuses=statuses,
        transitions=transitions,
        custom_fields=custom_fields,
    )
    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)} (sampled transitions from {sample_key})")
    return 0


def http_json(
    method: str,
    url: str,
    token: str | None = None,
    body: dict | None = None,
) -> dict | list:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()

    req = urllib.request.Request(url, method=method, headers=headers, data=data)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} on {method} {url}: {e.read().decode(errors='replace')}")


def fetch_oauth_token(client_id: str, client_secret: str) -> str:
    response = http_json(
        "POST",
        "https://auth.atlassian.com/oauth/token",
        body={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )
    return response["access_token"]


def fetch_project_statuses(base: str, token: str) -> dict[str, dict[str, str]]:
    """Collect unique statuses across all issue types for PROJECT_KEY."""
    data = http_json("GET", f"{base}/project/{PROJECT_KEY}/statuses", token)
    seen: dict[str, dict[str, str]] = {}
    for issue_type in data:
        for status in issue_type.get("statuses", []):
            key = slugify(status["name"])
            if key not in seen:
                seen[key] = {
                    "id": status["id"],
                    "name": status["name"],
                    "category": status["statusCategory"]["key"],
                }
    return dict(sorted(seen.items()))


def find_sample_issue_key(base: str, token: str) -> str:
    data = http_json(
        "POST",
        f"{base}/search/jql",
        token,
        body={
            "jql": f"project = {PROJECT_KEY} ORDER BY created DESC",
            "fields": ["summary"],
            "maxResults": 1,
        },
    )
    issues = data.get("issues") or []
    if not issues:
        sys.exit(f"No issues in project {PROJECT_KEY} — cannot sample transitions.")
    return issues[0]["key"]


def fetch_transitions(base: str, token: str, issue_key: str) -> dict[str, dict[str, str]]:
    """All transitions reachable from the sample issue.

    SPE workflow is team-managed with 'any status' transitions, so the set
    returned here is the full transition catalog regardless of the sample's
    current state.
    """
    url = f"{base}/issue/{issue_key}/transitions?includeUnavailableTransitions=true"
    data = http_json("GET", url, token)
    out: dict[str, dict[str, str]] = {}
    for t in data.get("transitions", []):
        key = "to_" + slugify(t["to"]["name"])
        out[key] = {
            "id": t["id"],
            "name": t["name"],
            "to": t["to"]["name"],
        }
    return dict(sorted(out.items()))


def fetch_custom_fields(base: str, token: str) -> dict[str, str]:
    data = http_json("GET", f"{base}/field", token)
    out: dict[str, str] = {}
    for field in data:
        name = field.get("name")
        if name in WANTED_CUSTOM_FIELDS and field.get("id", "").startswith("customfield_"):
            out[WANTED_CUSTOM_FIELDS[name]] = field["id"]
    missing = set(WANTED_CUSTOM_FIELDS.values()) - set(out)
    if missing:
        print(f"warning: missing custom fields {missing}", file=sys.stderr)
    return dict(sorted(out.items()))


def slugify(name: str) -> str:
    return (
        name.lower()
        .replace("&", "and")
        .replace("/", "_")
        .replace("-", "_")
        .replace(" ", "_")
    )


def write_yaml(
    *,
    path: Path,
    cloud_id: str,
    sample_issue: str,
    statuses: dict[str, dict[str, str]],
    transitions: dict[str, dict[str, str]],
    custom_fields: dict[str, str],
) -> None:
    """Hand-roll the YAML — avoids a PyYAML dependency."""
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

    lines: list[str] = [
        "# Generated by scripts/dump-jira-workflow.py — do not edit by hand.",
        "# Re-run the script when the Jira workflow changes.",
        "",
        f"project: {PROJECT_KEY}",
        f"cloud_id: {cloud_id}",
        f"generated_at: {now_iso}",
        f"sampled_from_issue: {sample_issue}",
        "",
        "statuses:",
    ]
    for key, meta in statuses.items():
        lines.append(
            f'  {key}: {{ id: "{meta["id"]}", name: "{meta["name"]}", category: "{meta["category"]}" }}'
        )

    lines += ["", "transitions:"]
    for key, meta in transitions.items():
        lines.append(
            f'  {key}: {{ id: "{meta["id"]}", name: "{meta["name"]}", to: "{meta["to"]}" }}'
        )

    lines += ["", "custom_fields:"]
    for key, field_id in custom_fields.items():
        lines.append(f"  {key}: {field_id}")

    lines += ["", "field_options:"]
    for field_slug, options in FIELD_OPTIONS.items():
        lines.append(f"  {field_slug}:")
        for opt_slug, opt_id in options.items():
            lines.append(f'    {opt_slug}: "{opt_id}"')

    lines += ["", "user_ids:"]
    for slug, account_id in USER_IDS.items():
        lines.append(f'  {slug}: "{account_id}"')

    path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
