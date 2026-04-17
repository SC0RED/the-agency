# Writing Great Jira Issues

A Jira issue is a contract between the person who found the problem and the person who fixes it. A great issue makes the fix obvious. A bad issue makes the engineer guess — and guessing is where hacks come from.

This protocol applies to every issue in the SPE project, whether filed by a human or an agent.

---

## Complexity Tiers

Not every issue needs the same ceremony. The reviews in this document scale by story points:

| Tier | Story Points | What's Required |
|------|-------------|-----------------|
| **Trivial** | 1 SP | The Standard (5 questions), abbreviated Architectural Review (Fix vs. Design + Untouched only), Test Plan, AI Anti-Pattern Self-Check |
| **Standard** | 2–5 SP | Everything in this document |
| **Complex** | 8+ SP | Everything in this document, plus mandatory breakdown into sub-tasks before planning begins |

**How to judge:** If filling out a section produces no insight (e.g., "Concurrency: N/A — changing a string"), skip it and note "N/A — [one-line reason]." The point is to catch real problems, not generate paperwork. But "N/A" is an answer you give after considering the question — not a way to avoid considering it.

---

## The Standard

Every issue should answer six questions. If it can't answer all six, it's not ready for engineering.

### 1. What problem are we solving?

**Bugs:** State the symptom in user terms. What did someone see, click, or experience that shouldn't have happened?

- **Good:** "Selecting companies across multiple pages on Discover tab — badge count drops to 0 when navigating to page 2"
- **Bad:** "Selection count bug"

**Features:** State the user need. What can't they do today that they should be able to? What workflow is painful or missing?

- **Good:** "Users need to filter the target list by whether companies have contacts, so they can focus outreach on reachable companies"
- **Bad:** "Add contacts filter"

Include screenshots or screen recordings when the current state is visual. Show what exists today — the before picture.

### 2. What does done look like?

State the expected outcome explicitly. Don't assume the reader knows.

**Bugs:** What should the user see instead of the broken behavior?
- **Good:** "Badge shows total selected count across all pages (e.g., 5 selected across 3 pages = badge shows 5)"
- **Bad:** "It should work correctly"

**Features:** What's the user experience when this ships? Be specific about behavior, not just UI elements.
- **Good:** "Toggle filter in toolbar. When active, only rows with ≥1 contact appear. Filter persists across pagination. Count in badge reflects filtered total."
- **Bad:** "Add a toggle for contacts"

If the expected behavior is ambiguous or undefined, say so — that's a product question, not an engineering question.

### 3. What's the current state?

**Bugs:** Step-by-step reproduction. Environment, data conditions, exact clicks. If it's intermittent, say so and describe what you've tried. For bugs that depend on data state (pagination, cache, specific records), include the query or record IDs that trigger it.

**Features:** Describe the current user experience (or lack of one). What exists today? What adjacent features does this interact with? What does the user currently do as a workaround, if anything?

This grounds the implementation in reality. You can't build the right thing if you don't understand what's already there.

### 4. What's the technical landscape?

This is the engineering section. Map the territory before proposing changes.

**Evidence before theory.** Follow this investigation order — do not skip ahead to reading code:

1. **Logs and errors first.** CloudWatch, application logs, browser console, error output. What does the system say happened?
2. **Data second.** Database queries, API responses, request payloads. What does the data look like when the bug manifests?
3. **Code third.** Now that you know what happened and what the data looks like, read the code to understand why.
4. **Hypothesis last.** Form your diagnosis from the evidence. If the evidence doesn't support the diagnosis, the diagnosis is wrong — not the evidence.

**Bugs:** Trace the symptom to the code.
- Which file(s) and method(s) are involved?
- What is the code doing, and what should it be doing instead?
- When was the behavior introduced? (commit hash if known)
- What evidence confirms the root cause? (log output, query results, reproduction with specific data)

**Features:** Map the existing architecture that this feature touches.
- Which components, services, and data flows are involved?
- What patterns does the codebase already use for similar features? (Follow them.)
- Are there API changes needed? New endpoints? Schema changes?
- What's the data model — does it exist already or need to be created?

