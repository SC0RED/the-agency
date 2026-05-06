# Writing Great Jira Issues — Base

## Audience

The primary reader of every issue is an **AI agent** — Patch when planning, Scarlett when reviewing, future-Patch when picking the ticket up for development. A human reviews these too, but the agent is the one who has to act on them with no benefit of intuition or tribal knowledge.

That changes the design priorities. Optimize for:

- **Signal density.** Every section earns its place. Don't pad sections to "show you considered" something — silence is fine.
- **Explicit references.** *"`target-list-store.service.ts:142`"*, *"the existing `OperationProgressHub` pattern"*, *"SPE-1997"* — never *"the usual approach"* or *"like we did before."* Agents can't infer; humans skim past it.
- **Predictable structure.** Sections appear in a fixed order with the same names. An agent reading this ticket can locate the diagnosis or the acceptance criteria deterministically.
- **Estimation at the top.** Risk / Intensity / SP / Velocity Impact lead the body. A reader (agent or human) decides how to engage with the ticket based on its size before reading anything else.

Two consequences for titles and comment openings carry over from any reader-first doc:

- **Titles are read ~100x more often than bodies.** Spend disproportionate care on the title.
- **The first sentence of every comment is the headline** — what's proposed, what changed, what's blocked. Provenance, prior-context recap, and scope-defense come after the headline, never before.

This document defines what every issue needs regardless of type. For type-specific structure, see `writing-great-bug-issues.md`, `writing-great-feature-issues.md`, and `writing-great-task-issues.md`.

---

## Title Rules

A title's job is to let an unfamiliar reader describe what the work is in plain English in five seconds.

- **Verb-first.** Start with the action (`Rewrite`, `Fix`, `Add`, `Migrate`, `Deprecate`).
- **No bracket prefixes.** Issue type and parent linkage are structured fields. Brackets steal characters.
- **No parent-ticket linkage in the title.** Use the *relates to* / *parent* field.
- **No anticipatory parentheticals.** Drop `(NOT in SPE-1989's scope)`, `(does not affect frontend)`. Scope-defense lives in the body if it lives anywhere.
- **8-word heuristic for verb-and-object.** Qualifying clauses after a comma or dash are free. If the core can't fit, the work isn't well-defined yet.

| Bad | Good |
| --- | --- |
| `[SPE-1989-E] Follow-up: flake_immunity guardrail (NOT in SPE-1989's scope)` | `Add flake_immunity guardrail to test-runner` |
| `[REFACTOR] Clean up retry logic (3 workers)` | `Consolidate SQS retry logic into shared helper` |
| `Fix selection count` | `Multi-select across pages loses selected count on Discover tab` |

---

## Comment Opening Rules

Every plan comment, status update, blocker note, and disagreement opens with the headline.

The first sentence answers exactly one of:

- **Plan:** what is being proposed
- **Status:** what changed
- **Blocker:** what's blocking and what's needed
- **Disagreement:** what you disagree with and your alternative

Bury-the-lede openers to avoid:

- *"Per the engineering protocol I picked this up because…"* — protocol context goes after.
- *"Following on from SPE-1989, where we…"* — recap goes after.
- *"To be clear, this is NOT in scope for…"* — scope-defense goes in a dedicated section if at all.

The headline is one sentence. The supporting paragraphs that follow can be as long as they need to be. Discipline on sentence one, not on total length.

---

## The Canonical Sections

Every issue body and plan comment uses the same ordered spine:

1. **Estimation** — Risk / Intensity / SP / Velocity Impact, top of the body.
2. **Problem** — what's broken (bug), what user need (feature), or what engineering cost (task). User terms, not developer terms.
3. **Reproduction or Current State** — bug: exact steps + environment + how it was detected; feature/task: what exists today.
4. **Diagnosis or Technical Landscape** — bug: root cause traced to file:line with evidence; feature/task: the components and patterns this fits into.
5. **Approach** — the proposed change in plain English, plus *Alternatives Considered* — name the existing pattern with a path (e.g., *"considered reusing `OperationProgressHub` — rejected because X"*) or state plainly that none applies and why. This is the reuse check; it is not optional.
6. **Acceptance Criteria** — Given/When/Then, testable. Each criterion can be checked deterministically.
7. **Definition of Done** — including the regression test (bug) or coverage scope (feature/task) that proves the work landed correctly.
8. **Production Signal** *(features and perf-fix tasks)* — telemetry, metric, or observation that confirms it's working post-deploy. Distinct from acceptance criteria, which only proves correctness in test.
9. **Rollback** *(conditional — only when irreversible)* — DB migrations, schema changes, deleted data, infra mutations, anything where `git revert` doesn't fully restore prior state. For ordinary code changes, omit this section entirely.

The per-type docs specialize section 2–8 with examples. Section 1 and the conditionality of 8–9 are universal.

### Silent sections don't appear

