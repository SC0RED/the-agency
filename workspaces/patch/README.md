# Patch — workspace README

This directory is Patch's workspace. Webhook-triggered runs are the primary mode: Clawndom matches the inbound event to a routing rule, the rule's template is rendered with the doc-injection helpers, and `claude -p` runs against the rendered prompt. This README is for humans operating the host — agent-facing rules live in `docs/SOUL.md`.

## Where it runs

- Host: `clawndom.tail708f46.ts.net` (dedicated `c7i.large` in `sc0red-dev`, us-east-1, reachable over Tailscale Funnel)
- Workspace path: `/home/clawndom/.clawndom/agents/SC0RED__the-agency/workspaces/patch/`
- Refresh: `clawndom-sync-agents.timer` (systemd) pulls `git@github.com:SC0RED/the-agency.git` every 5 minutes
- OS: Ubuntu 24.04
- Tool inventory: `../shared/docs/TOOLS.md`

## Webhook routing

Jira webhooks arrive at `clawndom.tail708f46.ts.net/hooks/jira`. Clawndom matches them against `clawndom.yaml` and spawns a `claude -p` subprocess with the rendered template. Per-status × per-type templates: **Plan** and **Ready for Development** each have Bug / Story / Task variants under `templates/`. Slack alert webhooks hit `/hooks/slack-alerts-*` and route to `templates/slack-alert.md`.

Edits push to `main`; the 5-minute sync timer pulls them to the host.

## For agent-facing rules

- `docs/IDENTITY.md` — name, creature, vibe
- `docs/SOUL.md` — engineering principles, branch discipline, escalation rules, voice
- `../shared/docs/hook-session-protocol.md` — non-negotiable rules for webhook runs
