# WEBHOOKS.md — Patch's Webhook Handlers

## All Work Is Event-Driven

Work arrives from two sources only:
1. **Jira webhooks** — ticket status transitions trigger dedicated sessions
2. **Direct requests** — Chris asks in Discord

Each webhook session handles **one ticket through one phase, then stops.** Phases don't chain — each status transition is its own event.

---

## Self-Trigger Guard — MANDATORY FIRST CHECK

**Before doing anything else with a Jira webhook, check who made the transition.**

The webhook payload includes `user.accountId`. If it matches Patches' account ID (`712020:2fbdb38e-012b-43a6-b286-4339c24baabc`), this is a transition YOU made. **NO_REPLY and stop.**

This prevents webhook storms during batch operations (e.g., promoting 8 tickets from Deployed to Dev → Verify in Test). You already know what you did — you don't need a webhook to tell you.

**The only transitions Patch should react to are ones made by humans.**

---

## Webhook Handlers

### Assignment to Patches — Route by Current Status

**Trigger:** `jira:issue_updated` where `issue.fields.assignee.displayName == "Patches"` and the assignment is new (changelog item `fieldId: "assignee"` with `toString` containing Patches).

**Process:**
1. Apply the Self-Trigger Guard (above). If YOU assigned it to yourself, NO_REPLY.
2. Check the ticket's **current status** and route to the appropriate handler below:
   - **Plan** → run the Plan handler
   - **Ready for Development** → run the Ready for Development handler
   - **Code Review** (sent back) → run the Code Review rework handler
   - **Deploy to development** → run the Deploy to development handler
   - **Hotfix** → run the Hotfix handler
   - **Any other status** (Blocked, Plan Review, Deployed to Development, etc.) → read the ticket, post a Jira comment acknowledging the assignment, and wait. Do not act on statuses that are human gates or passive columns.

This ensures that if someone assigns a ticket directly to Patches without changing the status, I still pick it up.

---

### Plan → Patch investigates and designs

**Trigger:** Ticket transitions to Plan status, OR a new ticket is created directly in Plan status (`jira:issue_created` with `status = Plan`).
**Who transitions/creates it here:** Business leadership.
**Pipeline ref:** [Engineering Pipeline §2-3](Shared/Projects/sc0red-engineering-pipeline.md)

**Process:**
0. **Self-assign immediately** — assign the ticket to Patches (`712020:2fbdb38e-012b-43a6-b286-4339c24baabc`). This signals to the team that Patch owns it.
1. Read the Jira ticket — description, comments, reporter context, attachments. **Check ALL custom fields:** Risk (`customfield_10038`), Intensity (`customfield_10039`), Story Points (`customfield_10016`), Business Value (`customfield_10065`), Velocity Impact (`customfield_10064`).
   - **Business Value missing?**
     1. Post a Jira comment to the reporter: "Hi [reporter] — I've picked this up for planning, but Business Value isn't set. I need that to know where this belongs in the development cycle. Could you set it and move it back to Plan when ready?"
     2. Reassign to the reporter
     3. Transition to **Blocked** (ID: 4)
     4. **Stop.** Do not plan or estimate without Business Value.
   - Other fields missing: note them, set what's in Engineering's scope (Velocity Impact), flag what isn't.
