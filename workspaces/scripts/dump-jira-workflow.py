#!/usr/bin/env python3
"""Regenerate workspaces/shared/jira-ids-reference.md from live Jira.

Why this exists
    When the Jira workflow changes (new status, renamed transition, new
    custom field), the authoritative Jira-ID reference goes stale —
    which is how transitions land tickets in the wrong status. This
    script queries live Jira and rewrites the reference doc in place.

    The reference doc is the only runtime-authoritative artifact for
    Jira IDs. Templates carry literal numbers copied from it. There is
    no intermediate YAML or generated-YAML-to-doc translation step.

Usage (on the EC2, credentials in 1Password)
    JIRA_USER_EMAIL=$(op item get "Service Account Auth Token: Jira" \\
        --vault Engineering --fields username) \\
    JIRA_API_TOKEN=$(op item get "Service Account Auth Token: Jira" \\
        --vault Engineering --fields credential --reveal) \\
    JIRA_CLOUD_ID=10449a34-7d09-4681-85d9-038414693fbd \\
    python3 workspaces/shared/tools/dump-jira-workflow.py

    Elsewhere, any Atlassian account + API token works — pass the same
    three env vars. Generate tokens at id.atlassian.com → Security →
    API tokens.

Env vars
    JIRA_USER_EMAIL  — Atlassian account the API token was generated under
    JIRA_API_TOKEN   — API token (secret)
    JIRA_CLOUD_ID    — sc0red.atlassian.net cloud UUID
    PROJECT_KEY      — defaults to SPE

When to re-run
    - After any Jira workflow edit (new status, renamed transition)
    - When a transitionJiraIssue call behaves unexpectedly — the script's
      output is the most reliable confirmation of what IDs mean now

Known limitations
    - Custom-field lookup via /field by display name is sometimes flaky;
      missing fields fall back to the hand-maintained defaults below.
    - Multiple transitions to the same destination are both listed (the
      reference card shows everything; callers pick the right one based
      on intended workflow gate, e.g. "Plan Approved" vs a generic
      "Manual" transition to Ready for Development).
"""

from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


PROJECT_KEY = os.environ.get("PROJECT_KEY", "SPE")
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "workspaces" / "shared" / "jira-ids-reference.md"


# Hand-maintained dicts. Custom-field lookups by display name are flaky
# through /field; these serve as defaults the API can override if it
# does return them. Field option IDs (Low/Medium/High etc.) aren't
# exposed through a single endpoint, so they stay here.

DEFAULT_CUSTOM_FIELDS: dict[str, str] = {
    "business_value":  "customfield_10065",
    "intensity":       "customfield_10039",
    "risk":            "customfield_10038",
    "story_points":    "customfield_10016",
    "velocity_impact": "customfield_10064",
}

WANTED_CUSTOM_FIELDS: dict[str, str] = {
    "Risk":            "risk",
    "Intensity":       "intensity",
    "Business Value":  "business_value",
    "Velocity Impact": "velocity_impact",
    "Story Points":    "story_points",
}

FIELD_OPTIONS: dict[str, list[tuple[str, str]]] = {
    "Risk (customfield_10038)": [
        ("No Risk", "10024"),
        ("Low",     "10025"),
        ("Medium",  "10026"),
        ("High",    "10027"),
    ],
    "Intensity (customfield_10039)": [
        ("No Intensity", "10028"),
        ("Low",          "10029"),
        ("Medium",       "10030"),
        ("High",         "10031"),
    ],
    "Velocity Impact (customfield_10064)": [
        ("Neutral",         "10041"),
        ("Weak Positive",   "10042"),
        ("Strong Positive", "10043"),
        ("Negative",        "10044"),
    ],
}

PATCH_ACCOUNT_ID = "712020:2fbdb38e-012b-43a6-b286-4339c24baabc"


def main() -> int:
    email = os.environ["JIRA_USER_EMAIL"]
    api_token = os.environ["JIRA_API_TOKEN"]
    cloud_id = os.environ["JIRA_CLOUD_ID"]

    auth_header = build_basic_auth(email, api_token)
    base = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3"

    sample_key = find_sample_issue_key(base, auth_header)
    transitions = fetch_transitions(base, auth_header, sample_key)
    custom_fields = fetch_custom_fields(base, auth_header)

    markdown = render_markdown(
        cloud_id=cloud_id,
        transitions=transitions,
        custom_fields=custom_fields,
    )
    OUTPUT_PATH.write_text(markdown)
    rel = OUTPUT_PATH.relative_to(REPO_ROOT)
    print(f"Wrote {rel} (sampled transitions from {sample_key})")
    print("Review the diff, commit if it looks right.")
    return 0


def build_basic_auth(email: str, api_token: str) -> str:
    raw = f"{email}:{api_token}".encode()
    return "Basic " + base64.b64encode(raw).decode()


def http_json(
    method: str,
    url: str,
    auth_header: str,
    body: dict | None = None,
) -> dict | list:
    headers = {"Accept": "application/json", "Authorization": auth_header}
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


