# the-agency

<img src="workspaces/patch/avatars/patch.jpg" alt="Patch" width="140" align="right">
<img src="workspaces/scarlett/avatars/scarlett.jpg" alt="Scarlett" width="140" align="right">

Workspaces for sc0red's engineering agents: **Patch** (AI software engineer) and **Scarlett** (reviewer). They share an EC2 host, share an engineering pipeline, and share most of the prose docs that define how sc0red builds software.

## Who they are and what they do

**Patch** is the AI engineer. Triggered by Jira webhooks when a ticket transitions into a status that's his to act on:

- **Plan** — investigate, propose an Approach + Acceptance Criteria + Definition of Done, post the plan as a Jira comment, transition to Plan Review and dispatch Scarlett.
- **Ready for Development** — implement the approved plan, push a PR, verify CI green, handle CodeRabbit, transition to Code Review and dispatch Scarlett.
- **Deploy to development** — merge the approved PRs into `development`, transition to Deployed to Development.
- **Verified in Development** — pulse-promote `development → testing` across the three repos when the pipeline is quiet.

Patch also wakes up on:

- **GitHub `check_suite.completed` failures** on his own PRs — out-of-band CI red catch-all.
- **Slack alerts** in the three `#alerts-platform-failure-*` channels — diagnose, search for an existing ticket, comment or create one, post a threaded reply.
- **Internal `address-pr-feedback` task** — dispatched by Scarlett after a `changes_requested` review.

**Scarlett** is the reviewer. She does not write fix code and does not merge PRs. Triggered by internal task dispatch from Patch:

- **plan-review** — read Patch's plan against the five-axis rubric (Correctness / Design / Consistency / Edge cases / Test coverage); approve or request changes.
- **code-review** — read the diff against the plan; post line-level GitHub comments + a verdict in Jira; dispatch `address-pr-feedback` back to Patch on `changes_requested`.

Plus scheduled:

- **daily-handoff** — Mon–Fri 7:45 AM ET, posts a digest of yesterday's PRs + open tickets needing eyes to `#general-engineering`.

Full agent identities in `workspaces/<agent>/identity/IDENTITY.md`; reviewing principles + voice in `workspaces/<agent>/identity/SOUL.md`.

## What's in this repo

| Path | Contents |
|---|---|
| `workspaces/patch/` | Patch's agent workspace — `clawndom.yaml`, `identity/`, `templates/`, `avatars/` |
| `workspaces/scarlett/` | Scarlett's agent workspace — same shape |
| `workspaces/shared/` | Cross-agent docs both agents inject: engineering pipeline, anti-patterns, issue-writing guides, Jira IDs reference, jira-write-auth pattern, TOOLS inventory, hook-session protocol, USER metadata, etc. |
| `workspaces/scripts/` | Operator scripts the templates shell out to at runtime: GitHub App token generator, per-agent Jira/Slack token generators, Jira-workflow ID dumper |

Per-agent layout:

```
workspaces/<agent>/
  clawndom.yaml          ← routing rules + per-rule tools + memory namespaces
  identity/              ← agent identity tier
    IDENTITY.md          ← name, role, who they work with
    SOUL.md              ← principles, voice, do/don't
    jira-as-<name>.md    ← service-account identity (Patches / Scarlett)
  templates/             ← Nunjucks templates (one per route)
  avatars/               ← portrait images
```

Both agents follow the canonical workspace layout — see [`clawndom/docs/guides/AGENT_WORKSPACE_LAYOUT.md`](https://github.com/SC0RED/clawndom/blob/main/docs/guides/AGENT_WORKSPACE_LAYOUT.md). The runtime, the routing engine, the doc-injection mechanism, and the tool-use protocol all live in [`SC0RED/clawndom`](https://github.com/SC0RED/clawndom).

## Identity / auth pattern

Every Jira comment, transition, and field edit authors as the agent's dedicated Atlassian service account, not as Chris. Templates fetch a bearer token via the matching script in `workspaces/scripts/` and use it on `curl` calls against `api.atlassian.com`. MCP-routed Jira writes (`mcp__atlassian__addCommentToJiraIssue`, etc.) author as Chris's OAuth and are forbidden — full rules in `workspaces/shared/jira-write-auth.md`.

Same shape for Slack: each agent has its own bot token; replies post as the matching identity.

## Operator scripts

`workspaces/scripts/` holds the shell helpers templates call at runtime:

- `generate-github-app-token.sh` — short-lived GitHub App token for `sc0red-patch` (cloning private repos, opening PRs).
- `generate-jira-{patches,scarlett}-token.sh` — bearer tokens for the per-agent Jira service accounts.
- `generate-slack-{patch,scarlett}-token.sh` — bearer tokens for the per-agent Slack apps.
- `dump-jira-workflow.py` — regenerates `workspaces/shared/jira-ids-reference.md` against the live Jira workflow. Run when the workflow changes.

## Adding a new agent

1. `mkdir -p workspaces/<name>/{identity,templates,avatars}`
2. Author `clawndom.yaml`, `identity/IDENTITY.md`, `identity/SOUL.md`, and the templates for whichever webhook surfaces the agent owns.
3. Push to `main`. The Clawndom sync timer on the EC2 picks it up within 5 minutes.

Don't add a `CLAUDE.md` — the Claude CLI auto-loads it into the system prompt on every hook session, polluting the template-controlled prompt. Clawndom owns the prompt byte-for-byte.

## Auditing the workspaces

```
clawndom-audit workspaces/patch --shared-dir workspaces/shared
clawndom-audit workspaces/scarlett --shared-dir workspaces/shared
```

Checks structural integrity — missing templates, unresolved injections, undeclared tools, legacy patterns. Zero findings is the bar.

## Related repositories

- [`SC0RED/clawndom`](https://github.com/SC0RED/clawndom) — the runtime. Hosts both agents; reads this repo at runtime; defines the canonical workspace layout.
- [`SC0RED/agency-tools`](https://github.com/SC0RED/agency-tools) — the typed Python tool library used by SPE-2078-style agents. Patch and Scarlett don't depend on it today (they shell out to bash + curl + aws + sonar-scanner); migration to agency-tools is on the roadmap to retire the shell-out pattern.
- [`ctcreel/winston-agency`](https://github.com/ctcreel/winston-agency) — Winston (the TALK office-manager agent). Same workspace shape, single-agent variant.
