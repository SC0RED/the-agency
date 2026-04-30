# Estimation & Prioritization Framework

Software estimation is inherently noisy. The point of this framework is not precision — it's a **horseshoes-and-hand-grenades** sanity check that gets humans and agents aligned on *roughly how big is this thing, and do we need to break it down before anyone touches it.*

Then — separately — the same framework produces data that feeds forecasting models (including Monte Carlo simulations of cycle time). Both purposes work only if the unit is shared across every actor doing the work.

## The principle that makes this work

**Story Points measure the *work*, not the *worker*.** A ticket that's 5 SP for a human engineer is 5 SP for Patch. They may take vastly different wall-clock amounts to complete it — that's a calibration property of each actor, tracked separately — but they arrive at the same SP by looking at the same observable properties of the ticket.

If you let the SP definition drift per actor ("5 SP = a few days for me / 60 turns for Patch"), you end up with two different rulers, and any forecasting model built on top of mixed-ruler data is garbage.

## Two subjective scores → one Story Point value

Score every issue on:

1. **Risk** — how likely is this work to create unpredictability? (What can go wrong that we can't see yet?)
2. **Intensity** — how much *work* is this? (Observable scope and depth, not wall-clock time.)

### Estimation Table

|                   | High Risk | Medium Risk | Low Risk | No Risk |
| :---------------: | :-------: | :---------: | :------: | :-----: |
| High Intensity    |    21     |     13      |    8     |    5    |
| Medium Intensity  |    13     |     8       |    5     |    3    |
| Low Intensity     |    8      |     5       |    3     |    2    |
| No Intensity      |    5      |     3       |    2     |    1    |

Story Points are a unit of *weight* — a 21 weighs a lot, a 1 is feather-light.

**Ceiling rule:** no issue moves to In Progress with SP > 5. If it weighs more than 5, break it down. The game is how to decompose the boulder into movable rocks, not how to push it harder.

---

# Risk

Risk is the degree to which this work could introduce unpredictability — ripple effects, hard-to-undo changes, unexpected coupling. Signals are observable properties of the code and the change, not properties of whoever's doing the work.

## Observable Risk Signals

Before scoring, check:

- **Test coverage of the affected code.** Low coverage = low evidence your change won't break something. Run the repo's coverage report or inspect the spec files adjacent to the target.
- **Blast radius.** `grep` for consumers of the symbols you're changing. A function called from one place is lower risk than one called from forty.
- **Reversibility.** Can a `git revert` restore prior behavior? Changes to SCSS, UI copy, and pure additions revert cleanly. Database migrations, API contract changes, and anything deployed to shared infrastructure don't.
- **Contract surface.** Does the change affect an interface that another system consumes (API, schema, event payload, public type)? Cross-boundary changes require coordination that intra-boundary changes don't.
- **Sensitivity.** Auth, security, billing, data shape, audit log, anything legally scoped — these are escalation territory regardless of how small the diff looks.
- **Coordination.** Is another open ticket or PR also touching this code? Concurrent edits amplify risk.

## High Risk

High-risk work could introduce significant unpredictability. High-risk work:

1. Creates ripple effects into code or systems outside the immediate scope
2. Is difficult to undo (schema migration, destroyed data, deployed contract change)
3. Increases the risk of other in-flight work in unanticipated ways
4. Touches auth, security, billing, data shape, or an external party's contract
5. Has low test coverage in the affected code
6. Has high blast radius (many consumers of the changed symbols)

### Examples of High-Risk Work

**Introducing unfamiliar architecture.** The codebase has no precedent for what you're about to do. Ways to reduce the risk:

- Break off a research/spike ticket first, separate from the production-ready ticket.
- Find an established library that handles the commodity parts.
- Prototype on a throwaway branch, then write the production version informed by what you learned.

**Large amounts of entirely new code.** New code is new opportunities for defects, poor documentation, and technical debt. Ways to reduce the risk:

- Ship a minimal first version with an architecture that can be expanded.
- Lean on existing libraries where possible.
- Build in test coverage from the first commit, not after.

**Touching unfamiliar, poorly-documented, low-coverage code.** The combination is the danger. Ways to reduce the risk:

- Split the work: first refactor the confusing parts and add coverage, *then* make the intended change on top of the improved foundation.
- Wrap the confusing code behind a clean interface, solve the problem, and file a follow-up for the underlying cleanup.

**Changing architecture.** New boundaries, new failure modes. Ways to reduce the risk:

- Build in parallel behind a feature flag or dynamic switch, allowing safe fallback to the old path.
- Establish the "Definition of Victory" up front — what does perfect look like? Often the honest answer reveals the change isn't worth it.
- Decompose large architectural shifts into smaller boundaries that can be replaced one at a time.

**Database schema changes.** Tables that consumers depend on shouldn't change shape without coordination. Ways to reduce the risk:

- Keep access mediated through an ORM or repository layer.
- Use dual-write / backfill / cutover patterns to transition incrementally.
- Back up first — always have a revert path.

## Medium Risk

Medium-risk work introduces some unpredictability. Medium-risk work:

1. Can be undone but the undo takes effort (revert + redeploy, data backfill)
2. Might take longer than expected but not dramatically so
3. Has observable impact on others, but the impact is well-understood and coordinated

### Examples of Medium-Risk Work

**Upgrading a dependency.** Transitive breaking changes and deprecations hide in minor version bumps. Ways to reduce the risk:

- Upgrade on a branch with exhaustive test runs before merge.
- Check the community for known problems with the target version.
- Stage with a single repo before propagating across all three.

**Refactoring existing code.** Behavior shouldn't change, but refactors still introduce bugs. Ways to reduce the risk:

- A strong test suite is the main defense — if behavior is preserved, tests should stay green.
- Decompose into smaller, sequential steps; ship each as its own PR when possible.
- Consider an abstract-factory style switch so you can flip between old and new implementations during verification.

**Fixing a bug in a shared library.** Ripple effects into every consumer. Ways to reduce the risk:

- Comprehensive testing, including integration tests in every consuming service.
- Stage the library version and roll out one consumer at a time.

**Replacing the implementation behind a stable interface.** The contract stays the same, but the implementation changes. Ways to reduce the risk:

- Parity tests that exercise both implementations against the same inputs.
- Roll out with a kill switch that can route back to the original implementation.

## Low Risk

Low-risk work introduces little to no unpredictability. Low-risk work:

1. Is easy to undo within minutes (one revert commit, no data migration)
2. Has few side effects, and known ones are well-understood
3. Is unlikely to affect others

### Examples of Low-Risk Work

**Changing configuration values.** Externalized settings that a deploy can flip back trivially.

**Adding logging or observability.** Low-risk by construction; the main downside is performance, and even that's usually marginal.

**Adding test coverage to existing code.** New assertions on existing behavior — no behavior change.

## No Risk

No-risk work is guaranteed safe. No-risk work:

1. Can be undone instantly
2. Has no side effects beyond the narrow change
3. Cannot negatively affect anyone

### Examples of No-Risk Work

**Documentation changes.** Docs don't execute.

**Small, contained PRs** (typically under 20 lines). Single-responsibility, surgically scoped, easy to review and reverse.

**Account and permission changes with clear audit trail.** Low-stakes administrative work.

---

# Intensity

Intensity is how much **work** the change represents — observable properties of what has to be done, not how long it will take any particular actor to do it.

This is the estimate that most often drifts when humans and agents share a framework: the temptation is to ground it in time ("a week of effort"). Don't. Ground it in observable scope. Each actor's wall-clock or turn-count is a calibration property, tracked separately — see *Measurement & Calibration* below.

## Observable Intensity Signals

Before scoring, inventory:

- **Scope** — how many files, repos, or systems does this touch?
- **Depth** — surgical (one spot), modular (a handful of related spots), pattern-level (refactor across a concept), architectural (new boundaries, new abstractions).
- **Novelty** — does the codebase have precedent for this? Established pattern to follow = lower intensity. Inventing the pattern = higher intensity.
- **Test surface** — how much new test work falls out of the change? Adding one behavior is lower intensity than adding a behavior plus three edge-case variants.

## No Intensity

- **Scope:** 1 file, 1–few lines
- **Depth:** surgical
- **Novelty:** none — the change is a direct substitution (typo, log statement, config tweak, CSS value change)
- **Test surface:** none, or a single added assertion

## Low Intensity

- **Scope:** under 5 files, single repo
- **Depth:** single concern, no new abstraction
- **Novelty:** following an established pattern in the codebase
- **Test surface:** one or two new tests of clearly delineated behavior

Examples: adding an input validation, fixing a well-isolated logic bug with a regression test, wiring a new query parameter through an existing endpoint.

## Medium Intensity

- **Scope:** many files in one repo, *or* two repos with small changes each
- **Depth:** modular — multiple related changes that fit cleanly into existing structures
- **Novelty:** mostly following existing patterns; possibly one small new abstraction
- **Test surface:** a handful of new tests including edge cases

Examples: new API endpoint with a frontend consumer, a new filter applied across UI + server, a feature flag rollout touching both sides of a boundary.

## High Intensity

- **Scope:** multi-repo (2+), *or* substantial new code in one repo
- **Depth:** pattern-level or architectural — introduces new abstractions, new interfaces, or crosses several layers
- **Novelty:** little or no precedent in the codebase; you're establishing the pattern
- **Test surface:** broad — unit + integration across every layer touched

Examples: a character-limit feature spanning Engine schema + Backend validator + Frontend UI + tests at each level; introducing a new state machine to replace accidental procedural code; a schema migration with dual-write.

**If a ticket scores High Intensity, it's probably over the 5-SP ceiling already. Break it down before starting.**

---

# Measurement & Calibration

This is where the shared SP scale pays dividends.

**The ruler is shared. The conversion is per-actor.**

Both humans and agents look at the same ticket and arrive at the same SP using the signals above. What differs is the conversion from SP to their own throughput:

- **Humans** track hours-or-days per SP. Over many tickets, each human builds a personal distribution. *"Engineer A averages ~4 hours per Low SP; Engineer B averages ~6."*
- **Patch** tracks `turns` and `total_cost_usd` per SP, emitted by every `runner.result` event and logged structurally. Over many tickets, her distribution looks like *"Low-Intensity tickets average 18 turns, ~$0.30."*

Feed both distributions into the same forecasting model (Monte Carlo, cycle-time prediction, whatever). The shared SP is the joint axis; each actor's conversion is a column. The model can answer *"if Patch takes this 8-SP ticket, what's the p90 completion time?"* the same way it answers it for a human.

## What to record per completed ticket

- SP (set at the Plan stage)
- Actual actor (who or which agent picked it up)
- Wall-clock (for humans) or `num_turns` + `total_cost_usd` (for Patch)
- Any major deviation from the plan (Mid-Implementation Discovery events)
- Final outcome status (merged, abandoned, blocked)

Over 20–30 completed tickets, each actor has enough data for honest calibration — and the team has enough data for Monte Carlo to be useful rather than ceremonial.

---

# Business Value

Business Value is perceived client desirability and value. Product owns this score — engineers don't set it.

|               | Description                                                                                                                                       | Examples                                                                                                                                                       |
| :------------ | :------------------------------------------------------------------------------------------------------------------------------------------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **High**      | "Must have" features — required for the product to be considered functional by clients. Must ship regardless of velocity impact.                  | Foundational features like the ability to generate Insights. Security work that blocks customer trust. Technical stories that block must-have features.        |
| **Medium**    | "Should have" features — important for serving clients, but the product is functional without them.                                               | Features that meet customer expectations, like returning Insights in a preferred file format.                                                                  |
| **Low**       | "Could have" features — not essential, not time-sensitive, but would improve user satisfaction.                                                   | Enhancements users don't expect, like showing detailed errors about why a batch job failed.                                                                     |
| **None**      | Not tied to business value — purely technical work. May still be prioritized when velocity impact is strong.                                       | Internal tooling, refactors of test infrastructure, observability work.                                                                                        |

Business Value is a snapshot in time. Groom it regularly — what was hot last quarter may not matter today.

---

# Velocity Impact

Velocity Impact measures how much this work affects *future* throughput. Engineers own this score — Product doesn't set it.

The unit isn't *"developer days saved"* — it's *"drag removed from future work."* Same concept, actor-neutral phrasing.

|                          | Description                                                                                             | Examples                                                                                                                                                         |
| :----------------------- | :------------------------------------------------------------------------------------------------------ | :--------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Strong Positive**      | Unblocks a lot of future work, or eliminates a recurring source of friction that currently slows many tickets. | Installing `gh` + the GitHub App so Patch can clone all three sc0red repos — unblocks every Ready-for-Development run. Fixing stale Jira IDs — unblocks every plan run. |
| **Weak Positive**        | Makes individual tickets marginally easier — shaves friction off a common path without removing a category of problem. | Refactoring a god-file so future edits touch less code per change.                                                                                                |
| **Neutral**              | No observable effect on throughput. Feature work that touches its own isolated area.                    | A new feature that lives in a leaf module with no shared plumbing.                                                                                               |
| **Negative**             | Adds real overhead to future work but is required for another reason (compliance, security, audit).    | Implementing an approval workflow for a regulatory requirement.                                                                                                   |

## Development Priority — the prioritization grid

Combining Business Value with Velocity Impact gives an ordering for what to work on next. Highest-priority first.

|            | Strong Positive | Weak Positive | Neutral | Negative |
| :--------: | :-------------: | :-----------: | :-----: | :------: |
| **High**   |       21        |      13       |    8    |    5     |
| **Medium** |       13        |       8       |    5    |    3     |
| **Low**    |        8        |       5       |    3    |    2     |
| **None**   |        5        |       3       |    2    |    1     |

Go after the highest-priority tier first (P-21), then the next (P-13), and so on. Within a tier, use SP (from Risk × Intensity) and dependency graph analysis to break ties.

---

# Separation of Concerns

- **Product** sets **Business Value** — interprets customer inputs, user research, market analysis.
- **Engineers** (or Patch) set **Intensity**, **Risk**, **Velocity Impact** — these are properties of the work as observed by whoever will do it.

Engineers don't set Business Value. Product doesn't set Velocity Impact. The cross-check happens at the grooming sessions.

---

# Grooming

All four dimensions (Risk, Intensity, Business Value, Velocity Impact) can shift over time:

- **Risk** decreases as the codebase matures and coverage improves.
- **Intensity** decreases as precedent accumulates — the first instance of a pattern is High Intensity; the tenth is Low.
- **Business Value** shifts with product strategy.
- **Velocity Impact** shifts as the infrastructure changes — something that was high-leverage last quarter may have already been solved.

Groom weekly (every two weeks at worst). Rescore the Risk Pool first; backlog grooming is less urgent but still necessary — backlog items age poorly.

Calibration data (hours-per-SP per human, turns-per-SP for Patch) should be reviewed at the same cadence. The point of collecting actuals is to feed them back into estimates, not to archive them.
