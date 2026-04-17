> Version: 2.7 - 2026-04-06
> Author: Scarlett, revised by Chris Creel
> Status: Approved
---

## Overview

This document defines how engineering work flows from request to production at sc0red. It covers ticket lifecycle, agent responsibilities, human gates, branching strategy, and environment promotion.

Every engineer and agent follows this process. No exceptions.

**Related documents:**
- [Estimation & Prioritization Framework](./sc0red-estimation-framework.md) - how we estimate, score, and order work
- [Writing Great Jira Issues](../Protocols/writing-great-jira-issues.md) - issue structure, architectural review requirements, and refactoring guidance
- [Extracting Workflow Transitions from Jira](./sc0red-jira-workflow-extraction.md) - how to map transition IDs from team-managed projects

---

## Roles

| Role                    | Who                            | Responsibility                                                              |
| ----------------------- | ------------------------------ | --------------------------------------------------------------------------- |
| **Requester**           | Any user or team member        | Submits feature request or bug report                                       |
| **Business Leadership** | Chris, Zack, Brian             | Prioritizes, sets requirements, moves to Plan                               |
| **Patch** (Agent)       | Senior AI Engineer             | Investigation, design, implementation, PR creation, environment promotion   |
| **Scarlett** (Agent)    | Senior Reviewer                | Plan review, PR code review, architectural oversight                        |
| **Engineering Team**    | Srikanth, Vedratna, Srilakshmi | PR review, verification in dev/testing, production readiness                |
| **Production Approver** | Chris Creel (only)             | Approves production deployments                                             |

---

## Event-Driven Architecture - Clawndom

All agent work is triggered by **Jira webhooks** via **Clawndom**, a webhook proxy that sits between Jira and OpenClaw. Clawndom:

1. Receives Jira webhooks via Tailscale Funnel
2. Validates HMAC signatures
3. Queues events in Redis (BullMQ)
4. Routes to the correct agent based on the issue's status name
5. Delivers one event at a time (global serialization via `MAX_CONCURRENT_RUNS=1`)
6. Waits for the agent session to complete before delivering the next event
7. Retries on failure (max 2 attempts, back-of-queue retry)

Each webhook spawns an **isolated agent session** - Patch's main thread is never interrupted. Clawndom handles serialization, so agents do not need to implement their own work gates or priority selection. They process whatever Clawndom feeds them, in order.

**Routing rules** match on `issue.fields.status.name` and render a Nunjucks message template with the Jira payload before delivering to the agent.

**Config:** `PROVIDERS_CONFIG` JSON env var in the launchd plist. Templates live at `~/.openclaw/workspace-patch/templates/`.

---

## Board Columns (Jira Statuses)

The Task workflow has **18 statuses** across three categories and **30 transitions** (12 global, 18 directed).

**Linear flow:**
```
New → Plan → In Planning → Plan Review → Ready for Development → In Development
  → Code Review → Deploy to development → Deployed to Development
  → Verified in Development → Deployed to Testing → Verified in Testing
  → Deployed to Production
```

**Side statuses** (reachable from any status via global transitions):
- **Triage** / **Backlog** — evaluation and deferral
- **Blocked** — awaiting human resolution
- **Hotfix** — emergency path direct to production
- **Abandon** — terminal, work will not be completed

**Reverse transitions** exist at key decision points: In Planning can return to Plan ("Stalled"), Plan Review and Code Review can return to Plan ("Replan"), and In Development can return to Ready for Development ("Stalled").

