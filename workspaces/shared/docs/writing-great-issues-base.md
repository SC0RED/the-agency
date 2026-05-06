# Writing Great Jira Issues — Base

## Reader Contract

The person reading this issue is scanning a queue, not auditing your scope. They have ten other tickets open in tabs and twenty seconds before the next one. Optimize for that reader.

Two consequences:

- **Titles are read ~100x more often than bodies.** They appear in board views, queue lists, search results, Slack notifications, and PR titles. Most readers decide whether to click based on the title alone. Spend disproportionate care on it.
- **The first sentence of every comment is the headline.** It states what changed, what's decided, or what's blocked. Provenance, prior-context recap, and scope-defense come *after* the headline — never before it.

This document tells you what every issue needs regardless of type (Bug / Feature / Task) and how to author the title and the plan comment so a queue-scanning reader can act in seconds. For type-specific guidance, see the companion docs (`writing-great-bug-issues.md`, `writing-great-feature-issues.md`, `writing-great-task-issues.md`) — they extend this one.

---

## Title Rules

A title's job is to let an unfamiliar reader describe what the work is in plain English in five seconds.

- **Verb-first.** Start with the action (`Rewrite`, `Fix`, `Add`, `Migrate`, `Deprecate`). The reader should know what *kind* of work this is from the first word.
- **No bracket prefixes.** No `[SPE-1989-E]`, no `[FOLLOWUP]`, no `[REFACTOR]`. Issue type and parent linkage already exist as structured fields. Brackets just steal characters.
- **No parent-ticket linkage in the title.** Use the *relates to* / *parent* field. The title describes *this* work, not its provenance.
- **No anticipatory parentheticals.** Drop `(NOT in SPE-1989's scope)`, `(does not affect frontend)`, `(safe to revert)`. Scope-defense belongs in the body if it belongs anywhere.
- **8-word heuristic for the verb-and-object.** The verb plus the thing being acted on should fit in roughly 8 words. Qualifying clauses after a comma or dash are free. If the core verb-and-object can't be said that briefly, the work isn't well-defined yet — sharpen it before filing.

Examples:

| Bad | Good |
| --- | --- |
| `[SPE-1989-E] Follow-up: flake_immunity guardrail (NOT in SPE-1989's scope)` | `Add flake_immunity guardrail to test-runner` |
| `[REFACTOR] Clean up retry logic (3 workers)` | `Consolidate SQS retry logic into shared helper` |
| `Fix selection count` | `Multi-select across pages loses selected count on Discover tab` |
| `Add has_contacts filter` | `Move Has Contacts filter from frontend to backend` |

---

## Comment Opening Rules

Every plan comment, every status comment, every PR-link comment, every blocked comment — they all open with the headline.

The first sentence answers exactly one of:

- **Plan comment:** *what is being proposed* (`Plan: rewrite four shared authoring docs to add a Reader Contract preamble.`)
- **Status comment:** *what changed* (`PR opened against development — link below.`)
- **Blocker comment:** *what's blocking and what's needed* (`Blocked: the testing branch diverged from production by 14 commits — need a human to reconcile before this can deploy.`)
- **Disagreement comment:** *what you disagree with and your alternative* (`Disagree with the proposed scope — evidence below shows the bug also reproduces on the Evaluate tab; expanding scope to cover both.`)

Bury-the-lede openers to avoid:

- *"Per the engineering protocol I picked this up because…"* — protocol context goes after.
- *"Following on from SPE-1989, where we…"* — recap goes after.
- *"This is a follow-up to the discussion in…"* — linkage goes after.
- *"To be clear, this is NOT in scope for…"* — scope-defense goes in a dedicated section if at all.

The headline can be one sentence. The supporting paragraphs that follow can be as long as they need to be. The discipline is on sentence one, not on total length.

---

## What Every Issue Answers

Every issue answers six questions. If it can't, it's not ready for engineering.

1. **What problem are we solving?** User-facing terms, not developer terms.
2. **What does done look like?** Explicit, measurable outcome.
3. **What's the current state?** Reproduction, workaround, or status quo.
4. **What's the technical landscape?** Where does this live in the code + data?
5. **What's the approach?** Plain English, with scope boundaries (what DOES and DOES NOT change).
6. **What's the test plan?** Specific behaviors and edge cases, not "it works."

The per-type docs specialize each question and provide good/bad examples.

For **evidence-before-theory** on question 4, follow this order regardless of issue type — don't skip ahead to reading code:

