# Writing Great Feature (Story) Issues

Feature-specific specialization of the canonical sections in `writing-great-issues-base.md`. Read that first.

Stories carry user-facing intent. The planning emphasis is requirements clarity and architectural fit, not root-cause investigation. The body / plan comment uses these sections in this order. Sections marked *(conditional)* appear only when applicable.

1. **Estimation** — Risk / Intensity / SP / Velocity Impact, top of the body.
2. **Job to be Done** — *When [context], the user wants to [motivation], so they can [outcome].* Names the actor and the desired outcome, not the implementation. Include before/after screenshots or sketches when relevant.
3. **Scope** — what's in, what's explicitly out. Be specific about boundaries — adjacent features that are NOT being touched, edge cases that are NOT being handled in this iteration.
4. **Current State** — what exists today, what workaround the user uses, which adjacent features this interacts with. Grounds the implementation in reality.
5. **Approach** — the design in plain English: which files change, which are new, what existing pattern is being followed (with a path to the precedent), what the smallest shippable increment is. Include *Alternatives Considered* — name the rejected design alternatives and why. Reuse check is not optional.
6. **Acceptance Criteria** — Given/When/Then. Each criterion is testable and traces back to the Job to be Done.
7. **Definition of Done** — coverage expectations: integration test for the user flow, unit tests for new logic, named edge cases each get their own test.
8. **Production Signal** — how we'll know it's working post-deploy: the metric, telemetry event, or observation. Distinct from acceptance criteria, which only proves correctness in test. *"Time-to-first-result drops below 2s on the dashboard panel"* is a production signal; *"the unit test passes"* is not.
9. **Rollback** *(conditional)* — only when the change is irreversible (schema migration, data shape change, infra mutation). `git revert` is not a rollback section.

---

## Worked Example

> **Title:** Add Has Contacts filter to Evaluate toolbar
>
> **Estimation:** Risk: Low · Intensity: Medium · SP: 5 · Velocity Impact: Weak Positive
>
> **Job to be Done:** *When evaluating a target list of 500+ companies, the user wants to filter to companies that have contacts, so they can focus outreach on reachable companies.*
>
> **Scope:** In — toggle in the Evaluate tab toolbar; backend query parameter `has_contacts`; pagination reflects filtered total; filter persists across page navigation. Out — Discover tab (contacts not relevant there); persisting filter state across sessions; combining with the existing label filter (independent toggles, unioned).
>
> **Current State:** No filter exists on Evaluate. Users manually scan rows looking for the contacts icon. On lists of 500+ companies, this is impractical and breaks across pagination boundaries.
>
> **Approach:** Follow the label-filter pattern at `Platform-Frontend/src/app/.../evaluate-tab.component.ts:412` and `Platform-Backend/handlers/target-lists/get-companies.js:88`. Frontend: add toggle to toolbar, pass `has_contacts=true` query param when active. Backend: when param present, `$lookup` against `contact_enrichments` (indexed on `target_list_id`) and filter to companies with at least one match. ~4 files across the two repos. *Alternatives Considered:* Considered client-side filtering for simpler implementation — rejected because pagination would break (current page might have 0 matches while later pages have matches). Considered a denormalized `has_contacts` boolean on the company doc — rejected because contacts are added asynchronously and the boolean would lag.
>
> **Acceptance Criteria:**
> - *Given* a target list of 10 companies, 5 with contacts, *when* the user toggles "Has Contacts" on, *then* only the 5 with contacts appear and the badge shows 5.
> - *Given* the toggle is on and the user navigates to page 2, *when* page 2 renders, *then* it shows the next page of contacts-only results and the toggle remains on.
> - *Given* the toggle is on, *when* the user toggles it off, *then* all companies reappear and the badge shows 10.
>
> **Definition of Done:** Backend integration test seeding 10 companies (5 with contacts), asserting filtered and unfiltered queries return the right counts. Frontend unit test asserting query param is included when toggle is on. End-to-end verification on dev. Pagination edge case (toggle on with 0 matches in current page range) covered.
>
> **Production Signal:** Toggle usage event recorded in product analytics (`evaluate_filter_toggled` with `filter=has_contacts`). Look at week-over-week usage 7 days post-deploy.
