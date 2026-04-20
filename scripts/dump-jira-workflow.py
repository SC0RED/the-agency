#!/usr/bin/env python3
"""Dump the SPE Jira workflow to workspaces/patch/jira-workflow.yaml.

Why this exists
    When the Jira workflow changes (new status, renamed transition, new
    custom field), the authoritative Jira-ID doc at
    workspaces/patch/docs/jira-ids.md goes stale. This script queries live
    Jira and writes a human-readable YAML dump you can eyeball to update
    that doc.

    The dump is not runtime-consumed — templates carry the literal IDs via
    {{doc:docs/jira-ids.md}}. Think of jira-workflow.yaml as a
    "what-does-Jira-say-right-now" snapshot for humans.

Usage (on the EC2)
    JIRA_USER_EMAIL=$(op item get "Service Account Auth Token: Jira" \
        --vault Engineering --fields username)
    JIRA_API_TOKEN=$(op item get "Service Account Auth Token: Jira" \
        --vault Engineering --fields credential --reveal)
    JIRA_CLOUD_ID=10449a34-7d09-4681-85d9-038414693fbd \
    JIRA_USER_EMAIL="$JIRA_USER_EMAIL" \
    JIRA_API_TOKEN="$JIRA_API_TOKEN" \
    python3 scripts/dump-jira-workflow.py

    Elsewhere, any Atlassian account + API token works — pass the same
    three env vars. Generate tokens at id.atlassian.com → Security →
    API tokens.

Env vars
    JIRA_USER_EMAIL  — Atlassian account the API token was generated under
    JIRA_API_TOKEN   — API token (secret)
    JIRA_CLOUD_ID    — sc0red.atlassian.net cloud UUID
    PROJECT_KEY      — defaults to SPE

When to re-run
    - After any Jira workflow edit
    - When docs/jira-ids.md feels out of date
    - When a transition starts doing something unexpected

Known limitations
    - Custom-field lookup via /field by display name is flaky — some
      fields may show as missing. Cross-check against the Atlassian UI
      if you see warnings.
    - If two transitions point at the same destination status (e.g.
      "Plan Approved" and a global "Manual"), the dict collapses to
      whichever sorted last. jira-ids.md manually resolves these.
"""

from __future__ import annotations

import base64
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
    email = os.environ["JIRA_USER_EMAIL"]
    api_token = os.environ["JIRA_API_TOKEN"]
    cloud_id = os.environ["JIRA_CLOUD_ID"]

    auth_header = build_basic_auth(email, api_token)
    base = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3"

    statuses = fetch_project_statuses(base, auth_header)
    sample_key = find_sample_issue_key(base, auth_header)
    transitions = fetch_transitions(base, auth_header, sample_key)
    custom_fields = fetch_custom_fields(base, auth_header)

    write_yaml(
        path=OUTPUT_PATH,
        cloud_id=cloud_id,
        sample_issue=sample_key,
        statuses=statuses,
        transitions=transitions,
        custom_fields=custom_fields,
    )
    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)} (sampled transitions from {sample_key})")
    print("Remember to sync workspaces/patch/docs/jira-ids.md with anything that changed.")
    return 0


def build_basic_auth(email: str, api_token: str) -> str:
    raw = f"{email}:{api_token}".encode()
    return "Basic " + base64.b64encode(raw).decode()


def http_json(
    method: str,
    url: str,
    auth_header: str | None = None,
    body: dict | None = None,
) -> dict | list:
    headers = {"Accept": "application/json"}
    if auth_header:
        headers["Authorization"] = auth_header
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


def fetch_project_statuses(base: str, auth_header: str) -> dict[str, dict[str, str]]:
    """Collect unique statuses across all issue types for PROJECT_KEY."""
    data = http_json("GET", f"{base}/project/{PROJECT_KEY}/statuses", auth_header)
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


def find_sample_issue_key(base: str, auth_header: str) -> str:
    data = http_json(
        "POST",
        f"{base}/search/jql",
        auth_header,
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


def fetch_transitions(base: str, auth_header: str, issue_key: str) -> dict[str, dict[str, str]]:
    """All transitions reachable from the sample issue.

    SPE workflow is team-managed with 'any status' transitions, so the set
    returned here is the full transition catalog regardless of the sample's
    current state.
    """
    url = f"{base}/issue/{issue_key}/transitions?includeUnavailableTransitions=true"
    data = http_json("GET", url, auth_header)
    out: dict[str, dict[str, str]] = {}
    for t in data.get("transitions", []):
        key = "to_" + slugify(t["to"]["name"])
        out[key] = {
            "id": t["id"],
            "name": t["name"],
            "to": t["to"]["name"],
        }
    return dict(sorted(out.items()))


def fetch_custom_fields(base: str, auth_header: str) -> dict[str, str]:
    data = http_json("GET", f"{base}/field", auth_header)
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
        "# Snapshot only, not runtime-authoritative. Templates read",
        "# workspaces/patch/docs/jira-ids.md; sync that doc with anything",
        "# that changed here.",
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
