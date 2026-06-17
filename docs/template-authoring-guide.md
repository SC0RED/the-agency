# Template authoring guide

A route template is the **entire context a context-free LLM gets** before it does
the job. Its only purpose is to give the model exactly what it needs to succeed —
no more. Every line that isn't pulling its weight is either noise that dilutes
the task or a fact that will drift out of sync with its real source.

This guide is the standard new templates are written to **and** the rubric the
template audit checks against. The audit reports findings by the numbered
sections below.

## 1. Intent block (required)

Every route template opens with an `## Intent` block, placed after any leading
`# Title`/intro or Jinja `{% set %}` lines and before the first content section
(`## team.json`, `# Current Trigger`, etc.). Exactly two fields, both positive:

```
## Intent

**Purpose:** <one sentence — the objective, stated first so the model is oriented before the steps>
**Success:** <the concrete, checkable things that make the output good>

---
```

Rules (these govern the **Intent block**, not the body — the body's step
instructions and anti-pattern lists may legitimately say "don't X"):
- **Positive framing only.** State what good *is*, never an "Out of scope" / "do
  not" list. Negative framing is unbounded (everything is out of scope) and
  models follow "do X" better than "don't do Y." If a boundary genuinely matters
  (e.g. "compose only the draft, triage already classified it"), fold it into
  **Purpose** positively. (Scope: the Intent block. Body anti-patterns are fine.)
- **Objective only, no trigger mechanics.** Never state the schedule, cron, time
  of day, or the triggering event ("runs Friday at 4pm", "fires on a Gmail
  push"). The *when/how it fires* lives in `agency.yaml`. This means cron/day/time
  and the firing event only — the dispatched task's *context* (the client,
  therapist, message it's acting on) and input provenance are not trigger
  mechanics and belong in the template.
- **No bench machine-tags.** The route's `deliverable` (text/decision/action) is
  a config attribute on the rule in `agency.yaml`, not prose in the intent.
- **Derive, don't invent.** Purpose/Success come from what the template actually
  does. Keep it tight — a summary, not a restatement of every step.

## 2. DRY — never restate what's injected or configured

If the model receives a fact another way, the template must not paraphrase it —
that paraphrase is where drift breeds.
- **Injected content**: the roster / `team.json`, gmail-label maps, system-docs
  (`{{system-doc:...}}`), and any `{{ variable }}` — reference them, don't
  re-describe their contents in prose.
- **Config**: schedule/cron, the model/tier, the tool allowlist, provider
  constraints all live in `agency.yaml`. The template doesn't restate them.
- **Other templates**: shared instructions duplicated across templates belong in
  a shared system-doc or partial, included once.

This targets restating **injected content or config**. It is NOT a violation for
the Intent block's summary to overlap the body's operating instructions — the
Intent orients, the body executes; that overlap is intended.

## 3. Accuracy — no hardcoded facts that live elsewhere

Flag any literal that has an authoritative source and could drift: times/days,
email addresses, people's names (derive the owner from `primary_inbox`), phone
numbers, counts, file paths, label names. Prefer deriving them at render time or
referencing the injected source. This is about facts with a real source that can
drift — illustrative numbers in rationale ("this saves ~$X"), input-field names,
and en dashes in numeric ranges (`1:45–2:15`) are not violations.

## 4. Formatting & structure

- Intent block present, correctly placed, correct two-field shape.
- Consistent section ordering; headings well-formed.
- No dead/duplicate Jinja (`{% set %}` that's unused; double-rendered blocks).
- Code fences closed; JSON examples valid.
- No stray TODO/placeholder text shipped as instructions.

## 5. House anti-patterns

- No AI slop: filler transitions ("That said,"), performative summaries ("To
  summarize,"), negative framing ("Don't hesitate to…").
- No em dashes (`—`, U+2014) anywhere in the template. Beyond house style, the
  model mirrors the template's prose, so em dashes in instructions prime em
  dashes in output. Use a comma, colon, period, or rewrite, and never instruct
  the model to emit one. This is the em dash only: en dashes (`–`) in numeric
  ranges and hyphens are fine. Literal external identifiers are also exempt: a
  Google Form's actual title, a filename or doc-naming convention, or any string
  matched against an external system keeps its real punctuation, even an em dash.
- No corporate-speak in anything the model emits to a person.
- Don't instruct the model to *avoid* calling a tool — if it shouldn't, it's not
  in the rule's `tools:` allowlist (the allowlist is the boundary, not prose).

## Audit finding format

For each template, report issues as: `section <n>` · `severity (high|med|low)` ·
the specific line/phrase · a concrete suggested fix. "Clean" is a valid result.