def fetch_transitions(
    base: str, auth_header: str, issue_key: str
) -> list[dict[str, str]]:
    """All transitions reachable from the sample issue.

    SPE is a team-managed workflow with many 'any status' global
    transitions, so querying from a single issue returns the full
    catalog. Returned as a list (not dict) so multiple transitions to
    the same destination both appear.
    """
    url = f"{base}/issue/{issue_key}/transitions?includeUnavailableTransitions=true"
    data = http_json("GET", url, auth_header)
    out: list[dict[str, str]] = []
    for t in data.get("transitions", []):
        out.append({
            "id": str(t["id"]),
            "name": t["name"],
            "to": t["to"]["name"],
        })
    # Sort by destination name, then by numeric id.
    out.sort(key=lambda r: (r["to"], int(r["id"])))
    return out


def fetch_custom_fields(base: str, auth_header: str) -> dict[str, str]:
    """Resolve the custom-field IDs we care about by display name.

    Falls back to DEFAULT_CUSTOM_FIELDS for anything /field doesn't
    return — the endpoint is flaky for some field types and we'd rather
    ship known-good defaults than write "missing" into the doc.
    """
    data = http_json("GET", f"{base}/field", auth_header)
    out: dict[str, str] = dict(DEFAULT_CUSTOM_FIELDS)
    found: set[str] = set()
    for field in data:
        name = field.get("name")
        if name in WANTED_CUSTOM_FIELDS and field.get("id", "").startswith("customfield_"):
            slug = WANTED_CUSTOM_FIELDS[name]
            out[slug] = field["id"]
            found.add(slug)
    missing = set(DEFAULT_CUSTOM_FIELDS) - found
    if missing:
        print(
            f"note: /field did not return {sorted(missing)} — using defaults",
            file=sys.stderr,
        )
    return out


def render_markdown(
    *,
    cloud_id: str,
    transitions: list[dict[str, str]],
    custom_fields: dict[str, str],
) -> str:
    lines: list[str] = [
        "# Jira IDs — SPE Reference",
        "",
        "Lookup card for Jira transition IDs, custom-field keys, and field option IDs "
        "when calling Atlassian MCP tools. Not a workflow narrative — for what each "
        "status *means*, see `sc0red-engineering-pipeline.md`.",
        "",
        "**Regenerated by `workspaces/shared/tools/dump-jira-workflow.py`.** Do not hand-edit. "
        "Re-run the script after any Jira workflow change and review the diff.",
        "",
        "If a `transitionJiraIssue` call fails with `400 Transition is not valid` or "
        "lands in an unexpected status, the Jira workflow changed — regenerate this "
        "doc, then update any template that hardcodes a transition ID.",
        "",
        "## Transitions",
        "",
        "Agent transitions go through curl + Bearer on the `api.atlassian.com` gateway "
        "(see `jira-write-auth.md` for the full pattern). Body: "
        "`{\"transition\":{\"id\":\"<id>\"}}`. Never call "
        "`mcp__atlassian__transitionJiraIssue` — it authors as Chris. "
        "When multiple transitions point at the same destination (e.g. a specific gate "
        "like *Plan Approved* plus a generic *Manual*), both are listed — pick the one "
        "matching the workflow gate you intend.",
        "",
        "| Destination | Transition name | id |",
        "|---|---|---:|",
    ]
    for t in transitions:
        lines.append(f"| {t['to']} | {t['name']} | {t['id']} |")

    lines += [
        "",
        "## Custom fields",
        "",
        "Set with curl PUT to `${JIRA_BASE}/issue/<KEY>` and "
        "`Authorization: Bearer ${YOUR_AGENT_JIRA_TOKEN}` (see `jira-write-auth.md`). "
        "Body: `{\"fields\":{\"<key>\":<value>}}`. Never call "
        "`mcp__atlassian__editJiraIssue` — it authors as Chris.",
        "",
        "| Field | key |",
        "|---|---|",
        f"| Business Value  | `{custom_fields['business_value']}` |",
        f"| Intensity       | `{custom_fields['intensity']}` |",
        f"| Risk            | `{custom_fields['risk']}` |",
        f"| Story Points    | `{custom_fields['story_points']}` |",
        f"| Velocity Impact | `{custom_fields['velocity_impact']}` |",
        "",
        "## Field option IDs",
        "",
        "Pass these as `{\"id\": \"...\"}` values when setting the custom fields above.",
        "",
    ]
    for field_label, options in FIELD_OPTIONS.items():
        lines += [
            f"**{field_label}**",
            "",
            "| Option | id |",
            "|---|---|",
        ]
        for opt_name, opt_id in options:
            lines.append(f"| {opt_name} | {opt_id} |")
        lines.append("")

    lines += [
        "## Atlassian MCP arguments",
        "",
        f"Every Atlassian MCP call needs `cloudId: \"{cloud_id}\"`. Project key is "
        f"`{PROJECT_KEY}`. Patch's own Atlassian account ID is `{PATCH_ACCOUNT_ID}`.",
        "",
    ]

    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
