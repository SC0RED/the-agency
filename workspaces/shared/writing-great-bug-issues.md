# Writing Great Bug Issues

Bug-specific specialization of the canonical sections in `writing-great-issues-base.md`. Read that first — it has the audience, title rules, comment opening rules, and the universal section spine.

The bug body / plan comment uses these sections in this order. Sections marked *(conditional)* appear only when applicable; everything else is required.

1. **Estimation** — Risk / Intensity / SP / Velocity Impact, top of the body.
2. **Symptom** — what the user saw, one paragraph in user terms. Screenshots or recordings when current state is visual.
3. **Reproduction** — exact steps, environment, data conditions, how it was detected (user report, monitor, test). For data-dependent bugs, include the query or record IDs that trigger it. Intermittent? Say so and describe what's been tried.
4. **Diagnosis** — root cause traced to file and line, with the evidence that confirmed it. Name the symptom, the cause (what the code does wrong), and the structural deficiency (why the code was written that way). When there's no structural deficiency — *"Logic error in an otherwise sound design — no structural change."* — say so plainly. When introduced (commit hash if known) goes here too.
5. **Approach** — the fix in plain English: which files change, which are new, and what does NOT change (scope boundaries). Include *Alternatives Considered* — name the existing pattern with a path, or state plainly that none applies and why. Reuse check is not optional.
6. **Acceptance Criteria** — Given/When/Then. Each criterion is a test that fails today and passes after the fix.
7. **Definition of Done** — coverage expectations and the regression test that would have caught this bug. The regression test is the most important artifact a bug ships — write it before the fix, watch it fail, implement the fix, watch it pass.
8. **Rollback** *(conditional)* — only when the change is irreversible. `git revert` is not a rollback section.

---

## Worked Example

> **Estimation:** Risk: Low · Intensity: Low · SP: 3 · Velocity Impact: Weak Positive
>
> **Symptom:** Selecting 3 companies on Discover tab page 1, navigating to page 2, the selection badge shows 0 instead of 3. Selecting 2 more on page 2 shows 2 instead of 5.
>
> **Reproduction:** Detected via internal use during testing.sc0red.ai walkthrough. Open any target list → Discover tab → select companies → click Next Page → observe badge count reset. Reproduces on dev, test, prod. No data dependencies — happens on any list with >1 page of results.
>
> **Diagnosis:** `getTabSelectedCompanies()` in `discover-tab.component.ts:878` filters the selection `Map` against `store.searchResults`, which contains only the current page. Cross-page selections are valid but invisible to this filter. Verified by logging Map size (5) vs. filter output (2) at the badge render site. Introduced in commit `bcc7021b` (March 8, 2026) as part of a perf optimization. Cause: filter applied where none was needed. Structural deficiency: each tab computes its own selection-count semantics — no single source of truth.
>
> **Approach:** Use `store.selectedCompanyCount` (raw `Map.size`) for badge display on Discover. On Discover, every selection is a search result by definition — the filter was solving a nonexistent problem. *Alternatives Considered:* Evaluate tab uses `getVisibleSelected()` which filters against `savedWebsites` (correct for its context — scoped to saved companies). Considered using the same shape on Discover; rejected because the semantics differ.
>
> **Acceptance Criteria:**
> - *Given* 5 companies are selected across 3 pages, *when* the badge renders, *then* it shows 5.
> - *Given* 0 companies are selected, *when* the badge renders, *then* it shows 0 (no badge).
> - *Given* 5 companies are selected and the user deselects 2, *when* the badge re-renders, *then* it shows 3.
>
> **Definition of Done:** Unit test in `discover-tab.component.spec.ts` setting selection Map to 5 entries and `searchResults` to a 2-entry subset, asserting badge shows 5. Existing `discover-tab.spec` suite passes. Manual verification on dev with multi-page data.
