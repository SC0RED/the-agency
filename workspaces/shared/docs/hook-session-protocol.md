# Hook Session Protocol

Webhook-triggered Claude CLI runs have a session key that starts with `hook-` (e.g. `agent:<you>:hook-jira-156`). If you are running in a hook session, the rules below are non-negotiable. They apply to every agent in the-agency.

## Isolation

- You are an isolated webhook handler. Execute ONLY the template message you received.
- Your template already injects everything you need via Nunjucks doc-injection: IDENTITY, SOUL, TOOLS, pipeline, anti-patterns, jira-ids-reference, github-access, and any per-task specialization (issue-writing guide for the ticket type, estimation framework for Plan templates, etc.). Do NOT open those files directly.
- Do NOT read docs that weren't injected. If the template doesn't pull a file, you don't need it.
- Do NOT check what other sessions are working on. Inter-agent task dispatch goes through Clawndom's `/api/tasks` endpoint (SPE-1707) — not through file-system snooping.
- **Start executing Step 1 of your template immediately.** No preamble, no context gathering.

## Tool loading

- MCP tools (`mcp__*`) are *deferred*. Calling one directly fails with `InputValidationError`. Load the schemas you need up front with `ToolSearch({query: "select:<name>[,<name>...]"})`. Prefer `select:` over keyword search — it's exact.
- `op` (1Password CLI) has `OP_SERVICE_ACCOUNT_TOKEN` already in env. Call it directly.
- `aws` CLI v2 has `sc0red-dev` as the default profile, `us-east-2` as the default region.

## Failure protocol — MANDATORY

If you hit a blocker you cannot resolve — a missing tool, a missing credential, scope you can't reach, a template instruction that doesn't match reality — **leave a trail before you stop**. The exact channel depends on your trigger source:

- **Jira-triggered run** — post a Jira comment on the originating ticket (use `mcp__claude_ai_Atlassian__addCommentToJiraIssue`; the cloudId is in `jira-ids-reference.md` which your template injects — don't hardcode it here).
- **Slack-triggered run** — reply in the alert thread (same Slack thread root the trigger came from).
- **Agent-task run (dispatched from another agent via `/api/tasks`)** — emit an `agent.task.response` with `verdict: blocked` and a body explaining the blocker, so the sender can route the problem.

The comment must state:

- What you were trying to do (step of the template, not internal jargon).
- What blocked you (specific error, missing thing, tool that failed).
- What you need from a human to unblock (one concrete ask).

Silent failure is the worst failure. A ticket sitting in its status with zero comments and zero transitions looks identical to a ticket Clawndom never received. Leaving a trail — even "I'm blocked on X, please Y" — is non-negotiable and is your final obligation before ending the run.

This applies whether you've used 2 turns or 22. If you can't finish the task, you can still leave the blocker.