| Column                  | Transition ID | Category    | Global? | Routed to Agent?                                             |
| ----------------------- | ------------- | ----------- | ------- | ------------------------------------------------------------ |
| New                     | 11            | To Do       | Yes     | No                                                           |
| Triage                  | 2             | To Do       | Yes     | No                                                           |
| Backlog                 | 30            | To Do       | Yes     | No                                                           |
| Plan                    | 16            | In Progress | No      | **Yes** - Patch investigates, writes plan                    |
| In Planning             | 14            | In Progress | No      | No                                                           |
| Plan Review             | 3             | In Progress | No      | No - human gate                                              |
| Ready for Development   | 28            | In Progress | Yes     | **Yes** - Patch implements                                   |
| In Development          | 19            | In Progress | No      | No                                                           |
| Code Review             | 20            | In Progress | No      | No - human gate                                              |
| Deploy to development   | 8             | In Progress | No      | **Yes** - Patch merges PR, moves to Deployed to Development  |
| Deployed to Development | 32            | In Progress | Yes     | No - awaiting engineer verification                          |
| Verified in Development | 12            | In Progress | Yes     | **Yes** - Patch checks gate, batch promotes to testing       |
| Deployed to Testing     | 33            | In Progress | Yes     | No - awaiting reporter/engineer verification                 |
| Verified in Testing     | 5             | In Progress | Yes     | **Yes** - Patch checks gate, creates production PR           |
| Deployed to Production  | 31 ("Done")   | Done        | Yes     | No                                                           |
| Hotfix                  | 13            | In Progress | Yes     | **Yes** - Patch creates PRs against production + back-merges |
| Blocked                 | 4             | To Do       | Yes     | No - human resolves                                          |
| Abandon                 | 9             | Done        | Yes     | No - terminal state                                          |

---

## Ticket Lifecycle

### 1. New
- **Who creates:** Requester (user, PM, human engineer, agent engineer)
- **What happens:** Ticket exists but hasn't been evaluated
- **Next:** Business leadership reviews, triages, and prioritizes

### 1a. Triage
- **Who transitions:** Business leadership or any team member
- **What happens:** Ticket is being evaluated for priority, scope, and feasibility. Used when a ticket needs discussion or investigation before committing to planning.
- **Global:** Yes - any ticket can be moved to Triage from any status
- **Next:** Business leadership moves to Plan (if approved), Backlog (if deferred), or Abandon (if rejected)

### 1b. Backlog
- **Who transitions:** Business leadership
- **What happens:** Ticket is accepted but deferred - not prioritized for immediate work
- **Global:** Yes - any ticket can be moved to Backlog from any status
- **Next:** Business leadership moves to Plan when ready to prioritize

### 2. Plan
- **Who transitions:** Business leadership
- **Trigger:** Jira webhook → Clawndom → Patch
- **What happens:** Patch immediately picks up the ticket and begins:
  - **Quality gates first** - checks for insufficient info, conflicting info, unclear scope, multiple work items. If any gate fails → Blocked (transition ID: 4) with a comment explaining what's needed.
  - **Investigation** - check logs, database, CloudWatch. Form diagnosis from evidence.
  - Root cause analysis (bugs) or requirements analysis (features)
  - Risk assessment and severity estimation per the [Estimation & Prioritization Framework](./sc0red-estimation-framework.md)
  - Story point lookup from the Risk × Intensity matrix
  - If SP > 5: must propose a breakdown before implementation
  - Design proposal with affected files, line numbers, and approach

- **Design quality requirements:**
  - Prefer structural improvements over quick fixes. If the underlying architecture is wrong, say so.
  - Apply established design patterns (GoF, architectural patterns) where appropriate - don't invent when a known pattern fits.
  - Consider downstream consequences - will this fix create the next bug? Does this component need extraction, not patching?
  - Small files, typed interfaces, consistent patterns. If you're adding to a god file, flag it.
  - A hack that ships is still a hack. Propose the right fix; if time/risk forces a compromise, document the tech debt explicitly.

- **Review request:** Patch spawns a Scarlett subagent for review. Scarlett reviews and sends verdict via `sessions_send`.
- **Transition:** Patch posts plan as Jira comment, updates custom fields (Risk, Intensity, Story Points, Velocity Impact), transitions to **In Planning** (ID: 14). Patch continues working; when plan is complete, transitions to **Plan Review** (ID: 3).

### 3. Plan Review
- **Who reviews:** Scarlett (agent) + Engineering team (human)
- **Scarlett checks:**
  - Is this solving the right problem? Root cause or symptom?
  - Does the design use appropriate patterns, or is it a hack?
  - Structural/architectural implications - god files, tight coupling, missing abstractions?
  - Would a refactor serve better than a patch?
  - Edge cases, downstream consequences, cross-component impact
  - Is the estimation reasonable given the risk and severity?
