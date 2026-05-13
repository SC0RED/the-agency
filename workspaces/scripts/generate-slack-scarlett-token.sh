#!/usr/bin/env bash
# Fetch the Scarlett Slack bot token from 1Password and print to stdout.
#
# Reads "Bot User Token" (xoxb-...) from the "Slack — Bot Token (Scarlett)"
# item in vault Engineering. On the EC2, OP_SERVICE_ACCOUNT_TOKEN is
# already injected — no op signin required. Elsewhere, run
# `eval $(op signin)` first.
#
# Authenticates as bot user `scarlett` (bot_id B0AHYRDBCVB) in workspace
# SC0RED. Used by Scarlett's daily-handoff template to post the daily
# platform digest to #general-engineering:
#
#   export SCARLETT_SLACK_TOKEN=$(workspaces/shared/tools/generate-slack-scarlett-token.sh)
#   curl -H "Authorization: Bearer ${SCARLETT_SLACK_TOKEN}" \
#        -d '{"channel":"...","blocks":[...]}' \
#        https://slack.com/api/chat.postMessage
#
# Tokens don't auto-expire. Rotate by re-installing the Scarlett Slack
# app and updating the 1Password item's "Bot User Token" field.

set -euo pipefail

OP_ITEM="Slack — Bot Token (Scarlett)"
OP_VAULT="Engineering"
OP_FIELD="Bot User Token"

op item get "${OP_ITEM}" --vault "${OP_VAULT}" --fields label="${OP_FIELD}" --reveal
