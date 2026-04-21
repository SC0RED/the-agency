# TOOLS.md — Patch's Infrastructure (Linux / EC2)

You run on a dedicated t3.small EC2 in `sc0red-dev` (us-east-1), reachable as `clawndom.tail708f46.ts.net` over Tailscale Funnel. **You are not on macOS.** No Keychain. No `security` command. No iCloud. The launchd plist setup is gone.

## 1Password

`OP_SERVICE_ACCOUNT_TOKEN` is already in your environment (Clawndom injects it from `/etc/clawndom/clawndom.env`). Use `op` directly — no token-fetching dance needed.

```bash
op vault list                                # only "Engineering" is in scope
op item list --vault Engineering
op item get Jira --vault Engineering --reveal
op read "op://Engineering/Jira/hmac"
```

**Vault scope:** the `Engineering` vault is the only one your service account can see. The old `Patch` vault on the Mac doesn't exist here. Items currently in `Engineering`:
- `Jira` (Secure Note) — fields include `hmac` (Clawndom's webhook signing secret)
- `Sonar Token` (Secure Note) — for SonarCloud scans
- `Service Account Auth Token: The Agency` (API Credential) — your own service-account token (don't read it; it's already in env)

If you need a secret that isn't in the `Engineering` vault, you can't get it. Ping Chris in `#general-engineering` to share the relevant item to the service account.

## AWS CLI

`aws` v2 is installed. Profiles:

| Profile | Account | Default? |
| --- | --- | --- |
| `sc0red-dev` | sc0red dev | yes (`AWS_DEFAULT_PROFILE` is set) |
| `sc0red-test` | sc0red testing | |
| `sc0red-prod` | sc0red production | |

`AWS_DEFAULT_REGION=us-east-2` (engine Lambda + most of sc0red infra runs in us-east-2, not us-east-1).

```bash
aws sts get-caller-identity                                  # confirms default profile
aws logs tail /aws/lambda/<fn> --since 1h --follow           # CloudWatch streaming
aws logs filter-log-events --log-group-name /aws/lambda/<fn> --filter-pattern ERROR --start-time $(date -d '1 hour ago' +%s%3N)
aws s3 ls s3://<bucket> --profile sc0red-test                # cross-profile
```

For prod investigation, override per-command: `aws --profile sc0red-prod logs tail ...`. Don't change the env default.

## Git + GitHub

- `git` is configured. SSH key at `~/.ssh/id_ed25519` is registered as a deploy key on `SC0RED/the-agency` (read-only).
- `gh` CLI is installed and authenticated as the deploy identity.
- For pushing code changes, use `gh pr create` after pushing the branch with `git push -u origin fix/...`.

## Repos

The three sc0red repos are NOT cloned on this host. You work with code by spawning Claude Code sessions in cloud environments, or by cloning a repo into `/tmp` for the duration of a task. The Patch *workspace* (this repo, `the-agency/workspaces/patch/`) is at `/home/clawndom/.clawndom/agents/SC0RED__the-agency/workspaces/patch/`, refreshed every 5 minutes by `clawndom-sync-agents.timer`.

If you need to clone a sc0red repo for analysis:
```bash
cd /tmp && git clone git@github.com:SC0RED/<repo>.git && cd <repo>
```
Clean it up when you're done — `/tmp` is private to your systemd unit (`PrivateTmp=true`) and gets wiped on restart.

## Jira

- Instance: `sc0red.atlassian.net`, project `SPE`
- **Use the Atlassian MCP tools** (`mcp__claude_ai_Atlassian__*`) for all Jira interactions. They handle auth and the v3 API for you. Do not write raw `curl` against the Jira REST API.
- **These are *deferred* tools.** They aren't in your default toolset — the CLI exposes them by name only, and calling one directly fails with `InputValidationError`. Load their schemas up front with `ToolSearch` before you touch any Jira task:
  ```
  ToolSearch({query: "select:mcp__claude_ai_Atlassian__getJiraIssue,mcp__claude_ai_Atlassian__searchJiraIssuesUsingJql,mcp__claude_ai_Atlassian__addCommentToJiraIssue,mcp__claude_ai_Atlassian__getTransitionsForJiraIssue,mcp__claude_ai_Atlassian__transitionJiraIssue,mcp__claude_ai_Atlassian__editJiraIssue"})
  ```
  Use `select:<name>[,<name>...]` — don't rely on keyword search like `"jira"`, which can miss the `Atlassian`-prefixed names. Once a tool's schema comes back in the `<functions>` block, it's callable for the rest of the run.
- Common tools you'll use:
  - `mcp__claude_ai_Atlassian__getJiraIssue` — fetch issue
  - `mcp__claude_ai_Atlassian__searchJiraIssuesUsingJql` — search by JQL
  - `mcp__claude_ai_Atlassian__addCommentToJiraIssue` — post a comment
  - `mcp__claude_ai_Atlassian__getTransitionsForJiraIssue` — list transition IDs
  - `mcp__claude_ai_Atlassian__transitionJiraIssue` — apply transition
  - `mcp__claude_ai_Atlassian__editJiraIssue` — update fields (Risk, Intensity, Story Points, Velocity Impact)
- Cloud ID: `10449a34-7d09-4681-85d9-038414693fbd` (the MCP tools take this as a parameter)

## Slack

- Workspace: sc0red
- Channels:
  - `#general-engineering` (C06TRR7A894) — PR review requests, blocked tickets, deploy confirmations
  - `#general-engineering-qa` (C0ALJS0M2NR) — plan summaries, QA findings
  - `#alerts-platform-failure-development` (C08UWMQJFBN), `-testing` (C08UVJDJZTL), `-production` (C08V6MV0VNV)
- The `Patch` Slack app is on Socket Mode, not webhooks — it doesn't need a public URL. Posting messages goes through the Slack Web API (Bot Token).
- Slack Bot Token: pull from 1Password if you need it (`op read "op://Engineering/Slack Bot Token/token"` — verify the exact item path before using).

## QA / Browser Testing

Browser-based testing via the historical OpenClaw `browser` tool is **not available on EC2**. The Mac had the OpenClaw gateway running locally; this host doesn't. If a fix needs browser verification, file a follow-up note in the PR — Chris or another agent runs the manual test for now.

If headless browser testing becomes a recurring need, that's a follow-up ticket: install Playwright on EC2 + plumb credentials through 1Password.

## SonarCloud

For Frontend and Engine PRs, run a local Sonar scan before push. Token is at `op://Engineering/Sonar Token/token` (verify path with `op item list`).

## The Agency repo (this workspace)

`/home/clawndom/.clawndom/agents/SC0RED__the-agency/workspaces/patch/` — auto-pulled from `SC0RED/the-agency` every 5 minutes. Edits to *this* repo (your identity, your templates, your docs) propagate to the live host without a Clawndom restart.

To edit your own workspace: clone the repo locally, change a file, push to `main`. The sync timer picks it up. You don't have direct write access to the cloned copy on the host — and you shouldn't, because the sync overwrites it.

**Obsidian is gone.** The vault was an experiment that ended when OpenClaw shut down. The three docs that lived in `Shared/` (`Patch-ARD`, `sc0red-engineering-pipeline`, `writing-great-jira-issues`) now live in `workspaces/patch/docs/` in this repo, and templates pull them in via the Nunjucks doc-injection syntax (double-brace + `doc:` + relative path). The syntax itself is omitted here because TOOLS.md is itself injected into every template — a literal example would re-parse as a template tag and blow up the render.

## Logging + observability

- Your stdout/stderr land in `/var/log/clawndom/clawndom.log` (rotated by systemd's append). The current invocation's session key is logged at start.
- The Clawndom dashboard at `https://clawndom.tail708f46.ts.net/api/events` streams typed events (webhook.* / job.* / runner.*) — Chris uses this to watch you work.
- For CloudWatch on the sc0red side: `aws logs tail` as documented above.

## Mac-isms that no longer apply

If you find yourself reaching for any of these, stop — they don't exist on Linux:

| Mac-ism | Linux equivalent |
| --- | --- |
| `security find-generic-password ...` | `op read "op://Engineering/<item>/<field>"` (token is already in env) |
| `~/Library/Mobile Documents/iCloud~md~obsidian/...` | files in `workspaces/patch/docs/` in this repo |
| `launchctl ...` | `systemctl --user ...` (but you almost never need this) |
| `/Users/ctcreel/...` | `/home/clawndom/...` for your home; sc0red repos are not pre-cloned |
| `pbcopy` / `pbpaste` | not available |
| OpenClaw `browser` tool | not available — file follow-up notes for manual testing |
| OpenClaw `sessions_spawn` (Scarlett) | tracked in SPE-1707 — until then, request human review via Jira comment |
