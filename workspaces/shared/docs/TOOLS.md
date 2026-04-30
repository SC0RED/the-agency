# TOOLS.md — Agent Infrastructure (Linux / EC2)

You run on a dedicated c7i.large EC2 in `sc0red-dev` (us-east-1), reachable as `clawndom.tail708f46.ts.net` over Tailscale Funnel. You are on Linux (Ubuntu 24.04 LTS). This is the tool inventory shared by every agent in the-agency.

## 1Password

`OP_SERVICE_ACCOUNT_TOKEN` is already in your environment (Clawndom injects it from `/etc/clawndom/clawndom.env`). Use `op` directly — no token-fetching dance needed.

```bash
op vault list                                # only "Engineering" is in scope
op item list --vault Engineering
op item get Jira --vault Engineering --reveal
op read "op://Engineering/Jira/hmac"
```

**Vault scope:** the `Engineering` vault is the only one your service account can see. Items currently in it:

- `Jira` (Secure Note) — `hmac` field is Clawndom's webhook signing secret
- `Service Account Auth Token: Jira` (API Credential) — Atlassian API token for the `dump-jira-workflow.py` script
- `Service Account Auth Token: The Agency` (API Credential) — your own service-account token (don't read it; it's already in env)
- `Sonar Token` (Secure Note) — SonarCloud scans
- `GitHub App: sc0red-patch` — see `shared/github-access.md`; the auth-flow doc owns this

If you need a secret that isn't in `Engineering`, you can't get it. Ping Chris in `#general-engineering` to share the relevant item to the service account.

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

`git` and `gh` are installed. The SSH deploy key at `~/.ssh/id_ed25519` is read-only, scoped to `SC0RED/the-agency` only. For cloning or pushing to the three `SC0RED` private repos (`Platform-Frontend`, `Platform-Backend`, `assessment_engine`), see **`shared/github-access.md`** — that's the authoritative auth flow (GitHub App token via `workspaces/shared/tools/generate-github-app-token.sh`).

## Language runtimes

- **Node.js** — system Node 22 on PATH. `nvm` is installed at `~/.nvm` with Node 18 (default) for Angular 15 projects. Switch with `nvm use 18` or `nvm use 22` as needed.
- **Python** — 3.12 (`python3`). `pip3`, `venv`, and `build-essential` are installed.
- **uv** (`/usr/local/bin/uv`) — modern Python package manager and runtime.

### Python dev toolchain (via `uv tool install`, on PATH)

- `ruff` — lint + format
- `pyright` — type checker
- `vulture` — dead-code detection
- `mypy` — alternative type checker
- `pytest` — testing
- `black`, `isort` — mostly superseded by `ruff` but available

## Browser testing

Google Chrome stable is installed (`google-chrome --version` works). Karma headless tests run with it.

## Databases

`mongosh` is installed for MongoDB investigation.

## SonarCloud

For Frontend and Engine PRs, run a local Sonar scan before push. `sonar-scanner` is installed at `/usr/local/bin/sonar-scanner`. Token at `op://Engineering/Sonar Token/token`.

## Jira

Use the Atlassian MCP tools for all Jira interactions. They handle auth and the v3 API for you. Never write raw `curl` against the Jira REST API.

**These are *deferred* tools.** They aren't in your default toolset — the CLI exposes them by name only, and calling one directly fails with `InputValidationError`. Load their schemas up front with `ToolSearch` before touching any Jira task:

```
ToolSearch({query: "select:mcp__claude_ai_Atlassian__getJiraIssue,mcp__claude_ai_Atlassian__searchJiraIssuesUsingJql,mcp__claude_ai_Atlassian__addCommentToJiraIssue,mcp__claude_ai_Atlassian__getTransitionsForJiraIssue,mcp__claude_ai_Atlassian__transitionJiraIssue,mcp__claude_ai_Atlassian__editJiraIssue"})
```

Use `select:<name>[,<name>...]` — don't rely on keyword search like `"jira"`, which can miss the `Atlassian`-prefixed names. Once a tool's schema comes back in the `<functions>` block, it's callable for the rest of the run.

Common tools:

- `mcp__claude_ai_Atlassian__getJiraIssue` — fetch issue
- `mcp__claude_ai_Atlassian__searchJiraIssuesUsingJql` — search by JQL
- `mcp__claude_ai_Atlassian__addCommentToJiraIssue` — post a comment
- `mcp__claude_ai_Atlassian__getTransitionsForJiraIssue` — list transition IDs
- `mcp__claude_ai_Atlassian__transitionJiraIssue` — apply transition
- `mcp__claude_ai_Atlassian__editJiraIssue` — update fields

For the actual IDs (cloud ID, transitions, custom fields, option IDs), see `shared/jira-ids-reference.md`.

## Slack

- Workspace: sc0red
- Channels:
  - `#general-engineering` (C06TRR7A894) — PR review requests, blocked tickets, deploy confirmations
  - `#general-engineering-qa` (C0ALJS0M2NR) — plan summaries, QA findings
  - `#alerts-platform-failure-development` (C08UWMQJFBN), `-testing` (C08UVJDJZTL), `-production` (C08V6MV0VNV)
- The `Patch` Slack app is on Socket Mode. Posting messages goes through the Slack Web API (Bot Token).
- Bot Token: `op read "op://Engineering/Slack Bot Token/token"` (verify the exact item path first with `op item list --vault Engineering`).

## Scratch space

`/tmp` is your scratch dir. `PrivateTmp=true` on the systemd unit — wiped on restart, isolated from other services. Clone target repos under `/tmp`, don't leave them anywhere else.

## The Agency repo (your workspace)

Your workspace lives at `/home/clawndom/.clawndom/agents/SC0RED__the-agency/workspaces/<agent>/` (substitute your own agent directory name). The repo is auto-pulled every 5 minutes by the `clawndom-sync-agents.timer` systemd timer. Edits to your identity / templates / docs propagate without a Clawndom restart.

Shared material (engineering pipeline, anti-patterns, writing-great-*, this TOOLS file, etc.) lives at `workspaces/shared/` — one level up from your own docs. Templates inject shared content with the `shared:` doc-injection prefix; they inject agent-specific content with the `doc:` prefix. Both are Nunjucks tags of the form `open-mustache PREFIX:path close-mustache`, preprocessed before Nunjucks rendering. Don't write literal mustache tags inside any injected doc — they'll try to render recursively and fail.

To edit any workspace: clone the repo locally, change a file, push to `main`. The sync timer picks it up. You don't have direct write access to the cloned copy on the host — and you shouldn't; sync overwrites.

## Logging + observability

- Your stdout/stderr land in `/var/log/clawndom/clawndom.log`. The current invocation's session key is logged at start.
- The Clawndom dashboard at `https://clawndom.tail708f46.ts.net/api/events` streams typed events (webhook.* / job.* / runner.*) — Chris uses this to watch you work.
- For CloudWatch on the sc0red side: `aws logs tail` as documented above.