1. **Logs and errors first.** CloudWatch, application logs, browser console, error output.
2. **Data second.** Database queries, API responses, request payloads.
3. **Code third.** Now read the code knowing what happened and what the data looks like.
4. **Hypothesis last.** Build your diagnosis from evidence. If the evidence doesn't support it, the diagnosis is wrong — not the evidence.

---

## Review Lenses — Architectural / Efficiency / Structural Quality

These are tools, not gates. Use the lens that has something to say about the ticket. **Silent sections don't appear.** Don't manufacture content to fill a heading; don't add `N/A — reason` lines for sections you considered and didn't find anything in. If a heading would carry no information, omit it.

The discipline is *consideration*, not *prose*. You still walk through every lens during planning. You only write up the ones that produced something worth the reader's time.

### Architectural Review

#### Root Cause Depth

Don't accept the symptom as the problem. Name three things:

- **Symptom:** What the user sees
- **Cause:** What the code does wrong
- **Structural deficiency:** Why the code was written this way

If your fix addresses only the symptom, you're patching. If it addresses the cause, you're fixing. If it addresses the structural deficiency, you're engineering. Know which one you're doing.

When there's genuinely no structural deficiency (off-by-one, typo, wrong comparison in otherwise sound design), say so plainly: *"Logic error in an otherwise sound design — no structural change."* Don't manufacture a deficiency to fill the heading.

#### Design Pattern Analysis

Think in Gang of Four patterns — Strategy, Observer, State, Builder, Chain of Responsibility, Factory. Code doesn't just have bugs; it has *accidental patterns*. A class with 15 boolean flags has accidentally become a State machine without the State pattern. A method with a giant switch is a Strategy waiting to be extracted.

Answer:
- **What pattern does this code currently implement (intentionally or accidentally)?** Name it. If genuinely none applies, name what shape the code does have (procedural transform, CRUD handler, data pipeline) — but don't reach for "no pattern" as a default.
- **What pattern should it implement?** Only if the current structure is causing or enabling bugs. If the code is correct as-is, say so. Don't propose a pattern just to have something to write.
- **Is the pattern change in scope?** If yes, include it. If no, file a follow-up with the structural case.

What counts as a structural case: *"This file is too big"* is not a case. *"This class violates SRP by owning both cache management and build orchestration, and the missing State pattern caused a feedback loop between initialization states"* is. Name the principle, name the pattern, name the bugs it prevents.

#### Divergent Implementation Search

Search the codebase for other code doing the same thing as the code you're about to change.

- If there are multiple methods/components solving the same problem differently, your fix must address the divergence — not add another path.
- If there aren't, show what you searched for. Stating *"no divergent implementations"* is fine when the search was real and turned up nothing — show the grep.

Two components computing the same value from different sources will eventually disagree. A fix that patches one without reconciling the other trades today's bug for tomorrow's.

#### Fix vs. Design

State explicitly:

- *"My fix does X."*
- *"The right design is Y."*

If they're the same: great — say so in one line and move on. If they differ: explain why the fix is acceptable and what the right design would cost. If the right design is in scope, propose it. If not, file a follow-up.

Speed pressure makes engineers propose the first thing that works. This question forces a pause: is the thing that works also the thing that's right? Sometimes a workaround is justified — but you have to name it as a workaround, not pretend it's the real fix.

#### What Stays Untouched

When the natural reading of the change suggests it might affect adjacent code that it doesn't, name what's untouched and why:

- *"Not changing `evaluate-tab.component.ts` because its `getVisibleSelected()` filters against the full saved set, which is correct for that tab's semantics."*
- *"Not changing `store-selection.ts` because the raw count is already correct; the bug is in the consumer."*

Skip this section when there's no obvious adjacent code to defend. A two-line bug fix in an isolated utility doesn't need a "What Stays Untouched" subsection — the diff itself already shows it.

### Efficiency Review

You have unlimited time and compute. The human reviewing your work does not. Optimize for correctness, performance, and maintainability — not for your own keystrokes.

#### Concurrency and Parallelism

Identify every operation in your implementation that could run concurrently.

- **I/O operations:** Independent queries, API calls, file reads → run in parallel (`Promise.all`, `asyncio.gather`).
- **Batch operations:** Independent items in a loop → use bulk APIs. One `bulkWrite` beats N `updateOne`s. One `SELECT ... WHERE id IN (...)` beats N `SELECT ... WHERE id = ?`.
- **Pipeline stages:** Map the dependency graph. Sequential only where data flows require it.

Show your work: *"These 3 queries are independent — parallelised via `Promise.all`."* or *"Must be sequential because query B uses the result of query A."*

