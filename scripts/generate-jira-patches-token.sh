#!/usr/bin/env bash
# Fetch the Patches service-account Jira API token for Bearer auth.
#
# Reads the token from the "Jira Access Token - Patch" item in 1Password
# Engineering vault and prints it to stdout. On the EC2,
# OP_SERVICE_ACCOUNT_TOKEN is already injected into the env — no op
# signin required. Elsewhere, run `eval $(op signin)` first.
#
# The token authenticates as Atlassian service account
#   patches-r1dqlj3a1q@serviceaccount.atlassian.com
# (displayName "Patches", accountId 712020:2fbdb38e-012b-43a6-b286-4339c24baabc)
# when used as a Bearer token against the api.atlassian.com gateway:
#
#   export PATCH_JIRA_TOKEN=$(scripts/generate-jira-patches-token.sh)
#   JIRA_BASE="https://api.atlassian.com/ex/jira/10449a34-7d09-4681-85d9-038414693fbd/rest/api/3"
#   curl -H "Authorization: Bearer ${PATCH_JIRA_TOKEN}" "${JIRA_BASE}/myself"
#
# Site-direct URLs (https://sc0red.atlassian.net/rest/api/3/...) do NOT
# work with this token — use the api.atlassian.com gateway form only.
#
# Atlassian API tokens don't auto-expire. Rotate by regenerating in
# Atlassian admin → Service accounts → Patches → Credentials, then
# updating the 1Password item's `credential` field.

set -euo pipefail

OP_ITEM="Jira Access Token - Patch"
OP_VAULT="Engineering"

op item get "${OP_ITEM}" --vault "${OP_VAULT}" --fields credential --reveal
