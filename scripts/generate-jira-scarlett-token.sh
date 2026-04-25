#!/usr/bin/env bash
# Fetch the Scarlett service-account Jira API token for Bearer auth.
#
# Reads the token from the "Jira Service Account - Scarlett" item in
# 1Password Engineering vault and prints it to stdout. On the EC2,
# OP_SERVICE_ACCOUNT_TOKEN is already injected into the env — no op
# signin required. Elsewhere, run `eval $(op signin)` first.
#
# The token authenticates as Atlassian service account
#   scarlett-8mweil0m1j@serviceaccount.atlassian.com
# (displayName "Scarlett", accountId 712020:9f1fa836-b561-4ae6-b5ab-9c4e6e39adfb)
# when used as a Bearer token against the api.atlassian.com gateway:
#
#   export SCARLETT_JIRA_TOKEN=$(scripts/generate-jira-scarlett-token.sh)
#   JIRA_BASE="https://api.atlassian.com/ex/jira/10449a34-7d09-4681-85d9-038414693fbd/rest/api/3"
#   curl -H "Authorization: Bearer ${SCARLETT_JIRA_TOKEN}" "${JIRA_BASE}/myself"
#
# Site-direct URLs (https://sc0red.atlassian.net/rest/api/3/...) do NOT
# work with this token — use the api.atlassian.com gateway form only.
#
# Atlassian API tokens don't auto-expire. Rotate by regenerating in
# Atlassian admin → Service accounts → Scarlett → Credentials, then
# updating the 1Password item's `credential` field.

set -euo pipefail

OP_ITEM="Jira Service Account - Scarlett"
OP_VAULT="Engineering"

op item get "${OP_ITEM}" --vault "${OP_VAULT}" --fields credential --reveal
