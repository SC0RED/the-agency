# Jira IDs — SPE Reference

Lookup card for Jira transition IDs, custom-field keys, and field option IDs when calling Atlassian MCP tools. Not a workflow narrative — for what each status *means*, see `sc0red-engineering-pipeline.md`.

Verified from live Jira on 2026-04-23. If a transition call fails with `400 Transition is not valid` or lands in an unexpected status, the Jira workflow changed — tell a human, don't guess.

## Transitions

Agent transitions go through curl + Bearer on the `api.atlassian.com` gateway (see `jira-write-auth.md` for the full pattern). Body: `{"transition":{"id":"<id>"}}`. Never call `mcp__atlassian__transitionJiraIssue` — it authors as Chris. When multiple transitions point at the same destination (e.g. a specific gate like *Plan Approved* plus a generic *Manual*), both are listed — pick the one matching the workflow gate you intend.

Named transitions (workflow-correct arrows — prefer these over the generic global ones):

| id | Name           | From → To                         |
|---:|----------------|-----------------------------------|
| 14 | Start Planning | Plan → In Planning                |
|  3 | Plan Complete  | In Planning → Plan Review         |
| 15 | Plan Approved  | Plan Review → Ready for Development |
|  6 | Replan         | Plan Review → Plan                |
| 10 | Deploy         | Deploy to development → Deployed to Development |

Global / `Manual` transitions (available from most statuses — use only when a named arrow above doesn't apply):

| Destination             | id |
|-------------------------|---:|
| Triage                  | 2  |
| Blocked                 | 4  |
| Verified in Testing     | 5  |
| Abandon                 | 9  |
| New                     | 11 |
| Verified in Development | 12 |
| Hotfix                  | 13 |
| Plan                    | 16 |
| Backlog                 | 30 |
| Deployed to Production  | 31 |
| Deployed to Development | 32 |
| Deployed to Testing     | 33 |
| Plan Review             | 35 |
| Code Review             | 36 |
| In Development          | 37 |

## Custom fields 

Set with curl PUT to `${JIRA_BASE}/issue/<KEY>` and `Authorization: Bearer ${YOUR_AGENT_JIRA_TOKEN}` (see `jira-write-auth.md`). Body: `{"fields":{"<key>":<value>}}`. Never call `mcp__atlassian__editJiraIssue` — it authors as Chris.

| Field           | key                   |
|-----------------|-----------------------|
| Business Value  | `customfield_10065`   |
| Intensity       | `customfield_10039`   |
| Risk            | `customfield_10038`   |
| Story Points    | `customfield_10016`   |
| Velocity Impact | `customfield_10064`   |

## Field option IDs

Pass these as `{"id": "..."}` values when setting the custom fields above.

**Risk** (`customfield_10038`):

| Option   | id    |
|----------|-------|
| No Risk  | 10024 |
| Low      | 10025 |
| Medium   | 10026 |
| High     | 10027 |

**Intensity** (`customfield_10039`):

| Option       | id    |
|--------------|-------|
| No Intensity | 10028 |
| Low          | 10029 |
| Medium       | 10030 |
| High         | 10031 |

**Velocity Impact** (`customfield_10064`):

| Option          | id    |
|-----------------|-------|
| Neutral         | 10041 |
| Weak Positive   | 10042 |
| Strong Positive | 10043 |
| Negative        | 10044 |

## Atlassian identifiers

- **Cloud ID** (for the `api.atlassian.com/ex/jira/<cloudId>/rest/api/3/...` gateway used by the Patches Bearer path, and for `cloudId` on the MCP-read tools): `10449a34-7d09-4681-85d9-038414693fbd`
- **Project key**: `SPE`
- **Patches account ID** (current assignee marker for Patch-owned tickets): `712020:2fbdb38e-012b-43a6-b286-4339c24baabc`
