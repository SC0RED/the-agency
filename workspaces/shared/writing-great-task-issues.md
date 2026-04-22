# Writing Great Task Issues

Type-specific guidance for Tasks — technical work that isn't a user-facing feature and isn't a bug. Read alongside `writing-great-issues-base.md` for the universal rules. This doc specializes the six questions for task work.

Tasks are: refactors, infrastructure changes, devex work, debt cleanup, dependency upgrades, performance work without a specific user-reported symptom. The shape is similar to a Story, but the motivating force is engineering-driven rather than user-driven.

---

## The Six Questions — Task Specialization

### 1. What problem are we solving?

State the engineering motivation. What cost is this paying? What capability is this unlocking?

- **Good:** *"The SQS retry logic in three different workers has drifted to three different retry policies. New engineers get confused about which is 'correct.' Consolidate into one shared helper."*
- **Bad:** *"Clean up retry logic"*

Tasks *tempt* vague framing — *"refactor X"*, *"improve Y"*. Push for specific cost or specific capability. Without that, the task shouldn't exist.

### 2. What does done look like?

Observable end state. What can the next engineer look at and confirm this is finished?

- **Good:** *"All three workers call `withBackoffRetry()` from `lib/retry.ts`. Individual retry-policy code is deleted. `grep -r 'attemptCount\|backoffMs' --include='*.ts'` returns hits only in the shared helper and its tests."*
- **Bad:** *"Retry logic is consolidated"*

For refactors, the definition of done must include: what's deleted, what's left, and how to verify nothing else changed.

### 3. What's the current state?

Describe the existing shape honestly. For refactors, show the divergence you're collapsing. For dependency upgrades, state the current version + any deprecated API usage that motivated the upgrade. For infra work, state what's broken or missing today.

### 4. What's the technical landscape?

Map what this touches.

- Which repos and files are affected?
- What patterns does the codebase already use? (Follow them — tasks especially tempt premature new abstractions.)
- Are there cross-repo contracts affected? If yes, list them and order the changes.
- Is there a migration window, a feature flag, or a dual-write phase?

### 5. What's the approach?

Plain English:

- Which files change (and which are new / deleted)
- **What the change does NOT do.** Tasks attract scope creep more than any other issue type — every "while I was in here" idea must be explicitly excluded or filed as a follow-up.
- For refactors: a "before vs. after" sketch (2 sentences of each).
- For perf work: the measurable improvement (ms → ms, QPS → QPS).
- For infra work: the rollback path.
- Estimated size (SP, files touched).

### 6. What's the test plan?

Right test scope depends on what kind of Task this is:

- **Refactor:** existing tests must still pass unchanged. Write *new* tests where the old tests had gaps the refactor exposed.
- **Performance / N+1 fix:** benchmark or test asserting the fix (*"no more than 1 query per page load"*).
- **Infra / devex / build:** verify the change end-to-end on this branch before pushing. Document the verification in the PR description.
- **Dependency upgrade:** full local validation suite + targeted manual checks for any deprecated API usage.

If the Task is genuinely untestable in any meaningful sense, say so explicitly in the PR description. *"Too hard to test"* is never the reason — it means the code needs restructuring first.

---

## Example — Task with Fix ≠ Design

> **Title:** CSV upload progress bar stalls at 90% for large files
>
> **Problem:** Uploading a 500-row CSV, the progress bar reaches ~90% and stalls for 30-60 seconds before jumping to 100%. Users think the upload has failed and retry, causing duplicates.
>
> **Done:** Progress bar advances smoothly through the full upload. No stall period.
>
> **Current state:** Upload CSV with 500+ rows → observe progress stall at ~90% → eventually completes.
>
> **Technical landscape:** Frontend polls `GET /requests/:id` for `completed_count / url_count`. Backend: `completed_count` is updated by SQS workers per-row, but `batch_end` processing (deduplication, rollup) blocks the final count update for 30-60s on large batches. CloudWatch confirms: last SQS worker completes at T+45s, `batch_end` completes at T+102s, `completed_count` jumps from 450 to 500 at T+102s.
>
> **Approach (fix):** Update `completed_count` in the SQS worker BEFORE `batch_end` processing — the count reflects completed work, not post-processing. Frontend progress will reach 100% when all rows are processed, and a brief "Finalizing..." state covers the `batch_end` phase. 2 SP.
>
> **Test plan:** Integration test — process 10-row batch, verify `completed_count` reaches 10 before `batch_end` completes. Unit test — SQS worker updates count on completion, not on batch_end. Frontend — verify *"Finalizing..."* state appears when count = total but status ≠ success.
>
> **Architectural Review:**
> - Root cause depth: Symptom — progress stalls at 90%. Cause — `completed_count` only updates after `batch_end`. Structural deficiency — progress tracking is coupled to post-processing; these are separate concerns sharing a single counter.
> - Design patterns: The batch pipeline is an implicit Pipeline/Chain but *progress* is tangled into *processing*. The right design would separate progress tracking via an Observer on per-row completion. Current fix decouples count update from batch_end without the full Observer refactor.
> - Fix vs. design: **They differ.** Fix: move count update to SQS worker, add "Finalizing" UI state. Right design: Observer pattern on row completion, with progress as a subscriber fully decoupled from the processing pipeline. Right design is ~5 SP across backend + engine and affects the SQS worker contract. Filing SPE-XXX for the structural fix. Current fix is acceptable because: (a) it resolves the user-facing stall, (b) it moves in the right direction (decoupling count from batch_end), (c) the Observer refactor can be layered on top without rework.
> - Divergent implementations: Other progress tracking (scorecard, single-company operations) use direct status field polling, not count-based. No divergence.
> - Untouched: `batch_end` handler (its logic is correct; the bug is WHEN it updates the count, not WHAT it does). Frontend polling (it already handles count/total correctly; it just needs the "Finalizing" state addition).
>
> **Efficiency Review:**
> - Concurrency: SQS workers already process in parallel. Count update is an atomic `$inc` — safe under concurrency, no locking needed.
> - Data flow: Adding one `$inc` per worker completion. Already happening for other fields — marginal cost.
>
> **Structural Quality:**
> - Progress tracking coupled to post-processing identified as a structural issue. Follow-up ticket SPE-XXX filed for Observer-based decoupling. Current fix reduces coupling without full refactor.
