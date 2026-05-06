# Writing Great Bug Issues

Type-specific guidance for bugs. Read alongside `writing-great-issues-base.md` — the base doc has the Reader Contract, Title Rules, Comment Opening Rules, and the review lenses (architectural / efficiency / structural quality). This doc specializes the six questions for bug work.

---

## The Six Questions — Bug Specialization

### 1. What problem are we solving?

State the symptom in user terms. What did someone see, click, or experience that shouldn't have happened?

- **Good:** *"Selecting companies across multiple pages on Discover tab — badge count drops to 0 when navigating to page 2"*
- **Bad:** *"Selection count bug"*

Include screenshots or screen recordings when the current state is visual.

### 2. What does done look like?

What should the user see instead of the broken behavior?

- **Good:** *"Badge shows total selected count across all pages (e.g., 5 selected across 3 pages = badge shows 5)"*
- **Bad:** *"It should work correctly"*

### 3. What's the current state?

Step-by-step reproduction. Environment, data conditions, exact clicks. If it's intermittent, say so and describe what you've tried. For bugs that depend on data state (pagination, cache, specific records), include the query or record IDs that trigger it.

### 4. What's the technical landscape?

Trace the symptom to the code.

- Which file(s) and method(s) are involved?
- What is the code doing, and what should it be doing instead?
- When was the behavior introduced? (Commit hash if known)
- What evidence confirms the root cause? (Log output, query results, reproduction with specific data)

### 5. What's the approach?

Plain English:

- Which files change (and which are new)
- What the change does conceptually
- What the change does NOT do (scope boundaries)
- Estimated size (SP, files touched)

### 6. What's the test plan?

Every fix ships with tests. No exceptions. For a bug, the regression test that fails *because of this bug* is the most important artifact — write it before the fix, watch it fail, implement the fix, watch it pass.

Describe:

- **What you're testing:** The specific behavior. *"Selecting 3 companies on page 1, navigating to page 2, badge still shows 3."* Not *"it works."*
- **How you're testing it:** Unit / integration / manual — and why that level is appropriate.
- **Edge cases:** Empty state, max values, concurrent access, error conditions.
- **Regression scope:** What existing tests need to run? Name them.

---

## Examples

### Bad Bug Issue

> **Title:** Fix selection count
>
> **Description:** The count is wrong on Discover. Should show right number.

Tells engineering nothing. What count? Wrong how? Right number according to what rule?

### Good Bug Issue

> **Title:** Multi-select across pages loses selected count on Discover tab
>
> **Problem:** Selecting 3 companies on page 1, then navigating to page 2, the selection badge shows 0 instead of 3. Selecting 2 more on page 2 shows 2 instead of 5.
>
> **Done:** Badge shows cumulative count across all pages (5 in this case).
>
> **Current state:** Open any target list → Discover tab → select companies → click Next Page → observe badge count reset.
>
> **Technical landscape:** `getTabSelectedCompanies()` in `discover-tab.component.ts` (line ~878) filters the selection Map against `store.searchResults`, which only contains the current page. Cross-page selections are valid but invisible to this filter. Introduced in commit `bcc7021b` (March 8, 2026) as part of a performance optimization.
>
> **Approach:** Use `store.selectedCompanyCount` (raw Map size) for badge display. On Discover, every selection is a search result by definition — you can't select something that isn't rendered. The filter was solving a nonexistent problem.
>
> **Test plan:** Unit test — set selection Map to 5 entries, set searchResults to 2 entries (subset), assert badge shows 5. Edge cases: empty selection, single page (no pagination), selection then deselection. Regression: run existing discover-tab spec suite.
>
> **Architectural Review:**
> - Root cause depth: Symptom — badge shows 0. Cause — `getTabSelectedCompanies()` filters against current-page results only. Structural deficiency — no single source of truth for selection count; each tab computes its own via different logic.
> - Divergent implementations: Evaluate tab has `getVisibleSelected()` which filters against `savedWebsites` (correct for its context — scopes to saved companies). Discover's `getTabSelectedCompanies()` is the divergent path. Searched `grep -r "selectedCompan" --include="*.ts"` and `grep -r "getSelected|getVisible" --include="*.ts"`. Fix removes the unnecessary filter on Discover.
> - Fix vs. design: Fix IS the right design — raw count is the correct semantic for Discover selections.
> - Untouched: `evaluate-tab.component.ts` — its filter is correct (scopes to saved companies). `store-selection.ts` — raw count already correct, bug is in the consumer.
>
> **Efficiency Review:**
> - Data flow: Currently filtering a Map against an array on every render. Fix removes the filter entirely — O(1) `Map.size` instead of O(n) filter.
>
> **Structural Quality:**
> - Divergent logic identified and resolved in this fix. No god-file contribution (removing code, not adding). No implicit coupling introduced.
