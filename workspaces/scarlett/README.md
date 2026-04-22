# Scarlett — workspace README

This directory is Scarlett's workspace. Her job is review: plan reviews for Patch's Jira plan comments, and PR reviews for Patch's code changes. She's triggered by `agent.task.request` events dispatched through Clawndom's `/api/tasks` endpoint (not Jira webhooks directly), returns an `agent.task.response` with a verdict (`approve` / `changes_requested`), and on approval transitions the ticket to the next status; on rejection, Patch's `handle-*-review` template addresses each point.

For hook-session runs, the triggering template injects everything needed. This README is for humans and for rare interactive `claude` sessions on the host.

## Where it runs

Same EC2 as Patch: `clawndom.tail708f46.ts.net` over Tailscale Funnel. Workspace at `/home/clawndom/.clawndom/agents/SC0RED__the-agency/workspaces/scarlett/`, auto-refreshed every 5 minutes by `clawndom-sync-agents.timer`.

Linux (Ubuntu 24.04). Shared tool inventory at `../shared/TOOLS.md`.

## Reading list (interactive sessions)

- **`docs/IDENTITY.md`** — name, creature, vibe.
- **`docs/SOUL.md`** — reviewer principles, voice, what I do / don't do.
- **`../shared/USER.md`** — who Chris is (operator metadata).
- **`../shared/TOOLS.md`** — host tool inventory (same as Patch's — it's shared).
- **`../shared/sc0red-engineering-pipeline.md`** — the full engineering pipeline. I need to understand it to know where my review fits.
- **`../shared/writing-great-issues-base.md`** + type specializations — my rubric for judging plan quality.
- **`../shared/anti-patterns.md`** — AI anti-patterns I actively flag in reviews.
- **`../shared/estimation.md`** — the Risk × Intensity scoring I validate plan estimates against.
- **`../shared/jira-ids-reference.md`** — transitions I apply after approving, and the cloudId for comments.
- **`../shared/github-access.md`** — GitHub App auth for reading PR diffs + posting PR comments.
- **`../shared/hook-session-protocol.md`** — non-negotiable rules for webhook-triggered runs.

## My authority boundary

- I review. I do **not** write fix code. My runner is configured with `--disallowedTools Edit,Write` — mechanical enforcement of "reviewer doesn't touch code."
- I do **not** merge PRs. Merge is a deployment; humans handle that.
- I return one verdict. If Patch's response to my feedback needs another round of mine, that's the signal to escalate — the reporter gets the ticket.

## Trigger surface (when the infrastructure ships)

Scarlett is triggered by `agent.task.request` events via Clawndom's `/api/tasks` endpoint (SPE-1707). Two kinds:

- `plan-review` — inputs: Jira ticket key + plan comment ID. Outputs: verdict via `agent.task.response`; on `approve`, transition the ticket to Plan Review (35); on `changes_requested`, dispatch a response task back to Patch.
- `code-review` — inputs: Jira ticket key + GitHub PR URL(s). Outputs: line-level PR comments + summary + verdict; on `approve`, transition to Code Review (36); on `changes_requested`, dispatch response task to Patch.

Templates live at `templates/review-plan.md` and `templates/review-pr.md` (TODO — infrastructure dependency).

## Runner config (planned)

Scarlett uses the `claude-cli` runner on Claude Opus (same as Patch) during initial rollout. The Codex CLI runner is planned but deferred (we want the review loop working end-to-end on one model family first, then swap).

In `clawndom.yaml`:

```yaml
# TODO once /api/tasks agent-task routing lands
runner:
  type: claude-cli
  disallowedTools: [Edit, Write]
```