- **Human review:** Engineers review Patch's plan (already vetted by Scarlett). May refine or approve as-is.
- **Next:** Engineer moves ticket to **Ready for Development**

### 4. Ready for Development
- **Who transitions:** Engineering team
- **Trigger:** Jira webhook → Clawndom → Patch
- **What happens:** Clawndom serializes delivery - Patch processes one ticket at a time, in queue order. No priority selection or work gates needed; Clawndom handles sequencing.
- **Patch's process:**
  1. **Immediately** transitions to **In Development** (ID: 19) - board reflects reality before any work starts
  2. Gets Jira OAuth token
  3. Reads the approved plan from Jira comments
  4. Creates branch: `fix/<jira-key>-<short-slug>` off `development`
  5. Spawns Claude Code to implement exactly the approved plan
  6. Reviews output - diff matches plan, tests exist, no scope creep
  7. Opens PR against `development`
  8. Posts PR link as Jira comment
  9. Handles automated review feedback (CodeRabbit, SonarCloud)
  10. Spawns Scarlett subagent for PR review

### 5. In Development
- **Scarlett reviews the PR:**
  - Correctness - does it match the approved plan?
  - Design quality - follows established patterns? Appropriate abstractions?
  - Consistency - follows existing conventions in the codebase?
  - Edge cases - stale refs, race conditions, missing null checks?
  - Tests - adequate coverage?
- **How:** Scarlett posts review comments on the **GitHub PR** (permanent record for humans), then sends verdict via `sessions_send`.
- **Back-and-forth:** Patch addresses feedback, pushes updates, spawns another Scarlett review. Repeat until clean.
- Once Scarlett approves → Patch transitions to **Code Review** (ID: 20), posts consolidated Jira comment listing all PRs

### 6. Code Review
- **Who transitions here:** Patch (after Scarlett approves)
- **What it means:** PRs are open, Scarlett has approved, ready for human engineer review.
- **Jira comment:** Patch posts a consolidated comment listing every open PR for this ticket.
- **Human PR Review:**
  - Human engineer reviews from Jira (any human team member, not Chris specifically)
  - Focus on: business logic correctness, UX implications, judgment calls
  - **If changes needed:** Move ticket back to **Ready for Development** (ID: 28). Patch picks it up, reworks, and cycles back through.
  - **If approved:** Move ticket to **Deploy to development** (ID: 8).

### 7. Deploy to development
- **Who transitions:** Engineer (after PR approval)
- **Trigger:** Jira webhook → Clawndom → Patch
- **What happens:**
  1. Patch finds the PR
  2. Runs local validation (type check + tests per repo — see Build Validation table)
  3. If local validation fails → fix issues before merging, do not waste CI
  4. Merges PR to `development` (squash + delete branch)
  5. Posts Jira comment confirming merge
  6. Transitions ticket to **Deployed to Development** (ID: 10)
- **Next:** Engineers verify the fix works in the dev environment, then move to **Verified in Development**

### 7a. Deployed to Development
- **Who transitions here:** Patch (after merging PR)
- **What it means:** Code is merged and deployed to development.sc0red.ai, awaiting human verification.
- **Next:** Engineers verify the fix works in dev, then move to **Verified in Development** (ID: 21)

### 8. Verified in Development
- **Who transitions:** Engineer (after verifying fix works in dev)
- **Trigger:** Jira webhook → Clawndom → Patch
- **Gate logic:** Patch checks if ANY tickets remain in **Deployed to Development** OR **Deploy to development**
  - **If yes (either column has tickets):** Posts comment listing what's still awaiting verification or in flight. Stops.
  - **If no (both empty):** Proceeds to batch promote.
- **Batch Promotion:**
  1. Collects all tickets in "Verified in Development"
  2. Creates a **single** development → testing PR per repo (Frontend, Backend, Engine)
  3. **Merges** those PRs
  4. Transitions all verified tickets to **Deployed to Testing** (ID: 23)

### 8a. Deployed to Testing
- **Who transitions here:** Patch (during batch promotion from Verified in Development)
- **What it means:** Code is deployed to testing.sc0red.ai, awaiting verification by the issue reporter or engineers.
- **Next:** Reporter/engineer verifies the fix works in testing, then moves to **Verified in Testing** (ID: 18)

