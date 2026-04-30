# Scarlett — workspace README

This directory is Scarlett's workspace. Her job is review: plan reviews for Patch's Jira plan comments, and PR reviews for Patch's code changes. She's triggered by `agent.task.request` events dispatched through Clawndom's `/api/tasks` endpoint (not Jira webhooks directly), returns an `agent.task.response` with a verdict (`approve` / `changes_requested`), and on approval transitions the ticket; on rejection, Patch's `handle-*-review` template addresses each point.

This README is for humans operating the host — agent-facing rules live in `docs/SOUL.md`.

## Where it runs

- Host: same EC2 as Patch — `clawndom.tail708f46.ts.net` (Tailscale Funnel)
- Workspace path: `/home/clawndom/.clawndom/agents/SC0RED__the-agency/workspaces/scarlett/`
- Refresh: `clawndom-sync-agents.timer` (systemd), every 5 minutes
- OS: Ubuntu 24.04
- Tool inventory: `../shared/docs/TOOLS.md`

## Trigger surface

Scarlett is triggered by `agent.task.request` events via Clawndom's `/api/tasks` endpoint (SPE-1707). Two task kinds:

- `plan-review` — inputs: Jira ticket key + plan comment ID. Outputs: verdict via `agent.task.response`; on `approve`, transition the ticket to Plan Review (35); on `changes_requested`, dispatch a response task back to Patch.
- `code-review` — inputs: Jira ticket key + GitHub PR URL(s). Outputs: line-level PR comments + summary + verdict; on `approve`, transition to Code Review (36); on `changes_requested`, dispatch response task to Patch.

Templates live under `templates/`.

## Runner config

Scarlett uses the `claude-cli` runner on Claude Opus during initial rollout, with `--disallowedTools Edit,Write` — mechanical enforcement of the reviewer-doesn't-touch-code rule. The Codex CLI runner is planned but deferred until the review loop is proven on one model family.

```yaml
runner:
  type: claude-cli
  disallowedTools: [Edit, Write]
```

## Memory

Durable memory lives in Clawndom's vector store, namespaced per agent. Scarlett's namespace is configured in `clawndom.yaml` if/when memory.retrieve is enabled on her routes. Reviewer routes default to no memory — each review is a fresh, evidence-driven read.

## For agent-facing rules

- `docs/IDENTITY.md` — name, creature, vibe
- `docs/SOUL.md` — reviewer principles, verdict format, escalation rules, voice
- `../shared/docs/hook-session-protocol.md` — non-negotiable rules for webhook runs
