# Writing Great Jira Issues — Base

A Jira issue is a contract between the person who found the problem and the person who fixes it. A great issue makes the fix obvious. A bad issue makes the engineer guess — and guessing is where hacks come from.

This base doc covers what every issue needs regardless of type (Bug / Feature / Task). For type-specific guidance on the six questions below, see the companion doc that matches the issue type — they're structured to extend this one.

---

## The Standard — Six Questions

Every issue answers six questions. If it can't, it's not ready for engineering.

1. **What problem are we solving?** User-facing terms, not developer terms.
2. **What does done look like?** Explicit, measurable outcome.
3. **What's the current state?** Reproduction, workaround, or status quo.
4. **What's the technical landscape?** Where does this live in the code + data?
5. **What's the approach?** Plain English, with scope boundaries (what DOES and DOES NOT change).
6. **What's the test plan?** Specific behaviors and edge cases, not "it works."

The per-type docs (`writing-great-bug-issues.md`, `writing-great-feature-issues.md`, `writing-great-task-issues.md`) specialize each question for the issue type and provide good/bad examples.

For **evidence-before-theory** on question 4, follow this order regardless of issue type — don't skip ahead to reading code:

1. **Logs and errors first.** CloudWatch, application logs, browser console, error output.
2. **Data second.** Database queries, API responses, request payloads.
3. **Code third.** Now read the code knowing what happened and what the data looks like.
4. **Hypothesis last.** Build your diagnosis from evidence. If the evidence doesn't support it, the diagnosis is wrong — not the evidence.

---

## Architectural Review

Include the answers under an `## Architectural Review` heading in the plan comment. This proves you understand the problem deeply enough to solve it correctly.

### Root Cause Depth

Don't accept the symptom as the problem. Name three things:

- **Symptom:** What the user sees
- **Cause:** What the code does wrong
- **Structural deficiency:** Why the code was written this way

If your fix addresses only the symptom, you're patching. If it addresses the cause, you're fixing. If it addresses the structural deficiency, you're engineering. Know which one you're doing.

When there's genuinely no structural deficiency (off-by-one, typo, wrong comparison in otherwise sound design), say so: *"Structural deficiency: none — this is a logic error in an otherwise sound design."* Don't manufacture structural problems to satisfy a checklist.

### Design Pattern Analysis

Think in Gang of Four patterns — Strategy, Observer, State, Builder, Chain of Responsibility, Factory. Code doesn't just have bugs; it has *accidental patterns*. A class with 15 boolean flags has accidentally become a State machine without the State pattern. A method with a giant switch is a Strategy waiting to be extracted.

Answer:
- **What pattern does this code currently implement (intentionally or accidentally)?** Name it, or say "No pattern applies — this is straightforward [procedural logic / CRUD / data transformation]."
- **What pattern should it implement?** Only if the current structure is causing or enabling bugs. If the code is correct as-is, say "Current structure is appropriate." Don't propose a pattern just to have something to write.
- **Is the pattern change in scope?** If yes, include it. If no, file a follow-up with the structural case.

What counts as a structural case: *"This file is too big"* is not a case. *"This class violates SRP by owning both cache management and build orchestration, and the missing State pattern caused a feedback loop between initialization states"* is. Name the principle, name the pattern, name the bugs it prevents.

### Divergent Implementation Search

Search the codebase for other code doing the same thing as the code you're about to change.

- If there are multiple methods/components solving the same problem differently, your fix must address the divergence — not add another path.
- If there aren't, show what you searched for. *"No divergent implementations"* without evidence is not an answer.

Two components computing the same value from different sources will eventually disagree. A fix that patches one without reconciling the other trades today's bug for tomorrow's.

### Fix vs. Design

State explicitly:

- *"My fix does X."*
- *"The right design is Y."*

If they're the same: great. If they differ: explain why the fix is acceptable and what the right design would cost. If the right design is in scope, propose it. If not, file a follow-up.

Speed pressure makes engineers propose the first thing that works. This question forces a pause: is the thing that works also the thing that's right? Sometimes a workaround is justified — but you have to name it as a workaround, not pretend it's the real fix.

### What Stays Untouched

List related code you're NOT changing and explain why:

- *"Not changing `evaluate-tab.component.ts` because its `getVisibleSelected()` filters against the full saved set, which is correct for that tab's semantics."*
- *"Not changing `store-selection.ts` because the raw count is already correct; the bug is in the consumer."*

If you can't justify leaving related code untouched, your scope is wrong.

---

## Efficiency Review

You have unlimited time and compute. The human reviewing your work does not. Never optimize for your own convenience — optimize for correctness, performance, and maintainability.

Include findings under `## Efficiency Review`. If a subsection doesn't apply, write *"N/A — [reason]"* and move on.

