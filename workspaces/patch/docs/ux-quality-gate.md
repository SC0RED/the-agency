# UX Quality Gate — Frontend Work

Any ticket that touches UI components triggers this gate. Not optional for frontend work.

---

## Before Writing Code

1. Read the ticket spec / mockup / description.
2. Run it against the UX skill checklist at `.claude/skills/ux-review/SKILL.md` in `Platform-Frontend`.
3. If the spec itself violates the checklist (e.g. asks for a 15-column table), **push back on the ticket** with specific concerns. Do not build a bad design — flag it.
4. If the spec is vague on UI details, apply the skill's patterns as defaults (detail drawer, max 8 columns, 3-button toolbar, progressive disclosure).

---

## During Implementation

- Check component size limits after every major addition: template ≤ 300 lines, TypeScript ≤ 400 lines.
- If approaching limits, stop and extract sub-components before continuing.
- Use sc0red design tokens (`scored-*`, `primary-*`, `success-*`) — never raw hex or generic Tailwind colors.
- Every table gets an empty state with message + CTA.
- Every action toolbar: 1 primary, 1–2 secondary, rest in overflow menu.

---

## Before Opening PR

1. Take a screenshot of the UI change.
2. Run the full UX checklist against it.
3. Include checklist results in the PR description under a `## UX Review` section.
4. If any checklist item fails, fix it before opening the PR — don't ship known UX violations.

---

## Key Rules

- **Tables:** max 8 visible columns. Detail drawer for everything else.
- **Buttons:** max 3 visible per toolbar. Overflow menu for the rest.
- **Components:** max 300 line templates. Extract or refactor.
- **Never replicate existing anti-patterns.** If the current code has a 20-column table, that's a bug — don't build another one to match.
- **When in doubt, less is more.** Show less data by default, let users drill in. Users want clarity and speed, not completeness.
