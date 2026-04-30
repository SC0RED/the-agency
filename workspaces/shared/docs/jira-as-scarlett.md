# Jira writes as Scarlett — authenticating as the service account

All of Scarlett's Jira **writes** (review verdict comments, transitions if and when she's authorised to do them) must author as the Atlassian service account `Scarlett`, not as Chris and not as Patches. Scarlett's voice on a ticket needs to be visibly distinct from Patch's so a human can see at a glance which agent reviewed what.

## The service account

| | |
| --- | --- |
| displayName | `Scarlett` |
| emailAddress | `scarlett-8mweil0m1j@serviceaccount.atlassian.com` |
| accountId | `712020:9f1fa836-b561-4ae6-b5ab-9c4e6e39adfb` |
| accountType | `app` |

The credential is a long-lived API token stored in 1Password Engineering vault as item `Jira Service Account - Scarlett`, field `credential`. Rotate in Atlassian admin → Service accounts → Scarlett → Credentials, then update the 1P item.

## Getting a token at task start

From Scarlett's workspace directory, the script is at `../shared/tools/generate-jira-scarlett-token.sh`:

```bash
export SCARLETT_JIRA_TOKEN=$(bash ../shared/tools/generate-jira-scarlett-token.sh)
export JIRA_BASE="https://api.atlassian.com/ex/jira/10449a34-7d09-4681-85d9-038414693fbd/rest/api/3"
```

Atlassian API tokens don't auto-expire — one fetch per task is enough.

## Making calls

**All Jira writes use `Authorization: Bearer` on the `api.atlassian.com` gateway URL.** Site-direct URLs (`https://sc0red.atlassian.net/rest/api/3/...`) do NOT work with a service-account token — only the gateway URL does.

### Post a review verdict comment

```bash
curl -sS -X POST "${JIRA_BASE}/issue/SPE-XXXX/comment" \
  -H "Authorization: Bearer ${SCARLETT_JIRA_TOKEN}" \
  -H "Content-Type: application/json" \
  -d @"${SCRATCH}/review-verdict.json"
```

For multi-paragraph or headed comments, build the ADF JSON body in `${SCRATCH}/review-verdict.json` (per-task scratch dir to avoid the cross-task `/tmp` collision that bit Patch on SPE-1719) and reference it with `-d @path`.

### Read the plan or PR you're reviewing

For reads, you can use either the MCP tools (which authenticate as Chris — fine for reads) or curl with your Bearer. Curl is preferred so the same auth path covers reads and writes:

```bash
curl -sS -H "Authorization: Bearer ${SCARLETT_JIRA_TOKEN}" \
  "${JIRA_BASE}/issue/SPE-XXXX?fields=comment,description,issuetype,status&expand=renderedFields"
```

## DO NOT use `mcp__atlassian__*` tools for writes

The MCP Atlassian server configured on this host authenticates with Chris's personal OAuth, so **every `mcp__atlassian__addCommentToJiraIssue`, `mcp__atlassian__transitionJiraIssue`, `mcp__atlassian__editJiraIssue`, etc. call authors as `Christopher Creel`, not `Scarlett`.** That defeats the entire point of having a separate reviewer identity.

Reads (`mcp__atlassian__getJiraIssue`, `searchJiraIssuesUsingJql`, `getTransitionsForJiraIssue`) are fine through MCP, but you can also do them via Bearer + curl as shown above. Pick one path and stick with it for the run.

**Rule of thumb**: if the tool name starts with `add`, `edit`, `transition`, `create`, or the HTTP verb is `POST`/`PUT`/`DELETE`, go through the Bearer + curl path. If it starts with `get`, `search`, `lookup`, MCP is acceptable for reads.

## Verifying you're authenticated as Scarlett

Sanity-check at the top of every task — the assertion is cheap and prevents an entire run from posting under the wrong identity:

```bash
curl -sS -H "Authorization: Bearer ${SCARLETT_JIRA_TOKEN}" "${JIRA_BASE}/myself" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['displayName']=='Scarlett', d; print('auth ok:', d['displayName'])"
```

If the assertion fails, **stop immediately** — investigate before touching the ticket. A misauth review comment landing under Chris's or Patches' name corrupts the audit trail.