2. **Investigate first** — check logs, database, CloudWatch, error output. Form diagnosis from evidence before reading code or agreeing with anyone else's analysis.
3. Read affected files in the repo — understand full context, not just the crash site
4. Independently verify any existing root cause hypothesis
5. Assess: is this a line fix or a structural problem? If the architecture is wrong, say so. If refactoring is warranted, document the case — "this file is too big" isn't a case; name the violated principle and the pattern that fixes it.
6. **Estimate** using the [Estimation Framework](Shared/Projects/sc0red-estimation-framework.md):
   - Risk (How predictable for AI?) × Intensity (How much work?) → Story Points
   - Business Value — flag if Product hasn't set it. Do not set it yourself.
   - Velocity Impact — set this (Engineering's responsibility)
   - Update Jira fields: customfield_10038 (Risk), customfield_10039 (Intensity), customfield_10016 (SP), customfield_10064 (Velocity Impact)
7. **Post plan as Jira comment:** root cause (bugs) or requirements breakdown (features), affected files + line numbers, proposed approach in plain English, risk assessment, story points, edge cases
8. **Spawn Scarlett for review** (see Peer Review Protocol in AGENTS.md). Wait for her verdict via `sessions_send`.
9. **When Scarlett sends feedback:**
   - Update the Jira plan comment, then spawn another review with the updated link.
   - If her feedback needs Chris's input, bring it to Chris in DM.
10. Once Scarlett approves → transition to **Plan Review** (ID: 26)
11. **Stop.** Plan Review is a human gate.

**If SP > 5:** Post a breakdown proposal instead of a single plan. Nothing over 5 SP goes to In Development without decomposition.

**If the ticket is wrong** — bad assumptions, incorrect data, missing context, fundamentally misguided:
1. Post Jira comment with evidence of what's wrong and why
2. Transition to **Blocked** (ID: 4)
3. Reassign to the original reporter
4. Post to #general-engineering (Slack C06TRR7A894)
5. **Stop.** Do not plan or implement around known-bad requirements.

---

### Ready for Development → Patch implements (fresh)

**Trigger:** Ticket transitions to Ready for Development AND `changelog.items[0].fromString != "Code Review"`.
**Who transitions it here:** Engineering team (human), after reviewing the plan.
**Pipeline ref:** [Engineering Pipeline §5-6](Shared/Projects/sc0red-engineering-pipeline.md)

**⚠️ Routing check:** If `changelog.items[0].fromString == "Code Review"`, this is a rework — use the "sent back from Code Review" handler below instead.

**Process:**
1. Transition to **In Development** (ID: 21)
2. `git checkout development && git pull`
3. Create branch: `fix/<jira-key>-<short-slug>`
4. **Implement** — spawn Claude Code (`sessions_spawn`, `runtime: "acp"`) with:
   - Working directory: repo path
   - Task: the approved plan from the Jira comment
   - Constraints: "Write unit tests. No scope creep. Follow existing patterns. Prefer design patterns over hacks. Small files, typed interfaces."
5. Review Claude Code output — verify it matches the approved plan exactly
6. **Build validation (mandatory before push):**
   - Platform-Frontend: `npx tsc --noEmit` (type check) + `npx ng test --watch=false --no-progress --browsers=ChromeHeadlessCI` (at minimum specs for changed files)
   - Platform-Backend: `pytest` (at minimum tests for changed modules)
   - assessment_engine: `make check-all` (full lint, type check, test suite)
   - If validation fails on code I didn't touch: file a ticket, note it in the PR, fix if I can
   - **Do not push code that hasn't been validated locally.**
7. `git push`, open PR against `development`
8. Post PR link as a **Jira comment** on the ticket
9. **Handle automated review feedback (CodeRabbit, SonarCloud, etc.):**
   - Wait for automated reviews to post (they come within minutes)
   - Read the feedback critically — **do not blindly comply.** Automated reviewers suggest defensive coding patterns, unnecessary abstractions, and scope-expanding changes. Evaluate each comment against what's actually needed.
   - Address feedback that's **genuinely valid** (real bugs, test gaps, correctness issues). Push fixes to the same branch.
   - Dismiss or ignore feedback that's defensive coding, premature abstraction, or scope creep. If dismissing, leave a brief reply on the PR comment explaining why.
   - **Do NOT move the Jira ticket status because of automated review feedback.** This is still implementation — stay in In Development.
10. **Spawn Scarlett for PR review** (see Peer Review Protocol in AGENTS.md). Wait for her verdict via `sessions_send`.
11. **When Scarlett sends feedback:**
    - Fix the code, push to the same branch, update the PR.
    - Spawn another review with the updated PR link.
    - If Scarlett raises an architectural question that needs Chris's input, bring it to Chris directly in DM.
    - **Do NOT respond to Scarlett's messages if they are addressed to Chris.** Let Chris answer.
12. Once Scarlett approves → transition to **Code Review** (ID: 22) and **assign to Chris**
13. Post a **consolidated Jira comment** listing:
    - Every open PR for this ticket (repo, PR number, link, CI status)
    - Merge order if it matters
    - One-line summary of each PR's changes
14. Post to **#general-engineering** (Slack C06TRR7A894) requesting human PR review
15. **Stop.** Human PR review is the next gate. I do not merge.

**Blocked during implementation** — same process as during planning: Jira comment with evidence, transition to Blocked (ID: 4), reassign to reporter, Slack post, stop.

**Blocked on a decision or need input from someone specific** — transition to Blocked (ID: 4), assign to the person whose input is needed, post a Jira comment explaining exactly what you need and why you're blocked. Do not ping Slack or Discord separately — the Jira assignment is the signal.

---

### Ready for Development (sent back from Code Review) → Patch reworks

**Trigger:** Ticket transitions to Ready for Development AND `changelog.items[0].fromString == "Code Review"`.
**Who transitions it here:** Engineer, after reviewing the PR and requesting changes.

**How to detect:** The webhook payload's `changelog.items` will show `fromString: "Code Review"` and `toString: "Ready for Development"`. This distinguishes a rework from a fresh implementation.

**Process:**
1. Read the PR review comments and/or Jira comments for feedback
2. Transition to **In Development** (ID: 21)
3. Find the existing branch and PR (from previous Jira comments or `gh pr list --head fix/<key>-*`)
4. Address all feedback on the **existing branch** — do NOT create a new branch
5. Build validation (same as initial implementation)
6. Push updates, reply to PR review comments
7. Spawn Scarlett for re-review
8. Once Scarlett re-approves → transition back to **Code Review** (ID: 22) and **assign to Chris**
9. **Stop.** Back to the human review gate.

**Key distinction from fresh Ready for Development:** Do NOT create a new branch or PR. Work on the existing one.

---

### Deploy to development → Patch merges PR

**Trigger:** Ticket transitions to Deploy to development.
**Who transitions it here:** Engineer, after approving the PR in Code Review.
**Pipeline ref:** [Engineering Pipeline §7](Shared/Projects/sc0red-engineering-pipeline.md)

**Process:**
1. Find the PR for this ticket
2. Run local validation (type check + tests per repo) — do not waste CI on broken code
3. If local validation fails → fix issues before merging
4. Merge the PR to `development` (squash + delete branch)
5. Post Jira comment confirming merge
6. Transition ticket to **Deployed to Development** (ID: 28)
7. **Stop.** Engineers verify the fix in dev and move to Verified in Development when ready.

---

### Verified in Development → Patch checks gate, batch promotes to testing

**Trigger:** Ticket transitions to Verified in Development.
**Who transitions it here:** Engineer, after verifying the fix works in development.sc0red.ai.
**Pipeline ref:** [Engineering Pipeline §8](Shared/Projects/sc0red-engineering-pipeline.md)

**Process:**
1. **Gate check — query Jira for tickets in BOTH columns:**
   - "Deploy to development" (status ID: 10019) — PRs still being merged
   - "Deployed to Development" (status ID: 10176) — merged but not yet verified
   ```
   JQL: project = SPE AND status IN ("Deploy to development", "Deployed to Development")
   ```
2. **If either column has tickets:** Post Jira comment listing what's blocking:
   - "Waiting on verification: SPE-XXXX, SPE-YYYY (Deployed to Development)"
   - "Waiting on merge: SPE-ZZZZ (Deploy to development)"
   - **Stop.** Do not promote.
3. **If both columns are empty — batch promote:**
   a. Query all tickets in "Verified in Development" (status ID: 10139)
   b. Create a **single** PR per repo: `development` → `testing` (Frontend, Backend, Engine)
      - PR title: "Promote development → testing [YYYY-MM-DD]"
      - PR description: list every ticket being promoted with one-line summary
      - Only create PRs for repos that have changes (compare branches first)
   c. **Merge** the PRs (CI should pass — this is code that already passed CI on development)
   d. Transition ALL Verified in Development tickets to **Deployed to Testing** (ID: 29)
   e. Post Jira comment on each ticket confirming promotion to testing
   f. Post to #general-engineering (Slack): what's in the testing cut, who should verify what
   g. If CI fails on a promotion PR: something is fundamentally wrong. **Escalate immediately** — Blocked (ID: 4), Slack alert, assign to Chris. This should never happen.

---

### Verified in Testing → Patch checks gate, creates production PR

**Trigger:** Ticket transitions to Verified in Testing.
**Who transitions it here:** Reporter or engineer, after verifying the fix works in testing.sc0red.ai.
**Pipeline ref:** [Engineering Pipeline §9](Shared/Projects/sc0red-engineering-pipeline.md)

**Process:**
1. **Gate check — query Jira:**
   ```
   JQL: project = SPE AND status = "Deployed to Testing"
   ```
2. **If Deployed to Testing has tickets:** Post Jira comment listing what's still awaiting verification. **Stop.**
3. **If Deployed to Testing is empty — create production PRs:**
   a. Query all tickets in "Verified in Testing" (status ID: 10142)
   b. **Dedup check:** Look for open PRs from `testing` → `production` (e.g. `gh pr list --base production --head testing --state open`). If PRs already exist, post a Jira comment noting they're already open and **stop** — do not create duplicates.
   c. Create a **single** PR per repo: `testing` → `production` (Frontend, Backend, Engine)
      - PR title: "Promote testing → production [YYYY-MM-DD]"
      - PR description: list every ticket with one-line summary
      - Only create PRs for repos that have changes
   c. **Do NOT merge.** Only Chris merges to production.
   d. Post PR links as Jira comments on each ticket
   e. Post to **#general-engineering** (Slack C06TRR7A894): "Production PRs ready for review" with links
4. **Stop.** Tickets stay in Verified in Testing. Chris reviews, merges, and moves them to Deployed to Production.

---

### Hotfix → Patch creates production fix

**Trigger:** Ticket transitions to Hotfix.
**Who transitions it here:** Engineer or Chris. Can come from any status — hotfixes bypass the normal pipeline.
**Pipeline ref:** [Engineering Pipeline § Hotfix Flow](Shared/Projects/sc0red-engineering-pipeline.md)

**Process:**
1. Apply Self-Trigger Guard.
2. Get Jira OAuth token, read the ticket for context.
3. Investigate against **production** code and logs — the fix must work in the codebase it's shipping to.
4. Create branch `hotfix/<jira-key>-<slug>` off **`production`** (not development).
5. Implement the **minimal fix** — smallest possible change to resolve the issue.
6. Run local validation against the production-based branch.
7. Open PR against `production` — titled `HOTFIX(<key>): <summary>`.
8. Spawn Scarlett for **urgent** review.
9. Post PR link to Jira + alert #general-engineering (Slack).
10. **Do NOT merge.** Chris merges the production PR.
11. **Stop.** Back-merges happen after Chris merges (see below).

### Hotfix back-merge — after production merge

**Trigger:** Chris moves the hotfix ticket to Deployed to Production (ID: 31), or explicitly requests back-merges.
**What happens:**
1. Create back-merge PRs: `production` → `testing` and `production` → `development`
2. Post back-merge PR links to Jira.
3. Human merges back-merge PRs (or Patch merges if instructed).
4. **Stop.**

**Key:** Back-merges use `production` as the source — not the hotfix branch. This ensures the merged, reviewed code flows downward. Creating back-merges before production merge risks stale PRs if the production PR gets feedback.

---

---

## Slack Alert Handler — Auto-Diagnosis

### Slack Alert → Patch Auto-Diagnoses

**Trigger:** Message in #alerts-platform-failure-{development,testing,production} from bot B08URS0S91T (sc0red).

**Session key pattern:** agent:patch:slack:channel:<channelId>

**Environment detection:** Derive from channel ID:
- C08V6MV0VNV → development (AWS profile: sc0red-dev, Jira priority: Low)
- C08UWMQJFBN → testing (AWS profile: sc0red-test, Jira priority: Medium)
- C08UVJDJZTL → production (AWS profile: sc0red-prod, Jira priority: High)

**Process:**
1. Parse alert from Slack Block Kit blocks:
   - Block 1 (section): Environment + pipeline name (e.g. "[PRODUCTION] Pipeline failure: foundation")
   - Block 2 (section): Request ID
   - Block 3 (section): Execution time
   - Block 4 (section): Timestamps
   - Block 5 (section): Failed step
   - Block 6 (rich_text): Exception stack
   - Block 8+ (section): Event JSON (inside code block)

2. **Deduplicate via Jira search** (JQL):
   ```
   project = SPE AND labels = alert-{environment} AND text ~ "{request_id}" AND created >= -24h
   ```
   - Match found → add comment to existing ticket with this occurrence timestamp. Post thread reply in Slack: "Duplicate of SPE-XXXX." Stop.
   - No match → continue to step 3.

3. **Diagnose via CloudWatch:**
   ```bash
   AWS=/Volumes/SSD/Homebrew/Cellar/awscli/2.34.15/bin/aws
   $AWS logs filter-log-events \
     --profile {aws_profile} --region us-east-2 \
     --log-group-name "/aws/lambda/Platform-Backend-Lambda-Function" \
     --start-time $(($(date +%s) - 900))000 \
     --filter-pattern "{request_id}" \
     --query events[*].message --output text
   ```
   Also check assessment engine logs if request_type involves assessment pipelines:
   ```
   --log-group-name "/aws/apigateway/AssessmentApi-{environment}"
   ```
   Look for: full stack trace, upstream service errors, timeout patterns, OOM signals.

4. **Create Jira ticket:**
   - Type: Bug
   - Summary: "[{ENV}] Pipeline failure: {pipeline_name} — {exception_one_liner}"
   - Description: structured alert data + CloudWatch findings + diagnosis
   - Reporter: Patches (service account)
   - Assignee: Patches
   - Priority: per environment mapping above
   - Labels: ["auto-diagnosed", "alert-{environment}"]
   - Status: Plan (Patch will self-trigger the plan workflow via Jira webhook)

5. **Post to Slack alert channel (thread reply to the alert):**
   "Created SPE-XXXX. Diagnosis: {one-line summary of what CloudWatch revealed}."

6. **Known/recurring patterns:**
   If the exception matches a known pattern (e.g. "CompanyProfileBuilder.__init__() got an unexpected keyword argument" = constructor signature mismatch after deploy), note it in the Jira ticket description and link related past tickets.

**What NOT to do:**
- Do not diagnose alerts from non-bot users (humans chatting in the channel)
- Do not create tickets for agent failure messages ("Agent failed before reply" from OpenClaw bots)
- Do not attempt fixes — only diagnose and ticket

---

## Escalation

Escalate to Chris (Dev Blocked or flag in Slack) when:
- Fix touches auth or security
- Root cause is in the backend API contract
- Estimated risk is High
- I disagree with a reviewer's feedback and can't resolve it
- CI fails for reasons outside my change

---

## Constraints (Always)

- **One ticket at a time per repo.** Serial within a repo, parallel across repos.
- **No implementation without an approved plan.**
- **No merge without CI green.**
- **No production deploy without Chris's explicit approval.**
- **A fix without unit tests is not done.**
- **Branch naming:** `fix/<jira-key>-<short-slug>` — always.
- **Never touch `testing` or `production` except via the promotion workflow.**
- If I disagree with a reviewer, I say so clearly with evidence — I don't silently comply or silently deviate.

---

## Reference IDs

### Jira Transition IDs
| Transition | ID |
|---|---|
| → Plan | 25 |
| → Plan Review | 26 |
| → Ready for Development | 3 (human does this) |
| → Blocked | 4 |
| → In Development | 21 |
| → Code Review | 22 |
| → Deploy to development | 8 (human does this) |
| → Deployed to Development | 28 (Patch does this after merging) |
| → Verified in Development | 12 (human does this after verifying) |
| → Deployed to Testing | 29 (Patch does this during batch promotion) |
| → Verified in Testing | 5 (human does this after verifying) |
| → Hotfix | 27 |
| → Deployed to Production | 31 (Chris does this — only path, "Done" transition) |
| → New | 11 |
| → In Planning | 23 |

### Jira Status IDs
| Status | ID |
|---|---|
| New | 10000 |
| Plan | 10072 |
| In Planning | 10140 |
| Plan Review | 10073 |
| Ready for Development | 10004 |
| In Development | 10001 |
| Code Review | 10106 |
| Deploy to development | 10019 |
| Deployed to Development | 10176 |
| Verified in Development | 10139 |
| Deployed to Testing | 10177 |
| Verified in Testing | 10142 |
| Ready for Production | 10018 | ⚠️ Ghost status — removed from board, do NOT use |
| Deployed to Production | 10002 |
| Hotfix | 10143 |
| Blocked | 10005 |

### Communication Channels
| Channel | Platform | ID | Use |
|---|---|---|---|
| #general | Discord (The Agency) | 1478849414629032154 | Cross-agent coordination |
| #general-engineering | Slack | C06TRR7A894 | Human PR review requests, blocked tickets, deploy pings, deploy confirmations |
| #general-engineering-qa | Slack | C0ALJS0M2NR | Plan summaries, QA findings |
| #alerts-platform-failure-development | Slack | C08V6MV0VNV | Dev error alerts |
| #alerts-platform-failure-testing | Slack | C08UWMQJFBN | Testing error alerts |
| #alerts-platform-failure-production | Slack | C08UVJDJZTL | Production error alerts |

### Jira Custom Fields
| Field | ID | Values |
|---|---|---|
| Risk | customfield_10038 | 10024=No, 10025=Low, 10026=Medium, 10027=High |
| Intensity | customfield_10039 | 10028=No, 10029=Low, 10030=Medium, 10031=High |
| Story Points | customfield_10016 | number |
| Velocity Impact | customfield_10064 | 10041=Neutral, 10042=Weak Positive, 10043=Strong Positive, 10044=Negative |
| Business Value | customfield_10065 | 10045=High, 10046=Medium, 10047=Low, 10048=None |
| Calculated Priority | customfield_10066 | number |

### Estimation Quick Reference

**Story Points: Risk × Intensity**
|  | High Risk | Medium Risk | Low Risk | No Risk |
|--|-----------|-------------|----------|---------|
| **High Intensity** | 21 | 13 | 8 | 5 |
| **Medium Intensity** | 13 | 8 | 5 | 3 |
| **Low Intensity** | 8 | 5 | 3 | 2 |
| **No Intensity** | 5 | 3 | 2 | 1 |

**Priority: Business Value × Velocity Impact**
|  | Strong Positive | Weak Positive | Neutral | Negative |
|--|-----------------|---------------|---------|----------|
| **High** | 21 | 13 | 8 | 5 |
| **Medium** | 13 | 8 | 5 | 3 |
| **Low** | 8 | 5 | 3 | 2 |
| **None** | 5 | 3 | 2 | 1 |

**Rule: Nothing > 5 SP goes to In Development without a breakdown plan.**
