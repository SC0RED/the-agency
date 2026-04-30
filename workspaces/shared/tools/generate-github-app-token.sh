#!/usr/bin/env bash
# Generate a GitHub App installation token for sc0red-patch.
#
# Reads app_id / installation_id / rsa_key from the "GitHub App: sc0red-patch"
# item in 1Password Engineering, signs a short-lived JWT, and exchanges it for
# a 1-hour installation access token. Prints the token to stdout.
#
# On the EC2, OP_SERVICE_ACCOUNT_TOKEN is already injected into the env — no
# op signin required. Elsewhere, run `eval $(op signin)` first.
#
# Usage
#   export GH_TOKEN=$(workspaces/shared/tools/generate-github-app-token.sh)
#   gh repo clone SC0RED/Platform-Frontend
#   # — or, for raw git:
#   git clone https://x-access-token:${GH_TOKEN}@github.com/SC0RED/Platform-Frontend
#
# Tokens expire after 1 hour. Re-run when you need a fresh one.

set -euo pipefail

OP_ITEM="GitHub App: sc0red-patch"
OP_VAULT="Engineering"

APP_ID=$(op item get "${OP_ITEM}" --vault "${OP_VAULT}" --fields app_id)
INSTALLATION_ID=$(op item get "${OP_ITEM}" --vault "${OP_VAULT}" --fields installation_id)
export RSA_KEY=$(op item get "${OP_ITEM}" --vault "${OP_VAULT}" --fields rsa_key --reveal)

exec python3 - "$APP_ID" "$INSTALLATION_ID" <<'PY'
import json
import os
import sys
import time
import urllib.error
import urllib.request

import jwt

app_id = sys.argv[1]
installation_id = sys.argv[2]
# 1Password sometimes wraps multi-line text fields in double quotes on paste;
# strip them so PEM parsing doesn't fail with "no start line".
private_key = os.environ["RSA_KEY"].strip().strip('"')

now = int(time.time())
assertion = jwt.encode(
    {"iat": now - 60, "exp": now + 540, "iss": app_id},
    private_key,
    algorithm="RS256",
)

request = urllib.request.Request(
    f"https://api.github.com/app/installations/{installation_id}/access_tokens",
    method="POST",
    headers={
        "Authorization": f"Bearer {assertion}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    },
)

try:
    with urllib.request.urlopen(request, timeout=15) as response:
        body = json.loads(response.read())
except urllib.error.HTTPError as exc:
    sys.exit(f"GitHub API error {exc.code}: {exc.read().decode(errors='replace')}")

sys.stdout.write(body["token"])
PY
