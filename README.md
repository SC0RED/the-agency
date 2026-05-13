# the-agency

<img src="workspaces/patch/avatars/patch.jpg" alt="Patch" width="140" align="right">
<img src="workspaces/scarlett/avatars/scarlett.jpg" alt="Scarlett" width="140" align="right">

Workspaces for sc0red's engineering agents: **Patch** (AI software engineer) and **Scarlett** (reviewer). They share an EC2, share the engineering pipeline, and share most of the prose docs that define how sc0red builds software.

## What they do

**Patch** is the AI engineer. He plans, implements, and ships work as Jira tickets move through the engineering pipeline:

- Investigates a ticket in **Plan**, posts the plan, hands it to Scarlett for review.
- Implements the approved plan in **Ready for Development**, opens PR(s), handles CI + CodeRabbit, hands the PR(s) to Scarlett for code review.
- Merges approved PRs in **Deploy to development** and advances the ticket.
- Pulse-promotes `development → testing` once tickets reach **Verified in Development**.
- Diagnoses pipeline alerts in the three `#alerts-platform-failure-*` Slack channels and either comments on the existing bug or creates one.
- Wakes up out-of-band on PR CI failures.

**Scarlett** is the reviewer. She doesn't write fix code, doesn't merge PRs — she reviews plans and code against the five-axis rubric (correctness, design, consistency, edge cases, tests), posts a verdict, and dispatches Patch back to the desk on `changes_requested`. She also posts a daily handoff to `#general-engineering` Mon–Fri 7:45 AM ET.

Each agent's identity, voice, and service-account auth live in `workspaces/<agent>/identity/`.

## Where things live

Standard Clawndom workspace shape — see [`clawndom/docs/guides/AGENT_WORKSPACE_LAYOUT.md`](https://github.com/SC0RED/clawndom/blob/main/docs/guides/AGENT_WORKSPACE_LAYOUT.md). Multi-agent variant: `workspaces/shared/` carries cross-agent prose (engineering pipeline, anti-patterns, issue-writing guides, jira-write-auth, etc.); `workspaces/scripts/` carries the operator scripts templates shell out to (token generators, workflow-id dumps).

Every Jira write authors as the agent's dedicated Atlassian service account, not as Chris — see `workspaces/shared/jira-write-auth.md`. Same shape for Slack: per-agent bot tokens.

## Related

- [`SC0RED/clawndom`](https://github.com/SC0RED/clawndom) — the runtime.
- [`SC0RED/agency-tools`](https://github.com/SC0RED/agency-tools) — typed Python tool library. Not yet a runtime dependency for Patch/Scarlett (they shell out today); SPE-2078 migration is on the roadmap.
- [`ctcreel/winston-agency`](https://github.com/ctcreel/winston-agency) — Winston, the TALK office-manager agent. Same workspace shape, single-agent variant.
