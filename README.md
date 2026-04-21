# the-agency

<img src="workspaces/patch/avatars/patch.jpg" alt="Patch" width="160" align="right">

Monorepo of agent workspaces consumed by [Clawndom](https://github.com/SC0RED/clawndom) at runtime. Each agent lives in its own directory under `workspaces/` — identity, principles, templates, reference docs, routing config. Clawndom pulls this repo on a 5-minute sync timer on the EC2 host and renders webhook-triggered prompts from the per-agent templates.

Currently only **Patch** (the AI software engineer, pictured) has a populated workspace. Additional agents can be added by creating a new `workspaces/<name>/` directory with the same layout — see *Adding a new agent* below.

---

## How Clawndom uses this repo

```
Jira webhook ──► Clawndom ──► match routing rule ──► render template ──► spawn `claude -p`
                                  │                       │
                                  │                       └─► {{doc:docs/*.md}} injected inline
                                  │
                                  └─► uses clawndom.yaml at workspaces/<agent>/clawndom.yaml
```

1. A webhook arrives at Clawndom (Jira, Slack, GitHub).
2. Clawndom loads `workspaces/<agent>/clawndom.yaml` from this repo to find the routing rule matching the event.
3. The rule names a template in `workspaces/<agent>/templates/`. Clawndom renders it with the webhook payload plus any `{{doc:...}}` injections it pulls from `workspaces/<agent>/docs/`.
4. Rendered prompt goes to a `claude -p` subprocess with the full context assembled at render time.

The agent sees **only** what the template includes. Nothing at the agent's workspace root is read unless the template injects it. This repo's structure is a tool for humans and Clawndom — the agent never navigates it directly.

**Sync timer.** A systemd timer on the EC2 host (`clawndom-sync-agents.timer`, 5-minute interval) runs `git pull` on `/home/clawndom/.clawndom/agents/SC0RED__the-agency/`. Edits pushed to `main` reach the agent within 5 minutes without a Clawndom restart.

---

## Repository layout

```
the-agency/
  README.md                            (you are here)
  .gitignore
  scripts/
    dump-jira-workflow.py              (regenerates workspaces/patch/docs/jira-ids-reference.md)
    generate-github-app-token.sh       (emits a 1-hour GitHub App token; called by agent templates)
  workspaces/
    patch/
      CLAUDE.md                        (Claude CLI entry point — read at subprocess start)
      clawndom.yaml                    (Clawndom routing rules for this agent)
      avatars/                         (identity imagery)
      specs/                           (workspace-specific specs / ADRs)
      templates/                       (Nunjucks templates — one per routing destination)
      docs/                            (identity, principles, protocols, references)
```

Only the Patch workspace is populated today. When a second agent is added, it gets its own `workspaces/<name>/` directory with the same structural layout.

---

## Agent workspace anatomy (`workspaces/patch/`)

### `CLAUDE.md`

Bootstrap file read by the Claude CLI at subprocess start. Two sections:

1. **Hook-session block (top, mandatory).** Rules for webhook-triggered runs: don't navigate outside the template, follow the failure protocol, start executing Step 1 immediately.
2. **Interactive-session block (below).** Reading list for the rare human-initiated session (`claude` launched directly in the workspace for ad-hoc debugging).

Hook sessions dominate real usage — the interactive block is mostly reference.

### `clawndom.yaml`

The routing config Clawndom reads to decide which template handles which event. Match rules are written against the webhook payload (Jira's `issue.fields.status.name` and `issue.fields.issuetype.name` are the common ones). Each matched rule names a template in `templates/` and optionally a model override.

### `templates/`

Nunjucks templates rendered once per webhook. Per-status × per-type: `jira-plan-{bug,story,task}.md` for Plan transitions, `jira-ready-for-dev-{bug,story,task}.md` for Ready for Development. Each template is self-contained — it carries the steps, the transition IDs, and `{{doc:...}}` injections for everything else.

**Important:** because templates are Nunjucks, any literal `{{` sequence inside an injected doc will be parsed as a template tag. Don't put literal template syntax in injected docs — see `docs/TOOLS.md` for the workaround phrasing.

### `docs/`

All context, policy, and reference material. Injected into templates via `{{doc:docs/<file>.md}}`.

| File | Purpose |
|---|---|
| `IDENTITY.md` | The agent's name, species, visual tag |
| `SOUL.md` | Engineering principles, What I Do / Don't Do, voice, Chris's expectations |
| `USER.md` | Human-metadata about the operator (name, timezone, role) |
| `TOOLS.md` | Host tool inventory — AWS CLI, 1Password, runtime versions, MCP tools, scratch space |
| `sc0red-engineering-pipeline.md` | The full ticket lifecycle narrative (statuses, gates, promotion flow) |
| `jira-ids-reference.md` | Lookup card for transition IDs, custom-field keys, field-option IDs — **regenerated by script** |
| `estimation.md` | Risk × Intensity story-point framework, human+agent shared ruler |
| `anti-patterns.md` | AI anti-patterns to avoid in plans and code |
| `writing-great-issues-base.md` | Universal rules for issue quality (6 questions, architectural review, checklists) |
| `writing-great-bug-issues.md` | Bug-type specialization + good/bad examples |
| `writing-great-feature-issues.md` | Story-type specialization |
| `writing-great-task-issues.md` | Task-type specialization |
| `github-access.md` | GitHub App auth flow for cloning private repos and opening PRs |
| `ux-quality-gate.md` | Frontend UX checklist |

Every numeric Jira ID lives in **one place**: `jira-ids-reference.md`. Templates copy specific literal values from it; no other doc carries transition IDs.

---

## Making changes

1. Clone this repo locally.
2. Edit the relevant file in `workspaces/<agent>/`.
3. Commit and push to `main`.
4. Sync timer pulls within 5 minutes; next webhook run uses the new content.

No PR flow on this repo (currently). Direct-push to main is the pattern. If Clawndom's routing config changes, the next event picks up the new rule without a restart.

---

## Scripts

### `scripts/dump-jira-workflow.py`

Queries live Jira via the Atlassian REST API and rewrites `workspaces/patch/docs/jira-ids-reference.md` in place.

**Run when the Jira workflow changes** (new status, renamed transition, new custom field, or when a `transitionJiraIssue` call lands a ticket in an unexpected status).

Needs an Atlassian API token + the account email + the SPE cloud ID. On the EC2 these come from 1Password:

```bash
JIRA_USER_EMAIL=$(op item get "Service Account Auth Token: Jira" \
  --vault Engineering --fields username)
JIRA_API_TOKEN=$(op item get "Service Account Auth Token: Jira" \
  --vault Engineering --fields credential --reveal)
JIRA_CLOUD_ID=10449a34-7d09-4681-85d9-038414693fbd \
  python3 scripts/dump-jira-workflow.py
```

Then `git diff workspaces/patch/docs/jira-ids-reference.md` — review what changed, commit, push. Review is important: templates that hardcode transition IDs may need follow-up edits when IDs change (see `workspaces/patch/templates/*.md`).

### `scripts/generate-github-app-token.sh`

Emits a 1-hour GitHub App installation token for `sc0red-patch`. Called by Patch's ready-for-dev templates when she needs to clone a private `SC0RED/*` repo. See `workspaces/patch/docs/github-access.md` for the full flow.

Reads credentials from the `GitHub App: sc0red-patch` item in 1Password Engineering (`app_id`, `installation_id`, `rsa_key`). Prints the token to stdout for capture:

```bash
export GH_TOKEN=$(bash scripts/generate-github-app-token.sh)
git clone https://x-access-token:${GH_TOKEN}@github.com/SC0RED/Platform-Frontend.git
```

---

## Template doc-injection: `{{doc:...}}` conventions

Templates use Nunjucks. `{{doc:path/to/file.md}}` is the Clawndom-side extension that inlines the named file at render time. Path is relative to the agent workspace root (so `{{doc:docs/SOUL.md}}` pulls `workspaces/patch/docs/SOUL.md`).

**Safety rule:** nothing injected can contain a literal `{{` — Nunjucks will try to parse it as a template tag. When a doc needs to reference the doc-injection syntax in prose (e.g. `TOOLS.md` explaining how it all works), describe it in words rather than showing a literal example. Hitting this footgun blocks every template render.

---

## Adding a new agent

To stand up a second agent:

1. Create `workspaces/<name>/` with the subdirectory skeleton: `templates/`, `docs/`, `avatars/`, `specs/`.
2. Author:
   - `CLAUDE.md` — bootstrap + hook-session block
   - `clawndom.yaml` — routing rules for whichever webhooks this agent consumes
   - `docs/IDENTITY.md`, `docs/SOUL.md`, `docs/TOOLS.md`, `docs/USER.md` — start from Patch's as templates
   - Per-status templates under `templates/`
3. Push. Clawndom picks up the new agent on next sync.

Shared docs (like the engineering pipeline) can be copied or cross-referenced — the current split lives under each agent's workspace, not at the repo root, so each agent has full control over its own context.

---

## Related repositories

- **[SC0RED/clawndom](https://github.com/SC0RED/clawndom)** — the webhook proxy / agent runner. Reads this repo at runtime.
- **SC0RED/Platform-Frontend**, **SC0RED/Platform-Backend**, **SC0RED/assessment_engine** — the codebases Patch works on. Accessed via the `sc0red-patch` GitHub App (see `workspaces/patch/docs/github-access.md`).

## Current runtime infrastructure

- EC2 host: `c7i.large` in `sc0red-dev` (us-east-1), reachable at `clawndom.tail708f46.ts.net` via Tailscale Funnel.
- Service: `clawndom.service` (systemd, auto-start enabled).
- Sync timer: `clawndom-sync-agents.timer` pulls this repo every 5 minutes.
- Toolchain on the host: Node 18 (via nvm) + 22 (system), Python 3.12, uv, ruff, pyright, vulture, mypy, pytest, mongosh, Google Chrome, sonar-scanner, AWS CLI v2, `op`, `gh`, `git`. Full inventory in `workspaces/patch/docs/TOOLS.md`.
