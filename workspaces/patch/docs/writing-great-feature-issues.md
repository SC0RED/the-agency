# Writing Great Feature (Story) Issues

Type-specific guidance for Stories — user-facing features. Read alongside `writing-great-issues-base.md` for the universal rules. This doc specializes the six questions for feature work.

Stories carry user-facing intent. The planning emphasis is on requirements clarity and architectural fit, not on root-cause investigation.

---

## The Six Questions — Feature Specialization

### 1. What problem are we solving?

State the user need. What can't they do today that they should be able to? What workflow is painful or missing?

- **Good:** *"Users need to filter the target list by whether companies have contacts, so they can focus outreach on reachable companies."*
- **Bad:** *"Add contacts filter"*

Include screenshots of the current state — the before picture. If relevant, sketch or describe the intended end state.

### 2. What does done look like?

What's the user experience when this ships? Be specific about behavior, not just UI elements.

- **Good:** *"Toggle filter in toolbar. When active, only rows with ≥1 contact appear. Filter persists across pagination. Count in badge reflects filtered total."*
- **Bad:** *"Add a toggle for contacts"*

If the expected behavior is ambiguous or undefined, say so — that's a product question, not an engineering question. Don't invent acceptance criteria the user didn't agree to.

### 3. What's the current state?

Describe the current user experience (or lack of one). What exists today? What adjacent features does this interact with? What does the user currently do as a workaround, if anything?

Grounds the implementation in reality. You can't build the right thing if you don't understand what's already there.

### 4. What's the technical landscape?

Map the existing architecture that this feature touches.

- Which components, services, and data flows are involved?
- What patterns does the codebase already use for similar features? (Follow them — don't invent.)
- Are there API changes needed? New endpoints? Schema changes?
- What's the data model — does it exist already, or does this feature need to create it?

### 5. What's the approach?

Plain English:

- Which files change (and which are new)
- What the change does conceptually
- What the change does NOT do (scope boundaries)
- **Smallest shippable increment.** Can this feature be broken into phases? Shipping 80% of a feature in one PR is usually worse than shipping two focused PRs. Name the phases.
- Estimated size (SP, files touched)

### 6. What's the test plan?

For a Story, tests verify the **user-facing behavior** in the "Done" section — not just the underlying functions. Integration tests for the user flow; unit tests for the new logic. Each named edge case gets its own test.

- **What you're testing:** User flow and acceptance criteria.
- **How you're testing it:** Integration test for the flow, unit tests for new logic.
- **Edge cases:** Empty state, max values, concurrent access, error conditions.
- **Regression scope:** Which existing tests need to run? Name them.

---

## Examples

### Bad Feature Issue

> **Title:** Add has_contacts filter
>
> **Description:** Need to filter by contacts on evaluate tab.

Filter where? What behavior? What happens to pagination? What's the API contract?

### Good Feature Issue

> **Title:** Has Contacts filter only applies to visible rows — move to backend
>
> **Problem:** Users want to filter their target list to companies that have contacts, so they can focus outreach. Current client-side filter only works on the visible page — companies with contacts on other pages are invisible.
>
> **Done:** Toggle in toolbar filters the full dataset server-side. Pagination reflects filtered total. Filter state persists across page navigation. Badge count updates to filtered total.
>
> **Current state:** No filter exists on Evaluate. Users manually scan rows looking for the contacts icon. On large lists (500+ companies), this is impractical.
>
> **Technical landscape:** Evaluate tab renders from `store.savedWebsites` (paginated). Backend endpoint `GET /target-lists/:id/companies` supports query params for pagination but not contacts filtering. Label filter was added recently via `label` query param — same pattern applies. MongoDB `contact_enrichments` collection links to companies via `target_list_id`. Two repos: frontend (toolbar toggle + query param) and backend (query param handling + aggregation pipeline).
>
> **Approach:** Follow the label filter pattern. Frontend: add toggle to toolbar, pass `has_contacts=true` query param when active. Backend: when param present, join against `contact_enrichments` to filter. 2 SP. Two repos, ~4 files total.
>
> **Test plan:** Backend — integration test: seed 10 companies, 5 with contacts. Request with `has_contacts=true`, assert 5 returned. Request without param, assert 10. Frontend — unit test: toggle filter, verify query param included in next API call. Edge cases: list with 0 contacts (empty state), toggle on/off across pagination.
>
> **Architectural Review:**
> - Root cause depth: N/A (feature, not bug). The structural gap is that filtering is client-side for a server-paginated dataset — the architecture doesn't support what the user needs.
> - Design patterns: The existing label filter established a Query Parameter → Aggregation Pipeline pattern for server-side filtering. Following it, not inventing a new one.
> - Divergent implementations: Searched — only the label filter exists. Following the same pattern ensures one approach to server-side filtering.
> - Fix vs. design: This IS the right design. Server-side filtering for paginated data.
> - Untouched: Discover tab (contacts aren't relevant to search results). Contact enrichment service (read-only consumer).
>
> **Efficiency Review:**
> - Concurrency: Single aggregation pipeline — MongoDB handles internal parallelism.
> - Data flow: `$lookup` against `contact_enrichments` adds one pipeline stage. Indexed on `target_list_id` — verify index exists or add it.
> - N+1: No — single aggregation, not per-row lookup.
> - Caching: N/A — filter state is transient (toolbar toggle).
>
> **Structural Quality:**
> - No god-file contribution — toolbar toggle is a small addition. Backend change is in the existing query builder.
> - No missing abstraction — following existing query-param pattern.
> - No implicit coupling — filter state lives in the toolbar component and is passed as a query param.
