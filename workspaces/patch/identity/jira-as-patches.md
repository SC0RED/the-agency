# Patches — Jira service account

Identity-only. The auth pattern (Bearer + gateway, `mcp__atlassian__*` writes are forbidden, common recipes) lives in `../../shared/jira-write-auth.md` and is injected alongside this file in every Patch template.

## Service account

| | |
| --- | --- |
| displayName | `Patches` |
| emailAddress | `patches-r1dqlj3a1q@serviceaccount.atlassian.com` |
| accountId | `712020:2fbdb38e-012b-43a6-b286-4339c24baabc` |
| accountType | `app` |

The credential is a long-lived API token stored in 1Password Engineering vault as item `Jira Access Token - Patch`, field `credential`. Regenerate in Atlassian admin → Service accounts → Patches → Credentials, then update the 1P item.

## Token fetch (at task start)

From Patch's workspace directory:

```bash
export PATCH_JIRA_TOKEN=$(bash ../../scripts/generate-jira-patches-token.sh)
export JIRA_BASE="https://api.atlassian.com/ex/jira/10449a34-7d09-4681-85d9-038414693fbd/rest/api/3"
```

## Sanity check (expected `/myself` output)

```bash
curl -sS -H "Authorization: Bearer ${PATCH_JIRA_TOKEN}" "${JIRA_BASE}/myself" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['displayName'], d['emailAddress'], d['accountType'])"
# Expected: Patches patches-r1dqlj3a1q@serviceaccount.atlassian.com app
```

If that prints anything other than `Patches / ... / app`, stop and investigate — your writes are about to land under the wrong account.