**If you don't know yet, say so.** "Technical landscape: under investigation" is honest. A wrong map is worse than no map. See [Investigation-In-Progress Plans](#investigation-in-progress-plans) for how to handle incomplete investigation.

### 5. What's the approach?

Plain English, not code. Describe the implementation:
- Which files change (and which are new)
- What the change does conceptually
- What the change does NOT do (scope boundaries)
- Estimated size (story points, files touched)
- For features: what's the smallest shippable increment? Can this be broken into phases?

### 6. What's the test plan?

Every fix ships with tests. No exceptions. Describe:

- **What you're testing:** The specific behavior, not "it works." "Selecting 3 companies on page 1, navigating to page 2, badge still shows 3."
- **How you're testing it:** Unit test, integration test, manual verification — and why that level is appropriate.
- **Edge cases:** What boundary conditions does this fix need to handle? Empty state, max values, concurrent access, error conditions.
- **Regression scope:** What existing tests need to run to confirm nothing broke? Name them.

If the fix is truly untestable (pure infrastructure, deployment config), say why. "Too hard to test" is never a valid reason — it means the code needs to be restructured for testability, which is part of the fix.

---

## Architectural Review (Mandatory for Standard and Complex Tiers)

Before proposing a fix, answer these questions. Include the answers in your plan comment under an **## Architectural Review** heading. This is where you prove you understand the problem deeply enough to solve it correctly.

For **Trivial** tier (1 SP): only Fix vs. Design and What Stays Untouched are required.

### Root Cause Depth

Don't accept the symptom as the problem. A bug has a symptom, a cause, and often a structural deficiency that allowed the cause to exist. Name all three.

- **Symptom:** What the user sees (badge shows 0)
- **Cause:** What the code does wrong (filters against current page only)
- **Structural deficiency:** Why the code was written this way (no single source of truth for selection count — each tab computes its own)

If your fix addresses only the symptom, you're patching. If it addresses the cause, you're fixing. If it addresses the structural deficiency, you're engineering. Know which one you're doing and why.

**When there's no structural deficiency:** Sometimes a bug is a genuine logic error — an off-by-one, a wrong comparison, a typo. If you investigate and honestly find no structural problem, say so: "Structural deficiency: none — this is a logic error in an otherwise sound design." Don't manufacture structural problems to satisfy a checklist.

### Design Pattern Analysis

Think in design patterns — Strategy, Observer, State, Builder, Chain of Responsibility, Factory, and the rest of the Gang of Four catalog. Code doesn't just have bugs — it has *accidental patterns*. A class that's grown 15 boolean flags has accidentally become a State machine without the State pattern. A method with a giant switch statement is a Strategy pattern waiting to be extracted.

For every plan, answer:
- **What pattern does this code currently implement (intentionally or accidentally)?** Name it. If the code is a 400-line method with nested conditionals, that's an accidental Procedural Script — name it as such. If it's straightforward logic that doesn't map to any pattern, say "No pattern applies — this is straightforward [procedural logic / CRUD / data transformation / etc.]." That's a valid answer.
- **What pattern should it implement?** Only if the current structure is causing or enabling bugs. If the code is correct as-is, say "Current structure is appropriate." Don't propose a pattern just to have something to write here.
- **Is the pattern change in scope?** If yes, include it in the plan. If no, file a follow-up ticket with the structural case.

**What counts as a structural case:** "This file is too big" is not a case. "This class violates SRP by owning both cache management and build orchestration, and the missing State pattern caused a feedback loop between initialization states" is a case. Name the principle violated, name the pattern that fixes it, name the bugs it prevents.

### Divergent Implementation Search

Search the codebase for other code doing the same thing as the code you're about to change.

- Are there multiple methods/components that solve the same problem differently?
- If yes: your fix must address the divergence — not add another path.
- If no: show what you searched for. "No divergent implementations" without evidence is not an answer.

**Why this matters:** Two components computing the same value from different sources will eventually disagree. A fix that patches one without reconciling the other trades today's bug for tomorrow's.

### Fix vs. Design

State explicitly:
- "My fix does X."
- "The right design is Y."

If they're the same: great. If they differ: explain why the fix is acceptable and what the right design would cost. If the right design is within scope, propose it. If it's not, file a follow-up ticket.