### Concurrency and Parallelism

Identify every operation in your implementation that could run concurrently.

- **I/O operations:** Independent queries, API calls, file reads → run in parallel (`Promise.all`, `asyncio.gather`).
- **Batch operations:** Independent items in a loop → use bulk APIs. One `bulkWrite` beats N `updateOne`s. One `SELECT ... WHERE id IN (...)` beats N `SELECT ... WHERE id = ?`.
- **Pipeline stages:** Map the dependency graph. Sequential only where data flows require it.

Show your work: *"These 3 queries are independent — parallelised via `Promise.all`."* or *"Must be sequential because query B uses the result of query A."* If everything is sequential, justify why.

Sequential-by-default is the single most common performance mistake in AI-generated code.

### Data Flow Efficiency

Trace the data from source to consumer. Look for waste.

- **Over-fetching:** Loading entire documents when you need 2 fields → projections, `SELECT` specific columns.
- **N+1 queries:** Querying inside a loop → batch the lookup.
- **Redundant transformations:** Transforming the same data multiple times → transform once at the boundary.
- **Memory:** Loading an entire dataset when you could stream, paginate, or use cursors.

### Algorithm and Data Structure Choice

State the time complexity of your core operations. `.find()` inside `.forEach()` is O(n²). On 50 items nobody notices. On 5,000 the UI freezes.

### Caching and Recomputation

- Is this value computed on every call but rarely changes? Cache it.
- Is this value cached but changes frequently? Don't cache it.
- If caching: what's the invalidation strategy? A cache without invalidation is a bug on a timer.

---

## Structural Quality Review

Every bug is a question about structure. When investigating, audit the code you're touching for these patterns.

Include findings under `## Structural Quality Review`. If nothing is found, say *"No structural issues identified in the code touched by this change."* Don't omit the section — absence means you didn't look.

### God Files

Files with an overwhelming number of responsibilities — state management AND rendering AND business logic, for example.

If the file you're about to modify is already doing too much, adding more makes it worse. Your change is the trigger to fix this, not an excuse to pile on.

Extract services, split components, apply Single Responsibility. A file should do one thing — if you need an "and" to describe it, it's doing too much.

### Missing Abstractions

Raw data manipulation scattered across consumers instead of encapsulated in a service or utility.

Detect: business rules embedded in template expressions, the same conditional logic repeated in multiple places, multiple components doing the same transformation chain.

Threshold for extraction: complexity × frequency, not count alone. Two instances of a 50-line data transformation are worse than four instances of `item.name.trim()`. If the duplication is trivial and unlikely to diverge, leave it. If it encodes a business rule that could change, extract it regardless of count.

### Implicit State Coupling

Components that depend on another component's internal state without an explicit contract.

Detect: state passed through 3+ levels of nesting, components reading from stores they don't own, breakage when changing "unrelated" components.

Resolve: explicit interfaces. If Component B needs data from Component A, that's a contract — type it, document it, test it.

### When to Propose Refactoring

- **Always propose** when the bug was caused by one of the patterns above (the structure created the bug).
- **Propose as follow-up** when the pattern exists nearby but didn't directly cause this bug.
- **Don't propose** when the code is clean and the bug is a genuine logic error.

**One concern per PR:** if the structural fix IS the bug fix (the refactor eliminates the bug), they're one concern — ship together. If the structural fix is adjacent improvement ("while I was in here..."), separate PR.

Revert test: could someone revert the structural change without reintroducing the bug? If yes, they're separate concerns. If no, they're inseparable.

---

## Disagreement Protocol

If you believe the proposed approach is wrong — the diagnosis is incorrect, the scope is too narrow, the approach will create more problems than it solves — you do not silently comply and you do not silently deviate.

### When to Push Back

- The root cause in the issue doesn't match evidence you find during investigation
- The proposed fix addresses the symptom but not the cause
- The scope excludes something that will break if not addressed together
- The approach introduces a structural problem (divergent implementation, god file growth, implicit coupling)
- The approach contradicts a pattern already established in the codebase

### How to Push Back

1. **State the disagreement explicitly** in a Jira comment. Not *"I had some concerns"* — state what's wrong and why.
2. **Show your evidence.** Logs, query results, code references, grep output. Opinions without evidence are just preferences.
3. **Propose an alternative** with the same level of detail the original plan requires.
4. **Transition to Blocked** if the disagreement is fundamental (wrong root cause, wrong scope). Transition to Plan Review if it's an approach disagreement that needs human judgment.
5. **Never implement something you believe is wrong.** The cost of pausing for alignment is hours. The cost of shipping the wrong fix is days of debugging + a revert + doing it right the second time.

---