Don't write `N/A — reason` or *"none applicable"* under a heading. If a section produced no content during planning, omit it. The discipline is *consideration*, not *prose*. You walk through every check during planning; you write up only the ones that produced findings the reader needs.

---

## Review Checks (Planning Tools, Not Required Sections)

Use these as questions to ask yourself during planning. They become content in the **Approach** or **Diagnosis** sections only when they produce something the reader needs. None of them are headings in the issue.

**Architectural**
- *Root cause depth (bugs).* Symptom vs. cause vs. structural deficiency. Patch a symptom, fix a cause, engineer a structural deficiency. Know which you're doing.
- *Pattern fit.* What pattern does the existing code implement? What pattern (if any) should the change implement? *Strategy, Observer, State, Builder, Chain of Responsibility, Factory* are the usual suspects.
- *Divergent implementations.* `grep` for code doing the same thing elsewhere. If multiple paths exist, the change must reconcile divergence — not add another path. Show the grep when there's nothing to find; that's evidence too.
- *Fix vs. design.* If they differ, name both. Justify the workaround as a workaround.

**Efficiency**
- *Concurrency.* Independent I/O / batch ops / pipeline stages — parallelize where data flow allows.
- *Data flow.* Over-fetching, N+1, redundant transforms, streaming opportunities.
- *Algorithm + data structure.* When complexity is non-obvious, state it.
- *Caching.* Cache rarely-changing values; don't cache frequently-changing ones; if caching, name the invalidation strategy.

**Structural quality**
- *God files / missing abstractions / implicit coupling.* If the bug or feature was caused by one of these, the structural fix IS part of the change. If the pattern exists nearby but didn't cause this, file a follow-up rather than scope-creep.

The **revert test** for whether a structural fix is in scope: could someone revert the structural change without reintroducing the bug? If yes, separate concerns — separate PR. If no, ship together.

---

## Evidence Before Theory

For investigation (bugs especially) — don't skip ahead to reading code:

1. **Logs and errors first.** CloudWatch, application logs, browser console, error output.
2. **Data second.** DB queries, API responses, request payloads.
3. **Code third.** Now read the code knowing what happened.
4. **Hypothesis last.** Diagnosis follows evidence. If evidence contradicts the hypothesis, the hypothesis is wrong — not the evidence.

---

## Disagreement Protocol

If the proposed approach is wrong — incorrect diagnosis, scope too narrow, approach creates more problems than it solves — neither silently comply nor silently deviate.

**When to push back:** root cause doesn't match evidence; fix addresses symptom not cause; scope excludes something that will break if not addressed together; approach contradicts an established codebase pattern; approach introduces a structural problem.

**How:**
1. Headline-first comment. State the disagreement and the alternative.
2. Show evidence — logs, query results, grep output, file:line refs.
3. Propose the alternative at the same level of detail the original plan required.
4. Transition to **Blocked** if the disagreement is fundamental; **Plan Review** if it's an approach disagreement needing human judgment.
5. Never implement something believed to be wrong. Hours of alignment beats days of debugging plus a revert.

---

## Mid-Implementation Discovery

Plans are hypotheses. Implementation is the experiment. When reality contradicts the plan, the plan is wrong.

**Minor deviation** (approach changed, scope and outcome unchanged): continue, document the deviation in the PR description, update the plan comment with strikethrough and correction.

**Major deviation** (root cause is different, scope changed, outcome affected): stop. Headline-first comment with the new evidence and revised plan. Transition back to **Plan Review** for re-approval. Keep already-written code on the branch — note what's reusable.

AI agents are biased toward completing the plan they started. Fight this. A correct pivot beats a completed mistake.

---

## Investigation-In-Progress Plans

Sometimes you can't finish investigation before posting a plan.

**Acceptable:** label sections as *confirmed* vs. *hypothesis*; state what investigation remains; include checks you CAN complete.

**Not acceptable:** approach resting on an unconfirmed hypothesis; *"Under investigation"* on a check you haven't tried.

**Gate:** investigation-in-progress plans cannot move to Ready for Development. They stay in Plan or Plan Review until investigation completes. If access is the blocker, transition to Blocked.

---

## Author Self-Check

Before moving to Plan Review, three quick checks on the artifact:

1. **5-second test on the title.** Read it cold. Could a teammate unfamiliar with parent context describe in plain English what the work is, in five seconds? If not, rewrite.
2. **Headline test on paragraph 1.** First sentence alone should answer "what is being proposed / what changed / what's blocking." If you started with *"I picked this up because…"* or *"Per the protocol…"*, move the headline up.
3. **Estimation visible at the top?** Risk / Intensity / SP / Velocity Impact appear before any prose. If they're buried, move them up.

Beyond those, the discipline applied during planning (evidence-first investigation, the review checks, scope boundaries, estimation) is what determines whether the plan is right. The self-check verifies the *artifact* communicates that work — not whether the work happened.