**Why this matters:** Speed pressure makes engineers propose the first thing that works. This question forces a pause: is the thing that works also the thing that's right? Sometimes a workaround is justified (small scope, low risk, follow-up filed). But you have to name it as a workaround — not pretend it's the real fix.

### What Stays Untouched

List related code you're NOT changing and explain why for each:
- "Not changing `evaluate-tab.component.ts` because its `getVisibleSelected()` filters against the full saved set, which is correct for that tab's semantics."
- "Not changing `store-selection.ts` because the raw count is already correct; the bug is in the consumer."

If you can't justify leaving related code untouched, your scope is wrong.

**Why this matters:** Every fix has a blast radius. Being explicit about what you're not touching — and why — prevents scope creep in review and catches cases where the scope should actually be bigger.

---

## Efficiency Review (Mandatory for Standard and Complex Tiers)

You have unlimited time and compute. The human reviewing your work does not. Every minute you spend finding the right solution saves them hours debugging the wrong one. Never optimize for your own convenience — optimize for correctness, performance, and maintainability.

Before proposing an implementation, answer these questions. Include the answers in your plan under an **## Efficiency Review** heading. If a subsection doesn't apply (e.g., concurrency analysis for a CSS change), write "N/A — [reason]" and move on.

### Concurrency and Parallelism

Identify every operation in your implementation that could run concurrently.

- **I/O operations:** Are there multiple database queries, API calls, or file reads that don't depend on each other? Run them in parallel (`Promise.all`, `asyncio.gather`, concurrent subscriptions).
- **Batch operations:** Are you processing items in a loop where each iteration is independent? Use bulk/batch APIs instead of sequential calls. One `bulkWrite` beats N `updateOne`s. One `SELECT ... WHERE id IN (...)` beats N `SELECT ... WHERE id = ?`.
- **Pipeline stages:** Can parts of the data flow execute concurrently? Map the dependency graph — only sequential where data flows require it.

**Show your work:** "These 3 queries are independent — running in parallel via `Promise.all`." or "These must be sequential because query B uses the result of query A." If everything is sequential, justify why.

**Why this matters:** Sequential-by-default is the single most common performance mistake in AI-generated code. An AI that writes `await queryA(); await queryB(); await queryC();` when the three are independent has wasted 2/3 of the wall-clock time. The human will never notice this in code review — they'll just wonder why the feature is slow.

### Data Flow Efficiency

Trace the data from source to consumer. Look for waste.

- **Over-fetching:** Are you loading entire documents/collections when you need 2 fields? Use projections, `SELECT` specific columns, GraphQL field selection.
- **N+1 queries:** Are you querying inside a loop? Batch the lookup.
- **Redundant transformations:** Are you transforming the same data multiple times in the pipeline? Transform once, at the boundary.
- **Memory:** Are you loading an entire dataset into memory when you could stream, paginate, or use cursors?

### Algorithm and Data Structure Choice

State the time complexity of your core operations. If you're iterating a list to find an item, that's O(n) — should it be a Map lookup at O(1)? If you're sorting to find the max, that's O(n log n) — should it be a single-pass O(n) scan?

This isn't academic. A `.find()` inside a `.forEach()` is O(n²). On 50 items nobody notices. On 5,000 the UI freezes.

### Caching and Recomputation

- Is this value computed on every call but rarely changes? Cache it.
- Is this value cached but changes frequently? Don't cache it.
- If caching: what's the invalidation strategy? A cache without invalidation is a bug on a timer.

---

## Structural Quality Review (Mandatory for Standard and Complex Tiers)

Every bug is a question about structure. When investigating, audit the code you're touching for these patterns — they're the most common sources of repeat bugs and the highest-value refactoring targets.

Include findings under a **## Structural Quality Review** heading in your plan. If nothing is found, say "No structural issues identified in the code touched by this change." Don't leave the section out — its absence means you didn't look.

### God Files

Files over 300 lines, classes with 20+ methods, components that own state management AND rendering AND business logic.

**Detect:** If the file you're about to modify is already doing too much, adding more to it makes it worse. Your change is the trigger to fix this — not an excuse to pile on.

**Resolve:** Extract services, split components, apply Single Responsibility. A file should do one thing — if you need an "and" to describe it, it's doing too much.

