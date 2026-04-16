# TOOLS.md - Patch's Infrastructure

## 1Password

**Token lives in macOS Keychain. Never run `op` bare — it hangs. Always pull token first.**

```bash
OP_TOKEN=$(security find-generic-password -s "openclaw.op_token_patch" -a "openclaw" -w 2>/dev/null)
OP_SERVICE_ACCOUNT_TOKEN=$OP_TOKEN op item list --vault Patch
OP_SERVICE_ACCOUNT_TOKEN=$OP_TOKEN op item get <item-id> --vault Patch --reveal
```

Vault: **Patch** (my.1password.com)

## Git SSH

The 1Password SSH agent may have no keys loaded. Use the system agent socket:
```bash
SSH_AGENT_SOCK=$(ls /private/tmp/com.apple.launchd.*/Listeners 2>/dev/null | head -1)
GIT_SSH_COMMAND="ssh -F /dev/null -o IdentityAgent=$SSH_AGENT_SOCK -o IdentitiesOnly=no" git push
```

## Repos

- Platform-Frontend: /Volumes/SSD/Code/Github/sc0red/Platform-Frontend
- Platform-Backend: /Volumes/SSD/Code/Github/sc0red/Platform-Backend
- assessment_engine: /Volumes/SSD/Code/Github/sc0red/assessment_engine
- All fixes target the `development` branch — never touch testing or production

## Jira

- Instance: sc0red.atlassian.net
- Project: SPE (team-managed, next-gen)
- API: POST /rest/api/3/search/jql (v3 only — v2 returns 410)
- **OAuth 2.0 (preferred):** vault item `z74ovcwsybnehh72eorriuj2fy` — fields: "Client ID", "Client secret" (lowercase s)
- Token: POST `https://auth.atlassian.com/oauth/token` with client_credentials grant
- API base: `https://api.atlassian.com/ex/jira/10449a34-7d09-4681-85d9-038414693fbd/rest/api/3`
- Legacy fallback: vault item `quklezthyyf5ougjxzzzihucfy` (posts as Chris)

## Slack

- Workspace: sc0red
- Post to: #general-engineering-qa (C0ALJS0M2NR)
- Alert channels: #alerts-platform-failure-development (C08V6MV0VNV), #alerts-platform-failure-testing (C08UWMQJFBN), #alerts-platform-failure-production (C08UVJDJZTL)

## QA / Browser Testing

### Target Environment
- Login URL: https://testing.sc0red.ai/search/url (bypasses home page redirect)
- Branch: testing
- Auth: Auth0 username/password (NOT Google SSO)
- Credentials: Patch vault → "testing.sc0red.com" (item: m5w733ioomgwpklzpmlvqvht7m)
  - username: patch@sc0red.com
  - password: pull from vault, never hardcode

### Browser Tool
Use OpenClaw's `browser` tool for navigation and testing. Flow:
1. Pull credentials from 1Password
2. Navigate to login URL
3. Click Login → Auth0 form → fill creds → submit
4. Wait for redirect to /dashboard/
5. Test from there

### Test Infrastructure
- automated_testing repo: /Volumes/SSD/Code/Github/sc0red/automated_testing
- Test plans: /Volumes/SSD/Code/Github/sc0red/automated_testing/test-plans/
- Playwright config + auth helpers available if needed

## The Agency — Shared Obsidian Vault

**Path:** `/Users/ctcreel/Library/Mobile Documents/iCloud~md~obsidian/Documents/The Agency`

Syncs via iCloud. Read/write directly — it's just markdown files.

- `Shared/ARDs/Patch-ARD.md` — your ARD
- `Shared/Agents/` — agent profiles
- `Journal/` — daily standups for Chris

**Notion is cancelled (March 2026). Do not reference Notion.**
