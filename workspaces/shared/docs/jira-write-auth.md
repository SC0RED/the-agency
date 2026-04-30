# Jira write auth — service-account pattern

Every agent's Jira **writes** (comments, transitions, field edits, assignee changes) must author as that agent's dedicated Atlassian service account, not as Chris. Audit-trail clarity: a human reading the ticket should see at a glance which agent posted what.

The per-agent specifics — service-account identity, 1Password reference, token-fetch script, expected `/myself` output — live in your workspace at `docs/jira-as-<name>.md`. This doc covers the auth pattern that's identical across agents.

## Use Bearer + `api.atlassian.com` — never the site-direct URL

```bash
export JIRA_BASE="https://api.atlassian.com/ex/jira/10449a34-7d09-4681-85d9-038414693fbd/rest/api/3"
```

Site-direct URLs (`https://sc0red.atlassian.net/rest/api/3/...`) do **not** accept service-account tokens. Only the gateway URL above works. Standard Bearer header on every call:

```
Authorization: Bearer ${YOUR_AGENT_JIRA_TOKEN}
```

Atlassian API tokens don't auto-expire — one fetch per task is enough.

## Reads vs writes

| Operation | Tool | Why |
|---|---|---|
| Reads (`get*`, `search*`, `lookup*`, any `GET`) | `mcp__atlassian__*` is fine | Authorship doesn't matter on reads. MCP is faster + better-typed. |
| Writes (`add*`, `edit*`, `transition*`, `create*`, any `POST`/`PUT`/`DELETE`) | `curl` with Bearer + gateway | MCP authenticates as Chris's personal OAuth — every write through it would post as `Christopher Creel`, defeating the whole reason this pattern exists. |

## DO NOT use `mcp__atlassian__*` for writes

The MCP Atlassian server on this host authenticates with Chris's personal OAuth, so **every `mcp__atlassian__addCommentToJiraIssue`, `mcp__atlassian__transitionJiraIssue`, `mcp__atlassian__editJiraIssue`, etc. call authors as `Christopher Creel`** regardless of which agent invoked it. That is the exact bug this auth pattern exists to prevent.

**Rule of thumb**: if the tool name starts with `add`, `edit`, `transition`, `create`, or the HTTP verb is `POST`/`PUT`/`DELETE`, go through Bearer + curl. If it starts with `get`, `search`, or `lookup`, MCP is fine.

## Common write recipes

### Post a comment

```bash
curl -sS -X POST "${JIRA_BASE}/issue/SPE-XXXX/comment" \
  -H "Authorization: Bearer ${YOUR_AGENT_JIRA_TOKEN}" \
  -H "Content-Type: application/json" \
  -d @"${SCRATCH}/comment-body.json"
```

For multi-paragraph or headed comments, build the ADF JSON body in your task scratch dir (per-task scratch avoids the cross-task `/tmp` collision that bit Patch on SPE-1719) and reference with `-d @path`.

### Transition an issue

```bash
curl -sS -X POST "${JIRA_BASE}/issue/SPE-XXXX/transitions" \
  -H "Authorization: Bearer ${YOUR_AGENT_JIRA_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"transition":{"id":"<id from jira-ids-reference>"}}'
```

### Edit issue fields (assignee, story points, risk, etc.)

```bash
curl -sS -X PUT "${JIRA_BASE}/issue/SPE-XXXX" \
  -H "Authorization: Bearer ${YOUR_AGENT_JIRA_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"fields":{"customfield_10048":3}}'
```

Field keys and transition IDs live in `jira-ids-reference.md`. That doc is always-authoritative — don't hard-code IDs from memory.

## Sanity check at task start

Cheap, and it prevents an entire run from posting under the wrong identity. Each agent's `docs/jira-as-<name>.md` shows the exact expected `/myself` output for their service account; the call shape is the same:

```bash
curl -sS -H "Authorization: Bearer ${YOUR_AGENT_JIRA_TOKEN}" "${JIRA_BASE}/myself" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['displayName'], d['emailAddress'], d['accountType'])"
```

If it prints anything other than your agent's expected identity, **stop immediately** — investigate before touching the ticket. A misauth comment landing under the wrong account corrupts the audit trail.
