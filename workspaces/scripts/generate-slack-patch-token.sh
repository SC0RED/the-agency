#!/usr/bin/env bash
# Fetch the Patch Slack bot token from 1Password and print to stdout.
#
# Reads "Bot User Token" (xoxb-...) from the "Slack — Bot Token (Patch)"
# item in vault Engineering. On the EC2, OP_SERVICE_ACCOUNT_TOKEN is
# already injected — no op signin required. Elsewhere, run
# `eval $(op signin)` first.
#
# Authenticates as bot user `patch` (bot_id B0ALY9FMKE2) in workspace
# SC0RED. Used by Patch's slack-alert flow to post diagnoses in the
# alert thread:
#
#   export PATCH_SLACK_TOKEN=$(workspaces/shared/tools/generate-slack-patch-token.sh)
#   curl -H "Authorization: Bearer ${PATCH_SLACK_TOKEN}" \
#        -d '{"channel":"...","thread_ts":"...","text":"..."}' \
#        https://slack.com/api/chat.postMessage
#
# Tokens don't auto-expire. Rotate by re-installing the Patch Slack
# app and updating the 1Password item's "Bot User Token" field.

set -euo pipefail

OP_ITEM="Slack — Bot Token (Patch)"
OP_VAULT="Engineering"
OP_FIELD="Bot User Token"

op item get "${OP_ITEM}" --vault "${OP_VAULT}" --fields label="${OP_FIELD}" --reveal
