# Writing Great Task Issues

Task-specific specialization of the canonical sections in `writing-great-issues-base.md`. Read that first.

Tasks are technical work that isn't a user-facing feature and isn't a bug — refactors, infrastructure, devex, debt cleanup, dependency upgrades, perf work without a specific user-reported symptom. The motivating force is engineering, not product. The body / plan comment uses these sections in this order.

1. **Estimation** — Risk / Intensity / SP / Velocity Impact, top of the body.
2. **Motivating Cost** — what cost is this paying down, or what capability is it unlocking? Specific. *"This file has 8 active bugs traced to its 600-line god-method"* is a reason. *"It's old"* is not. Tasks tempt vague framing — push for a concrete cost.
3. **Scope** — what's in, what's explicitly out. Tasks attract scope creep more than any other issue type. Every "while I was in here" idea is either explicitly excluded or filed as a follow-up.
4. **Current State** — the existing shape, honestly described. For refactors, show the divergence being collapsed (with file paths). For dependency upgrades, the current version + any deprecated APIs in use. For infra work, what's broken or missing today.
5. **Approach** — the design in plain English: files added, modified, *deleted*. Sequence — which steps must be ordered. For refactors, a 2-sentence before/after sketch. For perf work, the measurable improvement (ms → ms, QPS → QPS). Include *Alternatives Considered* — name rejected alternatives, especially "do nothing" or "smaller scope" if those were considered.
6. **Acceptance Criteria** — observable end state, deterministically verifiable. *"`grep -r 'attemptCount\|backoffMs' --include='*.ts'` returns hits only in `lib/retry.ts` and its tests"* is a criterion. *"Retry logic is consolidated"* is not.
7. **Definition of Done** — coverage expectations specific to the task type:
   - Refactor: existing tests pass unchanged; new tests fill gaps the refactor exposed.
   - Performance fix: benchmark or test asserting the improvement.
   - Infra / devex: end-to-end verification on the branch before push, documented in the PR.
   - Dependency upgrade: full local validation suite plus targeted manual checks for deprecated API usage.
8. **Production Signal** *(conditional — perf and infra tasks)* — the metric or observation that confirms the task delivered the cost reduction it promised. CloudWatch metric, log volume change, build-time dashboard, etc.
9. **Rollback** *(conditional)* — only when the change is irreversible (schema migration, infra mutation, dependency upgrade with non-trivial revert path). `git revert` is not a rollback section.

---

## Worked Example

> **Estimation:** Risk: Low · Intensity: Low · SP: 2 · Velocity Impact: Weak Positive
>
> **Motivating Cost:** CSV upload progress bar stalls at ~90% for 30–60 seconds on 500-row uploads. Users think the upload failed and retry, causing duplicates. Confirmed via 6 support tickets in the last quarter and CloudWatch traces showing T+45s last-row completion vs. T+102s `batch_end` completion.
>
> **Scope:** In — `completed_count` update timing in the SQS worker, frontend "Finalizing…" UI state for the post-`batch_end` window. Out — full Observer-pattern refactor of progress tracking (filed as SPE-XXXX); changes to other async progress flows (scorecard, single-company operations).
>
> **Current State:** Frontend polls `GET /requests/:id` for `completed_count / url_count`. Backend updates `completed_count` only after `batch_end` processing finishes (deduplication, rollup), which adds 30–60s on 500+ row batches. CloudWatch trace `req-7f3a2`: SQS workers complete at T+45s, `batch_end` completes at T+102s, count jumps from 450 to 500 at T+102s.
>
> **Approach:** Update `completed_count` in the SQS worker on each row completion (atomic `$inc`), BEFORE `batch_end` processing. Frontend progress reaches 100% when all rows are processed; a brief "Finalizing…" state covers the `batch_end` phase. ~2 files (`assessment_engine/parts_factories/batch_factory.py`, `Platform-Frontend/src/app/.../upload-progress.component.ts`). *Alternatives Considered:* Full Observer-pattern refactor decoupling progress tracking from the processing pipeline. Rejected for this ticket — ~5 SP, crosses backend + engine, affects the SQS worker contract. Filed as a follow-up; current fix moves in the right direction without rework.
>
> **Acceptance Criteria:**
> - *Given* a 500-row CSV upload, *when* the last SQS worker completes, *then* `completed_count` equals `url_count`.
> - *Given* `completed_count == url_count` but `status != success`, *when* the frontend renders, *then* the "Finalizing…" state is shown.
> - *Given* `batch_end` completes, *when* the frontend renders, *then* the success state replaces "Finalizing…".
>
> **Definition of Done:** Engine integration test processing a 10-row batch and asserting `completed_count == 10` before `batch_end` completes. Frontend unit test for the "Finalizing…" state transition. Manual e2e on dev with a 500-row CSV.
>
> **Production Signal:** Median time from "100% progress" to "success" state in the upload completion CloudWatch metric should drop from ~60s to ~5s post-deploy. Check 7 days after deploy.
