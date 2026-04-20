# Jira IDs — SPE project

Authoritative list of the Jira transition IDs and custom-field IDs you use when editing issues via the Atlassian MCP. Verified from live Jira on 2026-04-20.

If a `transitionJiraIssue` call fails with `400 Transition is not valid` or lands the ticket in an unexpected status, the Jira workflow changed — tell a human, don't guess.

## Transitions (pass these as `transition.id` to `mcp__claude_ai_Atlassian__transitionJiraIssue`)

| Destination             | transition.id |
|-------------------------|--------------:|
| Triage                  | 2             |
| Blocked                 | 4             |
| Verified in Testing     | 5             |
| Abandon                 | 9             |
| New                     | 11            |
| Verified in Development | 12            |
| Hotfix                  | 13            |
| Ready for Development   | 15            |
| Plan                    | 16            |
| Backlog                 | 30            |
| Deployed to Production  | 31            |
| Deployed to Development | 32            |
| Deployed to Testing     | 33            |
| Plan Review             | 35            |
| Code Review             | 36            |
| In Development          | 37            |

## Custom fields (pass these as field keys to `mcp__claude_ai_Atlassian__editJiraIssue`)

| Field           | key                   |
|-----------------|-----------------------|
| Business Value  | `customfield_10065`   |
| Intensity       | `customfield_10039`   |
| Risk            | `customfield_10038`   |
| Story Points    | `customfield_10016`   |
| Velocity Impact | `customfield_10064`   |

## Field option IDs (pass these as `{"id": "..."}` values when setting the custom fields above)

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

## Project context

- **Cloud ID:** `10449a34-7d09-4681-85d9-038414693fbd` (pass as `cloudId` to every Atlassian MCP tool)
- **Project key:** `SPE`
- **Patch's Atlassian account ID:** `712020:2fbdb38e-012b-43a6-b286-4339c24baabc`