### Missing Abstractions

Raw data manipulation scattered across consumers instead of encapsulated in a service or utility.

**Detect:** Business rules embedded in template expressions, the same conditional logic repeated in multiple places, multiple components doing the same transformation chain.

**Resolve:** Extract to a shared service or utility. The business rule lives in one place; consumers call it.

**Threshold for extraction:** It's not just about count — it's about complexity × frequency. Two instances of a 50-line data transformation are worse than four instances of `item.name.trim()`. Use judgment: if the duplication is trivial and unlikely to diverge, leave it. If it encodes a business rule that could change, extract it regardless of count.

### Implicit State Coupling

Components that depend on another component's internal state without an explicit contract.

**Detect:** State passed through 3+ levels of nesting, components reading from stores they don't own, breakage when changing "unrelated" components.

**Resolve:** Define explicit interfaces. If Component B needs data from Component A, that's a contract — type it, document it, test it.

### When to Propose Refactoring

Not every bug needs a refactoring PR. The threshold:

- **Always propose** when the bug was caused by one of the patterns above (the structure created the bug)
- **Propose as follow-up** when the pattern exists nearby but didn't directly cause this bug
- **Don't propose** when the code is clean and the bug is a genuine logic error

**One concern per PR — how to judge:** If the structural fix IS the bug fix (the refactor eliminates the bug), that's one concern — ship it together. If the structural fix is adjacent improvement ("while I was in here..."), it's a separate PR. The test: could someone revert the structural change without reintroducing the bug? If yes, they're separate concerns. If no, they're inseparable.

When proposing, document the structural case: which pattern/principle is violated, what the current structure is, what the improved structure would be, estimated scope, and what class of bugs it prevents. "This file is too big" is not a structural case. Name the principle, name the pattern, name the bugs.

---

## AI Anti-Patterns (Mandatory Reading)

These are the patterns that turn AI-generated code into slop. If you catch yourself doing any of these, stop and reconsider. This section exists because these patterns are invisible to AI — they feel like good engineering from the inside. They're not.

### "The Simplest Solution"

When an AI says "the simplest solution is," it almost always means "I'm about to hack my way through this instead of doing the right thing." Simplicity is a virtue in design — but "simple to implement right now" and "simple to maintain forever" are different things.

**The tell:** The proposed solution avoids touching the actual problem. It wraps, intercepts, special-cases, or adds a flag instead of fixing the root cause.

**Examples:**
- "The simplest solution is to add a null check here" — instead of figuring out why the value is null
- "The simplest solution is to add a setTimeout" — instead of understanding the lifecycle
- "The simplest solution is to copy this method and modify it" — instead of parameterizing the original
- "The simplest solution is to add a flag parameter" — instead of decomposing the function

**The rule:** Never propose "the simplest solution." Propose the *right* solution. If the right solution is also simple, great — but lead with *why it's right*, not why it's simple.

### Scope Shrinking

AI agents instinctively reduce scope to reduce risk. When a task is complex, the temptation is to solve 80% of it and call it done. This manifests as:

- Silently dropping edge cases ("this handles the main flow")
- Implementing the easy parts and deferring the hard parts to "follow-up"
- Choosing an approach that's easier to implement but worse for the user
- "For now, we can just..." — there is no "for now." There is only the code that ships.

**The rule:** Implement what was asked. All of it. If the scope genuinely should be smaller, say so explicitly with reasons — don't quietly shrink it.

### Defensive Spackle

Adding null checks, try/catch blocks, fallback values, and optional chaining to internal code paths instead of ensuring the data is correct at the source.

**Examples:**
- `value?.nested?.field ?? 'default'` — If this value should always exist, a silent fallback hides the bug that made it missing.
- `try { riskyThing() } catch (e) { /* silently continue */ }` — Now you'll never know it failed.
- `if (data && data.length > 0)` on data that is always an array — this isn't safety, it's doubt.

**The rule:** Internal code should trust internal contracts. Validate at system boundaries (user input, external APIs, database reads). Inside the system, if something is null that shouldn't be, that's a bug — surface it, don't paper over it.

### Premature Abstraction

