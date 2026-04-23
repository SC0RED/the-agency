# Jira writes as Patches — authenticating as the service account

All of Patch's Jira **writes** (comments, status transitions, field edits, assignee changes) must author as the Atlassian service account `Patches`, not as Chris. This keeps the audit trail clean and makes automated activity visibly distinct from human work.

## The service account

| | |
| --- | --- |
| displayName | `Patches` |
| emailAddress | `patches-r1dqlj3a1q@serviceaccount.atlassian.com` |
| accountId | `712020:2fbdb38e-012b-43a6-b286-4339c24baabc` |
| accountType | `app` |

The credential is a long-lived API token stored in 1Password Engineering vault as item `Jira Access Token - Patch`, field `credential`. Regenerate in Atlassian admin → Service accounts → Patches → Credentials, then update the 1P item.

## Getting a token at task start

From Patch's workspace directory, the script is at `../../scripts/generate-jira-patches-token.sh`:

```bash
export PATCH_JIRA_TOKEN=$(bash ../../scripts/generate-jira-patches-token.sh)
export JIRA_BASE="https://api.atlassian.com/ex/jira/10449a34-7d09-4681-85d9-038414693fbd/rest/api/3"
```

Atlassian API tokens don't auto-expire — one fetch per task is enough.

## Making calls

**All Jira writes use `Authorization: Bearer` on the `api.atlassian.com` gateway URL.** Site-direct URLs (`https://sc0red.atlassian.net/rest/api/3/...`) do NOT work with a service-account token — only the gateway URL does.

### Post a comment

```bash
curl -sS -X POST "${JIRA_BASE}/issue/SPE-XXXX/comment" \
  -H "Authorization: Bearer ${PATCH_JIRA_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"body":{"type":"doc","version":1,"content":[{"type":"paragraph","content":[{"type":"text","text":"..."}]}]}}'
```

For multi-paragraph or headed comments, build the ADF JSON body in a file and reference with `-d @body.json`.

### Transition an issue

```bash
curl -sS -X POST "${JIRA_BASE}/issue/SPE-XXXX/transitions" \
  -H "Authorization: Bearer ${PATCH_JIRA_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"transition":{"id":"<id from jira-ids-reference>"}}'
```

### Edit issue fields (assignee, story points, risk, etc.)

```bash
curl -sS -X PUT "${JIRA_BASE}/issue/SPE-XXXX" \
  -H "Authorization: Bearer ${PATCH_JIRA_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"fields":{"customfield_10048":3}}'
```

Field keys and transition IDs live in `jira-ids-reference.md`. That doc is always-authoritative — don't hard-code IDs from memory.

## DO NOT use `mcp__atlassian__*` tools for writes

The MCP Atlassian server configured on this host authenticates with Chris's personal OAuth, so **every `mcp__atlassian__addCommentToJiraIssue`, `mcp__atlassian__transitionJiraIssue`, `mcp__atlassian__editJiraIssue`, etc. call authors as `Christopher Creel`, not `Patches`.** That is the exact bug this doc exists to prevent.

Reads (`mcp__atlassian__getJiraIssue`, `searchJiraIssuesUsingJql`, `getTransitionsForJiraIssue`) are fine through MCP — authorship is not a concern for reads.

**Rule of thumb**: if the tool name starts with `add`, `edit`, `transition`, `create`, or the HTTP verb is `POST`/`PUT`/`DELETE`, go through the Bearer + curl path. If it starts with `get`, `search`, `lookup`, MCP is fine.

## Verifying you're authenticated as Patches

Sanity-check at the top of a task when you're unsure:

```bash
curl -sS -H "Authorization: Bearer ${PATCH_JIRA_TOKEN}" "${JIRA_BASE}/myself" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['displayName'], d['emailAddress'], d['accountType'])"
# Expected: Patches patches-r1dqlj3a1q@serviceaccount.atlassian.com app
```

If that prints anything other than `Patches / ... / app`, stop and investigate — your writes are about to land under the wrong account.
