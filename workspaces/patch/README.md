# Patch — workspace README

This directory is Patch's workspace. For hook-session runs (webhook-triggered `claude -p`), the template your trigger matches injects everything you need. This README is for humans or for rare interactive `claude` sessions launched directly on the host.

## Where it runs

You run on a dedicated c7i.large EC2 in `sc0red-dev` (us-east-1), reachable as `clawndom.tail708f46.ts.net` over Tailscale Funnel. Your workspace is at `/home/clawndom/.clawndom/agents/SC0RED__the-agency/workspaces/patch/`, auto-refreshed every 5 minutes from `git@github.com:SC0RED/the-agency.git` by the `clawndom-sync-agents.timer` systemd timer.

You are on Linux (Ubuntu 24.04). For the tool inventory, see `../shared/TOOLS.md`.

## Reading list (interactive sessions)

- **`docs/IDENTITY.md`** — your name, creature, vibe.
- **`docs/SOUL.md`** — your engineering principles and what Chris expects of you.
- **`../shared/USER.md`** — who Chris is (operator metadata).
- **`../shared/TOOLS.md`** — host tool inventory.
- **`../shared/sc0red-engineering-pipeline.md`** — the full engineering pipeline.
- **`../shared/writing-great-issues-base.md`** + type specializations (`writing-great-bug-issues.md`, `writing-great-feature-issues.md`, `writing-great-task-issues.md`) — ticket-quality guides.
- **`../shared/anti-patterns.md`** — AI anti-patterns to avoid in plans and code.
- **`../shared/estimation.md`** — Risk × Intensity scoring.
- **`../shared/jira-ids-reference.md`** — transition / field / option ID lookup (generated; regenerate with `scripts/dump-jira-workflow.py`).
- **`../shared/github-access.md`** — GitHub App auth flow for cloning private SC0RED repos and opening PRs.
- **`../shared/ux-quality-gate.md`** — frontend UX checklist.
- **`MEMORY.md`** (if present) — long-term memory index.

## Quick rules for interactive sessions

- Read today's and yesterday's daily memory files (`memory/YYYY-MM-DD.md`) for ambient context, if they exist.
- Memory-first: check memory before asking humans anything.
- No implementation without human approval (ticket moved to Ready for Development).
- All fixes target `development`. Never touch `testing` or `production` branches directly.
- Clean PRs with tests — a fix without a test is not done.
- Discord/Slack: no markdown tables, use bullet lists.

## Webhook routing

Jira webhooks arrive at `clawndom.tail708f46.ts.net/hooks/jira`. Clawndom matches them against `clawndom.yaml` routing rules and spawns a Claude CLI subprocess with the appropriate template. Per-status × per-type templates: **Plan** and **Ready for Development** each have Bug / Story / Task variants under `templates/`. Slack alert webhooks hit `/hooks/slack-alerts-*` and land on `templates/slack-alert.md`.

Edits to this repo push to `main` and the 5-minute sync timer pulls them to the host.

## Hook-session discipline

See `../shared/hook-session-protocol.md` — the non-negotiable rules that apply to every webhook-triggered run (isolation, tool loading, failure protocol).
