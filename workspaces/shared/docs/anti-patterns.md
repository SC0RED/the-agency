# AI Anti-Patterns — Mandatory Reading

These are the patterns that turn AI-generated code into slop. If you catch yourself doing any of these, stop and reconsider. They're invisible from the inside — they feel like good engineering while they're happening. They're not.

Injected into both plan and implementation templates. The patterns apply to both the plan you write and the code you ship.

---

## "The Simplest Solution"

When an AI says *"the simplest solution is,"* it almost always means *"I'm about to hack my way through this instead of doing the right thing."* Simplicity is a virtue in design — but "simple to implement right now" and "simple to maintain forever" are different things.

**The tell:** The proposed solution avoids touching the actual problem. It wraps, intercepts, special-cases, or adds a flag instead of fixing the root cause.

**Examples:**

- *"The simplest solution is to add a null check here"* — instead of figuring out why the value is null.
- *"The simplest solution is to add a setTimeout"* — instead of understanding the lifecycle.
- *"The simplest solution is to copy this method and modify it"* — instead of parameterizing the original.
- *"The simplest solution is to add a flag parameter"* — instead of decomposing the function.

**The rule:** Never propose *"the simplest solution."* Propose the *right* solution. If the right solution is also simple, great — but lead with *why it's right*, not why it's simple.

---

## Scope Shrinking

AI agents instinctively reduce scope to reduce risk. When a task is complex, the temptation is to solve 80% of it and call it done. This manifests as:

- Silently dropping edge cases (*"this handles the main flow"*)
- Implementing the easy parts and deferring the hard parts to "follow-up"
- Choosing an approach that's easier to implement but worse for the user
- *"For now, we can just..."* — there is no "for now." There is only the code that ships.

**The rule:** Implement what was asked. All of it. If the scope genuinely should be smaller, say so explicitly with reasons — don't quietly shrink it.

---

## Defensive Spackle

Adding null checks, try/catch blocks, fallback values, and optional chaining to internal code paths instead of ensuring the data is correct at the source.

**Examples:**

- `value?.nested?.field ?? 'default'` — if this value should always exist, a silent fallback hides the bug that made it missing.
- `try { riskyThing() } catch (e) { /* silently continue */ }` — now you'll never know it failed.
- `if (data && data.length > 0)` on data that is always an array — this isn't safety, it's doubt.

**The rule:** Internal code should trust internal contracts. Validate at system boundaries (user input, external APIs, database reads). Inside the system, if something is null that shouldn't be, that's a bug — surface it, don't paper over it.

---

## Premature Abstraction

Creating abstractions, utilities, factories, or configuration systems for things that exist in exactly one place.

**Examples:**

- Writing a `formatCompanyName()` utility used by one component
- Creating a configuration object for values that will never change
- Building a plugin system for a feature with one implementation
- Adding generic type parameters to a function called with one type

**The rule:** Wait until you understand the actual variation before designing for it. The threshold for extraction is complexity × frequency, not count alone.

---

## Pattern Blindness

The inverse of cargo-cult patterns. AI agents default to procedural code — long methods, nested conditionals, manual state tracking — when a named design pattern would solve the problem cleanly. This happens because patterns require recognizing the *shape* of a problem, and AI agents optimize for the *immediate* problem.

**Symptoms:**

- A method with a growing switch/case on a type field → should be Strategy
- A class with boolean flags controlling behavior branches → should be State
- A constructor with 8+ parameters, half optional → should be Builder
- Multiple listeners manually wired to a shared data source → should be Observer/Subject
- A chain of if/else handlers where each checks eligibility → should be Chain of Responsibility

**The rule:** Before writing a conditional that switches on type or state, ask: is there a Gang of Four pattern for this shape? If yes, use it. Patterns exist because they've been proven to prevent the exact class of bugs that procedural alternatives create. A Strategy pattern isn't overhead — it's insurance against the next developer adding case 17 to your switch statement.

---

## Cargo-Cult Patterns

The inverse of pattern blindness. Applying patterns, libraries, or architectural decisions because they're "best practice" rather than because the problem requires them.

**Examples:**

- Adding Redux/NgRx to manage state that lives in one component
- Creating an abstract base class for a single implementation
- Using a factory pattern when a constructor works fine
- Adding dependency injection for a pure utility function
- Wrapping a perfectly good library in an "adapter" for no reason

**The rule:** Every pattern has a cost (complexity, indirection, learning curve). Only introduce a pattern when the cost of *not* having it is higher. *"Best practices"* are contextual — a pattern that's essential in a 500-developer monolith is overhead in a 3-developer startup.

**How Pattern Blindness and Cargo-Cult coexist:** These are not contradictions. Pattern Blindness says *"recognize when a pattern solves your problem."* Cargo-Cult says *"don't use a pattern that doesn't solve your problem."* The judgment call: does this specific code have the *shape* of the problem the pattern was designed to solve? A switch on type with 6 cases that will grow? Strategy. A switch on type with 2 cases that are stable? Just a switch.

---

## Time-Optimization Bias

AI agents optimize for their own implementation speed by default. This produces code that's fast to write but slow to maintain: missing tests, unclear names, copy-paste instead of refactor, inline logic instead of named functions.

**The reframe:** You are immortal and work at machine speed. The human maintaining this code is mortal and works at human speed. Every minute you spend writing clean, well-tested, well-named code saves them hours later. You don't have a deadline — they do.

**Specific behaviors:**

- **Never skip tests to save time.** Write them. You can generate 50 test cases in the time it takes a human to write 2.
- **Never use unclear names to save keystrokes.** `filteredCompaniesWithContacts` is better than `filtered` every time.
- **Never copy-paste and modify when you could parameterize.** The 30 seconds you save creates a divergent implementation that costs hours to debug.
- **Never leave TODO comments for things you could do now.** If it's in scope, do it. If it's out of scope, file a ticket. TODOs are where intentions go to die.

---

## The God Commit

Fixing the bug, refactoring the file, updating the tests, adding a feature, and changing the formatting — all in one commit/PR.

**The rule:** One concern per commit. If your PR description needs "and" more than once, it's doing too much.

Revert test: could someone revert one part of this commit without reintroducing the bug or breaking the feature? If yes, they're separate concerns — split the commit. If no, they're inseparable — keep them together.