## Mid-Implementation Discovery Protocol

Plans are hypotheses. Implementation is the experiment. When reality contradicts the plan, the plan is wrong — not reality.

### When Your Plan Breaks

You'll discover during implementation that:

- The root cause is different than diagnosed
- The scope needs to be larger (or smaller) than planned
- The approach hits a technical wall you didn't anticipate
- A dependency you assumed existed doesn't, or behaves differently

### What to Do

**Minor deviation** (approach changes but scope and outcome are the same):
- Continue implementing.
- Document the deviation in your PR description: *"Plan said X, implemented Y because [evidence]."*
- Update the Jira plan comment with a strikethrough and correction so the record is clear.

**Major deviation** (root cause is different, scope changed, or outcome affected):
- **Stop implementing.** Do not force the original plan onto a different problem.
- Comment on the Jira ticket with what you found, what changed, and a revised plan.
- Transition back to Plan Review for re-approval.
- If you've already written code, keep it on the branch — don't throw it away. Note what's reusable in the revised plan.

AI agents are biased toward completing the plan they started. Fight this instinct. A correct pivot beats a completed mistake.

---

## Investigation-In-Progress Plans

Sometimes you can't complete the full review because investigation is ongoing.

### What You Can Submit

A plan with incomplete investigation must:

- Label sections: *"Root cause (confirmed via CloudWatch): X"* vs. *"Root cause (hypothesis — needs DB verification): X"*
- State what investigation remains and what you need to complete it
- Include review sections you CAN complete (Divergent Implementation Search doesn't need the root cause)

### What You Cannot Submit

- A plan where the approach rests on an unconfirmed hypothesis. *"I think the bug is in X, so here's my plan"* without evidence is guessing.
- A plan that skips review sections. *"Under investigation"* means incomplete, not exempt.

### Gate Rules

- Investigation-in-progress plans **cannot** move to Ready for Development. They stay in Plan or Plan Review until investigation is complete.
- If investigation requires access (database, logs, environment) and you're blocked on access, say so explicitly and transition to Blocked.

---

## Checklist

Before moving an issue to Plan Review, confirm every section. Items marked **★** are required for Trivial (1 SP) tier; everything is required for Standard (2–5 SP) and Complex (8+ SP).

### Issue Quality

- [ ] ★ Problem stated in user terms (not developer terms)
- [ ] ★ Expected behavior stated explicitly with measurable criteria
- [ ] ★ Current state described (reproduction steps for bugs, status quo for features)
- [ ] Technical landscape mapped with file/method/line references (or marked *"under investigation"* — not guessed)
- [ ] Evidence cited — logs, query results, reproduction data confirming the diagnosis
- [ ] ★ Approach described in plain English with scope boundaries
- [ ] ★ Test plan included — what's tested, how, edge cases, regression scope
- [ ] Estimation fields set (Risk, Intensity, Story Points, Velocity Impact — see `shared/docs/estimation.md`)
- [ ] If SP > 5, breakdown into sub-tasks proposed

### Architectural Review

- [ ] Root cause depth: symptom, cause, and structural deficiency all named (or *"none — genuine logic error"* with justification)
- [ ] Design pattern analysis: current pattern named, correct pattern identified if needed, or *"No pattern applies"* with reasoning
- [ ] Divergent implementations searched — evidence shown (grep commands, files checked)
- [ ] ★ Fix vs. design stated — if they differ, workaround justified AND follow-up ticket filed
- [ ] ★ Untouched code listed with justification

### Efficiency Review

- [ ] Independent I/O operations identified — parallel where possible, sequential only with justification
- [ ] Batch operations used instead of loops where applicable
- [ ] No N+1 queries — data access pattern traced and verified
- [ ] Algorithm complexity stated for core operations — no hidden O(n²)
- [ ] Over-fetching checked — projections/field selection used where appropriate
- [ ] Sections that don't apply marked *"N/A — [reason]"* (not omitted)

### Structural Quality

- [ ] No god-file contributions — if target file is already too large, extraction proposed with structural case
- [ ] No missing abstractions — repeated logic extracted based on complexity × frequency
- [ ] No implicit state coupling — cross-component data flows use explicit contracts
- [ ] Refactoring proposals include structural case: principle violated, pattern that fixes it, bugs it prevents
- [ ] Refactor + fix in same PR only when inseparable (revert test passes)

### Process Checks

- [ ] ★ If you disagree with the issue's diagnosis or approach, disagreement documented with evidence before implementing
- [ ] If investigation is incomplete, hypothesis vs. confirmed sections clearly labeled
- [ ] If plan changes during implementation, deviation documented (minor: PR description, major: back to Plan Review)
- [ ] Anti-pattern self-check (see `anti-patterns.md`) passed