Creating abstractions, utilities, factories, or configuration systems for things that exist in exactly one place.

**Examples:**
- Writing a `formatCompanyName()` utility used by one component
- Creating a configuration object for values that will never change
- Building a plugin system for a feature with one implementation
- Adding generic type parameters to a function called with one type

**The rule:** Wait until you understand the actual variation before designing for it. The threshold for extraction is complexity × frequency, not count alone — see [Missing Abstractions](#missing-abstractions).

### Pattern Blindness

The inverse of cargo-cult patterns. AI agents default to procedural code — long methods, nested conditionals, manual state tracking — when a named design pattern would solve the problem cleanly. This happens because patterns require recognizing the *shape* of a problem, and AI agents optimize for the *immediate* problem.

**Symptoms:**
- A method with a growing switch/case on a type field → should be Strategy
- A class with boolean flags controlling behavior branches → should be State
- A constructor with 8+ parameters, half optional → should be Builder
- Multiple listeners manually wired to a shared data source → should be Observer/Subject
- A chain of if/else handlers where each checks eligibility → should be Chain of Responsibility

**The rule:** Before writing a conditional that switches on type or state, ask: is there a Gang of Four pattern for this shape? If yes, use it. Patterns exist because they've been proven to prevent the exact class of bugs that procedural alternatives create. A Strategy pattern isn't overhead — it's insurance against the next developer adding case 17 to your switch statement.

### Cargo-Cult Patterns

The inverse of pattern blindness. Applying patterns, libraries, or architectural decisions because they're "best practice" rather than because the problem requires them.

**Examples:**
- Adding Redux/NgRx to manage state that lives in one component
- Creating an abstract base class for a single implementation
- Using a factory pattern when a constructor works fine
- Adding dependency injection for a pure utility function
- Wrapping a perfectly good library in an "adapter" for no reason

**The rule:** Every pattern has a cost (complexity, indirection, learning curve). Only introduce a pattern when the cost of *not* having it is higher. "Best practices" are contextual — a pattern that's essential in a 500-developer monolith is overhead in a 3-developer startup.

**How Pattern Blindness and Cargo-Cult coexist:** These are not contradictions. Pattern Blindness says "recognize when a pattern solves your problem." Cargo-Cult says "don't use a pattern that doesn't solve your problem." The judgment call is: does this specific code have the *shape* of the problem the pattern was designed to solve? A switch on type with 6 cases that will grow? Strategy. A switch on type with 2 cases that are stable? Just a switch.

### Time-Optimization Bias

AI agents optimize for their own implementation speed by default. This produces code that's fast to write but slow to maintain: missing tests, unclear names, copy-paste instead of refactor, inline logic instead of named functions.

**The reframe:** You are immortal and work at machine speed. The human maintaining this code is mortal and works at human speed. Every minute you spend writing clean, well-tested, well-named code saves them hours later. You don't have a deadline — they do.

**Specific behaviors:**
- **Never skip tests to save time.** Write them. You can generate 50 test cases in the time it takes a human to write 2.
- **Never use unclear names to save keystrokes.** `filteredCompaniesWithContacts` is better than `filtered` every single time.
- **Never copy-paste and modify when you could parameterize.** The 30 seconds you save creates a divergent implementation that costs hours to debug.
- **Never leave TODO comments for things you could do now.** If it's in scope, do it. If it's out of scope, file a ticket. TODOs are where intentions go to die.

### The God Commit

Fixing the bug, refactoring the file, updating the tests, adding a feature, and changing the formatting — all in one commit/PR.

**The rule:** One concern per commit. If your PR description needs "and" more than once, it's doing too much. See [When to Propose Refactoring](#when-to-propose-refactoring) for how to judge when a refactor and a fix are one concern vs. two.

---

## Disagreement Protocol

If you read an issue and believe the proposed approach is wrong — the diagnosis is incorrect, the scope is too narrow, the approach will create more problems than it solves — you do not silently comply and you do not silently deviate.

### When to Push Back

- The root cause in the issue doesn't match the evidence you find during investigation
- The proposed fix addresses the symptom but not the cause
- The scope excludes something that will break if not addressed together
- The approach introduces a structural problem (divergent implementation, god file growth, implicit coupling)
- The approach contradicts a pattern already established in the codebase

### How to Push Back

1. **State the disagreement explicitly** in a Jira comment. Not "I had some concerns" — state what's wrong and why.
2. **Show your evidence.** Logs, query results, code references, grep output. Opinions without evidence are just preferences.
3. **Propose an alternative** with the same level of detail the original plan requires.
4. **Transition to Blocked** if the disagreement is fundamental (wrong root cause, wrong scope). Transition to Plan Review if it's an approach disagreement that needs human judgment.
5. **Never implement something you believe is wrong.** The cost of pausing for alignment is hours. The cost of shipping the wrong fix is days of debugging + a revert + doing it right the second time.

---

## Mid-Implementation Discovery Protocol

Plans are hypotheses. Implementation is the experiment. When reality contradicts the plan, the plan is wrong — not reality.

### When Your Plan Breaks

This will happen. You'll discover during implementation that:
- The root cause is different than diagnosed
- The scope needs to be larger (or smaller) than planned
- The approach hits a technical wall you didn't anticipate
- A dependency you assumed existed doesn't, or behaves differently

### What to Do

**Minor deviation** (approach changes but scope and outcome are the same):
- Continue implementing
- Document the deviation in your PR description: "Plan said X, implemented Y because [evidence]"
- Update the Jira plan comment with a strikethrough and correction so the record is clear

**Major deviation** (root cause is different, scope changed, or outcome affected):
- **Stop implementing.** Do not force the original plan onto a different problem.
- Comment on the Jira ticket with what you found, what changed, and a revised plan
- Transition back to Plan Review for re-approval
- If you've already written code, keep it on the branch — don't throw it away. Note what's reusable in the revised plan.

**The instinct to resist:** AI agents are biased toward completing the plan they started. This is the single most common source of AI slop — the plan says "add a null check in component X" but the real problem is in service Y, and the AI adds the null check anyway because that's what was approved. Fight this instinct. A correct pivot beats a completed mistake.

---

## Investigation-In-Progress Plans

Sometimes you can't complete the full review because investigation is ongoing. This is acceptable — but there are rules.

### What You Can Submit

A plan with incomplete investigation must:
- Clearly label which sections are confirmed and which are hypotheses: "Root cause (confirmed via CloudWatch logs): X" vs. "Root cause (hypothesis — needs DB verification): X"
- State what investigation remains and what you need to complete it
- Include the Architectural Review sections you CAN complete (Divergent Implementation Search doesn't require knowing the root cause — you can search for related code anytime)

### What You Cannot Submit

- A plan where the approach is based on an unconfirmed hypothesis. "I think the bug is in X, so here's my plan to fix X" without evidence is guessing — and guessing is where hacks come from.
- A plan that skips the review sections entirely. "Under investigation" means some sections are incomplete, not that reviews don't apply.

### Gate Rules

- An investigation-in-progress plan **cannot** move to Ready for Development. It stays in Plan or Plan Review until investigation is complete.
- The investigation itself may require access (database, logs, environment) — if you're blocked on access, say so explicitly and transition to Blocked.

---

## Examples

### Bad Bug Issue
> **Title:** Fix selection count
> **Description:** The count is wrong on Discover. Should show right number.

This tells engineering nothing. What count? Wrong how? Right number according to what rule?

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
> **Test plan:** Unit test: set selection Map to 5 entries, set searchResults to 2 entries (subset), assert badge shows 5. Edge cases: empty selection, single page (no pagination), selection then deselection. Regression: run existing discover-tab spec suite.
>
> **Architectural Review:**
> - Root cause depth: Symptom — badge shows 0. Cause — `getTabSelectedCompanies()` filters against current-page results only. Structural deficiency — no single source of truth for selection count; each tab computes its own via different logic.
> - Design patterns: No pattern applies — this is straightforward state consumption. The store already IS the single source of truth; Discover just wasn't using it. No pattern change needed.
> - Divergent implementations: Evaluate tab has `getVisibleSelected()` which filters against `savedWebsites` (correct for its context — scopes to saved companies). Discover's `getTabSelectedCompanies()` is the divergent path. Searched: `grep -r "selectedCompan" --include="*.ts"`, `grep -r "getSelected\|getVisible" --include="*.ts"`. Fix removes the unnecessary filter on Discover.
> - Fix vs. design: Fix IS the right design. Raw count is the correct semantic for Discover selections.
> - Untouched: `evaluate-tab.component.ts` — its filter is correct (scopes to saved companies). `store-selection.ts` — raw count already correct, bug is in the consumer.
>
> **Efficiency Review:**
> - Concurrency: N/A — single synchronous computation, no I/O.
> - Data flow: Currently filtering a Map against an array on every render. Fix removes the filter entirely — O(1) `Map.size` instead of O(n) filter.
> - Caching: N/A — `Map.size` is O(1), no caching needed.
>
> **Structural Quality:**
> - Divergent logic identified and resolved in this fix. No god-file contribution (removing code, not adding). No implicit coupling introduced.

### Bad Feature Issue
> **Title:** Add has_contacts filter
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
> **Test plan:** Backend: integration test — seed 10 companies, 5 with contacts. Request with `has_contacts=true`, assert 5 returned. Request without param, assert 10. Frontend: unit test — toggle filter, verify query param included in next API call. Edge cases: list with 0 contacts (empty state), toggle on/off across pagination.
>
> **Architectural Review:**
> - Root cause depth: N/A (feature, not bug). The structural gap is that filtering is client-side for a server-paginated dataset — the architecture doesn't support what the user needs.
> - Design patterns: The existing label filter established a Query Parameter → Aggregation Pipeline pattern for server-side filtering. This is the right pattern — following it, not inventing a new one.
> - Divergent implementations: Searched for other filter implementations — only the label filter exists. Following the same pattern ensures one approach to server-side filtering. Searched: `grep -r "has_contacts\|hasContacts" --include="*.ts" --include="*.js"`, `grep -r "query.*filter\|filter.*query" routes/`.
> - Fix vs. design: This IS the right design. Server-side filtering for paginated data.
> - Untouched: Discover tab — contacts aren't relevant to search results, only to saved companies. Contact enrichment service — read-only consumer, no changes needed.
>
> **Efficiency Review:**
> - Concurrency: Single aggregation pipeline — MongoDB handles internal parallelism. No application-level parallelism needed.
> - Data flow: `$lookup` against `contact_enrichments` adds one pipeline stage. Indexed on `target_list_id` — verify index exists or add it.
> - N+1: No — single aggregation, not per-row lookup.
> - Caching: N/A — filter state is transient (toolbar toggle), each pagination request includes the param.
>
> **Structural Quality:**
> - No god-file contribution — toolbar toggle is a small addition. Backend change is in the existing query builder.
> - No missing abstraction — following existing query-param pattern, which is already the right abstraction.
> - No implicit coupling — filter state lives in the toolbar component and is passed as a query param. Explicit contract, no hidden state.

### Good Issue with Fix ≠ Design
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
> **Test plan:** Integration test: process 10-row batch, verify `completed_count` reaches 10 before `batch_end` completes. Unit test: SQS worker updates count on completion, not on batch_end. Frontend: verify "Finalizing..." state appears when count = total but status ≠ success.
>
> **Architectural Review:**
> - Root cause depth: Symptom — progress stalls at 90%. Cause — `completed_count` only updates after `batch_end`. Structural deficiency — progress tracking is coupled to post-processing; these are separate concerns (work completion vs. finalization) but share a single counter.
> - Design patterns: The batch processing pipeline is an implicit Pipeline/Chain pattern but the "progress" concern is tangled into the "processing" concern. The right design would separate the progress tracking into an Observer on per-row completion. Current fix decouples the count update from batch_end without the full Observer refactor.
> - Fix vs. design: **They differ.** Fix: move count update to SQS worker, add "Finalizing" UI state. Right design: Observer pattern on row completion, with progress as a subscriber that's fully decoupled from the processing pipeline. The right design is ~5 SP across backend + engine and affects the SQS worker contract. Filing SPE-XXX for the structural fix. Current fix is acceptable because: (a) it resolves the user-facing stall, (b) it moves in the right direction (decoupling count from batch_end), (c) the Observer refactor can be layered on top without rework.
> - Divergent implementations: Other progress tracking (scorecard, single-company operations) use direct status field polling, not count-based. No divergence — different mechanisms for different operation types.
> - Untouched: `batch_end` handler — its processing logic is correct; the bug is in WHEN it updates the count, not WHAT it does. Frontend polling logic — it already handles count/total correctly; it just needs the "Finalizing" state addition.
>
> **Efficiency Review:**
> - Concurrency: SQS workers already process in parallel. Count update is an atomic `$inc` — safe under concurrency, no locking needed.
> - Data flow: Adding one `$inc` per worker completion. Already happening for other fields — marginal cost.
>
> **Structural Quality:**
> - Progress tracking coupled to post-processing identified as a structural issue. Follow-up ticket SPE-XXX filed for Observer-based decoupling. Current fix reduces coupling without full refactor.

---

## Checklist

Before moving an issue to Plan Review, confirm every section. A missing section means the issue is not ready. For **Trivial** tier (1 SP), items marked with ★ are the only required checks.

### Issue Quality
- [ ] ★ Symptom described in user terms (not developer terms)
- [ ] ★ Expected behavior stated explicitly with measurable criteria
- [ ] ★ Reproduction steps included (or marked as intermittent with details on what was tried)
- [ ] Root cause identified with file/method/line references (or marked as "under investigation" — not guessed)
- [ ] Evidence cited — logs, query results, or reproduction data that confirms the diagnosis
- [ ] ★ Approach described in plain English with scope boundaries (what changes AND what doesn't)
- [ ] ★ Test plan included — what's tested, how, edge cases, regression scope
- [ ] Estimation fields set (Risk, Intensity, Story Points, Velocity Impact)
- [ ] If SP > 5, breakdown into sub-tasks proposed instead of a monolithic plan

### Architectural Review
- [ ] Root cause depth: symptom, cause, and structural deficiency all named (or "none — genuine logic error" with justification)
- [ ] Design pattern analysis: current pattern named if applicable, correct pattern identified if needed, "no pattern applies" accepted with reasoning
- [ ] Divergent implementations searched — evidence shown (grep commands, files checked), not just "none found"
- [ ] ★ Fix vs. design stated explicitly — if they differ, workaround justified AND follow-up ticket filed
- [ ] ★ Untouched code listed with justification for each item

### Efficiency Review
- [ ] Independent I/O operations identified — parallel where possible, sequential only with justification
- [ ] Batch operations used instead of loops where applicable
- [ ] No N+1 queries — data access pattern traced and verified
- [ ] Algorithm complexity stated for core operations — no hidden O(n²)
- [ ] Over-fetching checked — projections/field selection used where appropriate
- [ ] Sections that don't apply marked "N/A — [reason]" (not omitted)

### Structural Quality
- [ ] No god-file contributions — if target file is already too large, extraction proposed with structural case
- [ ] No missing abstractions — repeated logic extracted based on complexity × frequency, not count alone
- [ ] No implicit state coupling — all cross-component data flows use explicit contracts
- [ ] Refactoring proposals (if any) include a structural case: principle violated, pattern that fixes it, bugs it prevents
- [ ] Refactor + fix in same PR only when inseparable (revert test: could you revert the refactor without reintroducing the bug?)

### AI Anti-Pattern Self-Check
- [ ] ★ No "simplest solution" framing — approach justified by correctness, not ease
- [ ] ★ No scope shrinking — all requirements from the issue are addressed
- [ ] ★ No defensive spackle — null checks only at system boundaries, not internal code paths
- [ ] No premature abstraction — no utilities/factories/configs for single-use cases
- [ ] No pattern blindness — conditionals on type/state evaluated for GoF pattern fit
- [ ] No cargo-cult patterns — every pattern/library justified by the specific problem
- [ ] ★ No time optimization — tests written, names clear, no copy-paste-modify
- [ ] One concern per commit — PR doesn't bundle unrelated changes

### Process Checks
- [ ] ★ If you disagree with the issue's diagnosis or approach, disagreement documented with evidence before implementing
- [ ] If investigation is incomplete, hypothesis vs. confirmed sections clearly labeled
- [ ] If plan changes during implementation, deviation documented (minor: PR description, major: back to Plan Review)