Sequential-by-default is the single most common performance mistake in AI-generated code. If concurrency *isn't* a relevant concern for this change (no I/O, no loops, no parallelizable work), omit the subsection rather than writing it just to omit it.

#### Data Flow Efficiency

Trace the data from source to consumer. Look for waste.

- **Over-fetching:** Loading entire documents when you need 2 fields → projections, `SELECT` specific columns.
- **N+1 queries:** Querying inside a loop → batch the lookup.
- **Redundant transformations:** Transforming the same data multiple times → transform once at the boundary.
- **Memory:** Loading an entire dataset when you could stream, paginate, or use cursors.

#### Algorithm and Data Structure Choice

State the time complexity of your core operations when complexity is non-obvious. `.find()` inside `.forEach()` is O(n²). On 50 items nobody notices. On 5,000 the UI freezes.

#### Caching and Recomputation

- Is this value computed on every call but rarely changes? Cache it.
- Is this value cached but changes frequently? Don't cache it.
- If caching: what's the invalidation strategy? A cache without invalidation is a bug on a timer.

### Structural Quality Review

Every bug is a question about structure. When investigating, audit the code you're touching for these patterns. If you find issues, name them. If you don't, omit the heading.

#### God Files

Files with an overwhelming number of responsibilities — state management AND rendering AND business logic, for example.

If the file you're about to modify is already doing too much, adding more makes it worse. Your change is the trigger to fix this, not an excuse to pile on.

Extract services, split components, apply Single Responsibility. A file should do one thing — if you need an "and" to describe it, it's doing too much.

#### Missing Abstractions

Raw data manipulation scattered across consumers instead of encapsulated in a service or utility.

Detect: business rules embedded in template expressions, the same conditional logic repeated in multiple places, multiple components doing the same transformation chain.

Threshold for extraction: complexity × frequency, not count alone. Two instances of a 50-line data transformation are worse than four instances of `item.name.trim()`. If the duplication is trivial and unlikely to diverge, leave it. If it encodes a business rule that could change, extract it regardless of count.

#### Implicit State Coupling

Components that depend on another component's internal state without an explicit contract.

Detect: state passed through 3+ levels of nesting, components reading from stores they don't own, breakage when changing "unrelated" components.

Resolve: explicit interfaces. If Component B needs data from Component A, that's a contract — type it, document it, test it.

#### When to Propose Refactoring

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

1. **State the disagreement explicitly** in a Jira comment. Not *"I had some concerns"* — state what's wrong and why. The first sentence is the headline (per Comment Opening Rules above).
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
- Comment on the Jira ticket with what you found, what changed, and a revised plan. Headline first, evidence second.
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
- Include review lenses you CAN complete (Divergent Implementation Search doesn't need the root cause)

### What You Cannot Submit

- A plan where the approach rests on an unconfirmed hypothesis. *"I think the bug is in X, so here's my plan"* without evidence is guessing.
- A plan that has skipped a lens because investigation is hard. *"Under investigation"* on a lens you haven't tried is incomplete; *"Under investigation — DB access pending"* on a lens you've started is honest.

### Gate Rules

- Investigation-in-progress plans **cannot** move to Ready for Development. They stay in Plan or Plan Review until investigation is complete.
- If investigation requires access (database, logs, environment) and you're blocked on access, say so explicitly and transition to Blocked.

---

## Author Self-Check

Before moving an issue to Plan Review, the author runs a short check on the artifact they're about to publish. This is for the author, not a signal to a reviewer — there's no checklist box to tick, no audit. Just three reads of the work:

1. **5-second test on the title.** Read your own title cold. Could a teammate unfamiliar with the parent context describe in plain English what the work is, in five seconds, without clicking through? If not — the title is doing too little or hiding behind metadata. Rewrite it.
2. **Headline test on paragraph 1.** Read the first sentence of the comment alone. Does it answer "what is being proposed / what changed / what's blocking"? If you started with "I picked this up because…", "Per the protocol…", "Following on from…" — you buried the lede. Move the headline up; provenance follows.
3. **N/A scan.** Search your own draft for `N/A`. For each match, ask: does this carry information the reader needs? If yes, keep it. If it's filler proving you considered the question, delete the whole subsection. Consideration without content is invisible to the reader; that's the point.

Beyond those three, the discipline you applied during planning (evidence-first investigation, the review lenses, scope boundaries, estimation) is what determines whether the plan is right. The self-check verifies the *artifact* communicates that work — not whether the work happened.