### 9. Verified in Testing
- **Who transitions:** Reporter or engineer (after verifying fix works in testing)
- **Trigger:** Jira webhook → Clawndom → Patch
- **Gate logic:** Patch checks if ANY tickets remain in **Deployed to Testing**
  - **If yes:** Posts comment listing what's still awaiting verification. Stops.
  - **If no (all verified):** Creates a **single** testing → production PR per repo. **Does NOT merge.** Posts to #general-engineering alerting that a production PR is ready for Chris to review. Tickets stay in Verified in Testing.

### 10. Deployed to Production
- **Who transitions:** Chris (after merging production PRs)
- **What happens:** Done. Ticket closed.

---

## Hotfix Flow

For critical fixes that must reach production immediately. Hotfixes bypass the normal pipeline entirely — no Plan Review, no Code Review column. The urgency is the process; review happens on the PR itself.

**If production is truly catastrophic:** Chris goes off-script. It won't hit the board, and that's fine.

### Process
1. Engineer moves ticket to **Hotfix** (ID: 13) from wherever it is (New, Plan, Blocked — doesn't matter)
2. **Trigger:** Jira webhook → Clawndom → Patch
3. **Patch's process:**
   a. Investigates the issue against **production** code and logs — not development. The fix must work in the codebase it's shipping to.
   b. Creates branch `hotfix/<jira-key>-<slug>` off **`production`** (not development)
   c. Implements the minimal fix — smallest possible change to resolve the issue
   d. Runs local validation against the production-based branch
   e. Opens PR against `production` — titled `HOTFIX(<key>): <summary>`
   f. Spawns Scarlett for **urgent** review (scope: does this fix the problem without breaking anything else?)
   g. Posts PR link to Jira + alerts #general-engineering
   h. **Does NOT merge** — Chris merges the production PR
4. **After Chris merges to production:**
   a. Patch creates back-merge PRs: `production` → `testing` and `production` → `development`
   b. Posts back-merge PR links to Jira
   c. Human merges back-merge PRs (or Patch merges if instructed)
   d. Ticket moves to **Deployed to Production** (ID: 31)

### Branching
- Normal flow: feature branch off `development`, PRs target `development`
- Hotfix flow: branch off **`production`**, PR targets `production`. Back-merges flow downward after production merge.
- This ensures the fix is authored against production from the start — no rebasing development work onto production, no conflict risk from unrelated changes

### What triggers the back-merge?
The production merge itself. When Chris moves the ticket to Deployed to Production (or tells Patch to create back-merges), Patch creates the downward PRs. Not before — the production PR might get feedback and change, which would make premature back-merge PRs stale.

---

## Blocked

"Blocked" (transition ID: 4) is a universal status used across the entire pipeline when:
- Ticket has insufficient information, conflicting requirements, or unclear scope
- CI fails on a PR
- Testing branch is out of sync
- No approved plan exists
- Any situation requiring human intervention

**Who moves to Blocked:** Patch (any template) or any human
**Who resolves:** The original reporter or an engineer. After resolving, they move the ticket back to the appropriate column (Plan, Ready for Development, etc.), which re-triggers the Clawndom webhook.

---

## Abandon

"Abandon" (transition ID: 9) is a terminal status used when a ticket will not be completed. It is a global transition - any ticket can be abandoned from any status.

**When to use:**
- Requirements no longer relevant (business pivot, feature superseded)
- Duplicate of another ticket
- Investigation determined the issue doesn't exist or isn't reproducible
- Cost/benefit doesn't justify the work

**Who transitions:** Business leadership or the original reporter
**Category:** Done (green) - the ticket is resolved, just not by completing the work

---

## Promotion Protocol - Gate-Driven Branch Merges

Individual tickets merge to `development` via per-ticket PRs. Promotions between environments are **gate-driven** - triggered automatically when all tickets in a deployment column are verified.

### Development → Testing
- **Trigger:** Ticket moves to "Verified in Development"
- **Who executes:** Patch (automatic via Clawndom webhook)
- **Gate:** Both "Deploy to development" AND "Deployed to Development" must be empty
- **Process:**
  1. Patch checks both columns - if either has tickets, posts comment and stops
  2. Creates a **single** development → testing PR per repo (all 3 repos)
  3. **Merges** the PRs
  4. Transitions all "Verified in Development" tickets to "Deployed to Testing" (ID: 23)
- **Key rule:** Never promote individual tickets. One PR per repo per batch.

### Testing → Production
- **Trigger:** Ticket moves to "Verified in Testing"
- **Who executes:** Patch creates PRs, **Chris merges**
- **Gate:** "Deployed to Testing" must be empty
- **Process:**
  1. Patch checks "Deployed to Testing" - if any tickets remain, posts comment and stops
  2. Creates a **single** testing → production PR per repo (all 3 repos)
  3. Posts PR links to Jira + alerts #general-engineering
  4. **Does NOT merge** - Chris reviews and merges
- **Key rule:** Never promote individual tickets. One PR per repo per batch.

### Rules
- Development → testing: Patch can merge (automated gate)
- Testing → production: Patch creates PR only, human merges (production gate stays human)
- If CI fails on a promotion PR, something is fundamentally broken — escalate immediately to Chris
- Promotions are all-or-nothing per branch merge. If a specific ticket needs to be held back, it should not be merged to `development` until it's ready to travel with the batch.

---

## Build Validation (by repo)

Before opening a PR, the build must not be broken. What that means varies:

| Repo | Validation Command | What It Checks |
|------|-------------------|----------------|
| Platform-Frontend | `tsc --noEmit` + test suite | Type safety + unit tests |
| Platform-Backend | `pytest` | Unit + integration tests |
| assessment_engine | `make check-all` | Full lint, type check, and test suite |

If the command fails on code you didn't touch, **that's still our problem.** File a ticket immediately, fix it if you can, and note it in your PR. Nothing in this codebase is someone else's job.

---

## Agent Communication - How Engineering Agents Talk

All structured agent-to-agent communication for code review happens via `sessions_send` (spawned subagents):

### Review Flow (sessions_send)
- **Plan review requests:** Patch spawns a Scarlett subagent with Jira link + summary. Scarlett sends verdict via `sessions_send` to `agent:patch:main`.
- **PR review requests:** Patch spawns a Scarlett subagent with PR link + ticket reference. Scarlett reviews on GitHub and sends verdict via `sessions_send`.
- **Back-and-forth:** Patch fixes issues, spawns another Scarlett review. No passive monitoring needed - delivery is guaranteed.

### GitHub PR Comments
- **Code review feedback:** Scarlett posts line-level and summary comments directly on the GitHub PR via `gh`
- **Patch responses:** Patch reads PR comments, pushes fixes, spawns another review
- **Why GitHub:** This is where human engineers will also review. Keeping all code-level discussion on the PR means one place for everyone.

### What goes where
- Review requests → spawned Scarlett subagent
- Code-level feedback → GitHub PR comments + verdict via `sessions_send`
- PR approved, requesting human review → #general-engineering (Slack)
- Blocked on something → #general-engineering (Slack)

---

## Branching Strategy

| Branch | Environment | Purpose |
|--------|-------------|---------|
| `development` | Development | Active development, all feature branches merge here |
| `testing` | Testing | Verified dev changes promoted for stakeholder testing |
| `production` | Production | Release branch, Chris-only merge approval |

- Feature/fix branches: `fix/<jira-key>-<short-slug>` off `development`
- Hotfix branches: `fix/<jira-key>-<slug>` **rebased onto `production`**, with back-merge PRs to testing and development
- No direct commits to `testing` or `production` - always via PR

---

## Communication Channels

| Channel | Platform | ID | Purpose |
|---------|----------|----|---------|
| **#general-engineering** | Slack | C06TRR7A894 | PR review requests to humans, blocked tickets, production readiness pings, deploy confirmations |
| **#general-engineering-qa** | Slack | C0ALJS0M2NR | QA findings, test results, plan summaries |
| **#alerts-platform-failure-*** | Slack | Various | Automated error alerts (dev/testing/production) |
| **#general** | Discord (The Agency) | 1478849414629032154 | Cross-agent coordination, non-review discussion |
| **Jira comments** | Jira | - | Plan proposals, review feedback, permanent technical record |
| **GitHub PR comments** | GitHub | - | Code-level review (Scarlett + engineers) |

---

## Escalation Rules

Patch escalates to Chris (moves to Blocked or flags in Slack) when:
- Fix touches auth or security
- Root cause is in the backend API contract
- Estimated risk is High
- She disagrees with a human reviewer's feedback and can't resolve it
- CI fails for reasons outside her change

---

## Implementation Tooling - Claude Code

Agents use **Claude Code** (via `sessions_spawn` with `runtime: "acp"`) as the implementation engine. Agents don't edit files directly for multi-file changes - they spawn Claude Code sessions with full repo context, the approved plan, and coding standards.

### Why Claude Code
- Loads full repo into context - file trees, type definitions, imports, test suites
- Makes coherent multi-file changes that respect existing patterns
- Runs in-process validation (type checking, linting)

### Session Lifecycle
1. Agent receives work from Clawndom (ticket in the appropriate status)
2. Agent spawns Claude Code with: repo path, branch, task description, constraints
3. Claude Code executes - writes code, runs checks
4. Agent reviews output - commits, test results, diff quality
5. Session terminates - RAM freed

### Local Validation - MANDATORY Before Push

**Never push code that hasn't been validated locally.** CI is not your first line of defense - it's your last.

| Repo | Command | What to check |
|------|---------|---------------|
| Platform-Frontend | `npx ng test --watch=false` + `npx tsc --noEmit` | Unit tests + type check |
| Platform-Backend | `npm test` | Unit tests |
| assessment_engine | `make check-all` | Full lint, type check, and test suite |

**Rules:**
- Type check: **every push, no exceptions**
- Unit tests for changed files: **every push, no exceptions**
- If local validation fails on code you didn't touch: file a ticket, note it in the PR, fix if you can
- **Do not rely on CI to catch problems you could have caught locally in 30 seconds**

### SonarCloud Local Scan - MANDATORY Before Push (Frontend & Engine)

Run a local SonarCloud scan before pushing to catch quality gate violations (code duplication, coverage gaps, code smells) that would otherwise fail CI.

**Applies to:** Platform-Frontend, assessment_engine (Backend has SonarCloud disabled in CI)

**Process:**
1. Pull the Sonar Token from the Engineering vault in 1Password
2. Run `sonar-scanner` with the repo's project key and organization
3. Check the quality gate status via the SonarCloud API
4. If the gate fails: read the violations, fix them, re-scan
5. Do NOT push until the quality gate passes

**If the scan can't run** (network issue, token expired): note it in the PR description and proceed - but this is the exception, not the rule.

### CI Failure Remediation - GitHub Webhook Safety Net

Even with local validation, CI can fail for reasons local scans don't catch (environment differences, flaky tests, dependency issues). A GitHub webhook routes CI failures on Patch's PRs back through Clawndom as isolated fix sessions.

**Flow:**
1. GitHub fires a `check_run` webhook when CI completes
2. Clawndom receives it, validates HMAC, filters to only failed checks on Patch's branches (`fix/SPE-*`)
3. Routes to Patch as an isolated session with failure details
4. Patch reads CI logs, fixes the issue, pushes
5. CI re-runs automatically

**Guardrails:**
- **Max 2 fix attempts per PR.** If the build still fails after 2 automated fix cycles, move the ticket to Blocked and notify #general-engineering.
- **Deduplication:** Clawndom filters duplicate check events for the same commit SHA - only the first failure triggers a fix session.
- **Scope:** Only fires for branches matching `fix/SPE-*` owned by Patch. Does not interfere with human PRs.

---

## Key Constraints

- Clawndom serializes all agent work - one event at a time, completion-aware
- No implementation without an approved plan
- No merge without CI passing
- No production merge without Chris's explicit approval (Patch creates PR only)
- Development → testing promotion: Patch can merge (automated gate)
- Testing → production promotion: Patch creates PR, human merges
- A fix without unit tests is not done
- Prefer structural improvements over quick hacks - if the architecture is wrong, say so
- Refactoring is a valid fix - but requires documented architectural justification and approval

