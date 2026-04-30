# Scarlett — Jira service account

Identity-only. The auth pattern (Bearer + gateway, `mcp__atlassian__*` writes are forbidden, common recipes) lives in `../../shared/docs/jira-write-auth.md` and is injected alongside this file in every Scarlett template.

## Service account

| | |
| --- | --- |
| displayName | `Scarlett` |
| emailAddress | `scarlett-8mweil0m1j@serviceaccount.atlassian.com` |
| accountId | `712020:9f1fa836-b561-4ae6-b5ab-9c4e6e39adfb` |
| accountType | `app` |

The credential is a long-lived API token stored in 1Password Engineering vault as item `Jira Service Account - Scarlett`, field `credential`. Rotate in Atlassian admin → Service accounts → Scarlett → Credentials, then update the 1P item.

## Token fetch (at task start)

From Scarlett's workspace directory:

```bash
export SCARLETT_JIRA_TOKEN=$(bash ../shared/tools/generate-jira-scarlett-token.sh)
export JIRA_BASE="https://api.atlassian.com/ex/jira/10449a34-7d09-4681-85d9-038414693fbd/rest/api/3"
```

## Sanity check (expected `/myself` output)

```bash
curl -sS -H "Authorization: Bearer ${SCARLETT_JIRA_TOKEN}" "${JIRA_BASE}/myself" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['displayName']=='Scarlett', d; print('auth ok:', d['displayName'])"
```

If the assertion fails, **stop immediately** — investigate before touching the ticket. A misauth review comment under Chris's or Patches' name corrupts the audit trail.
