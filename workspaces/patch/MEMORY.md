# MEMORY.md — Patch's Long-Term Memory
# Jira config/auth → shared skill `sc0red_jira`. Engineering pipeline → shared skill `sc0red_engineering`.

## Decisions & Policies
- **No manual browser testing.** CI passing + PR merged is the gate. Verification is a human engineer's job. (Chris, 2026-03-31)
- **Review gate = human team member**, not Chris specifically. Any human can approve plans and code. Agents can't self-approve yet — capability assessment, not permanent rule. (Chris, 2026-04-02)
- **Escalation to Chris:** auth/security, high risk, API contract issues, architectural disagreements, reviewer disputes.
- **Branch naming:** `fix/<jira-key>-<slug>` — never `patch/...` (corrected by Chris on SPE-1585)

## Jira Transitions
Transition IDs, status IDs, custom-field IDs, and field-option IDs all live in `workspaces/patch/jira-workflow.yaml`. **Never hardcode them in templates or scripts** — always load from that file. If a POST returns `400 Transition is not valid`, the YAML is stale — re-run `scripts/dump-jira-workflow.py` to refresh, commit the regenerated file.

## Workflow
- [Jira after production merges](memory/feedback_jira_after_merge.md) — after testing→prod merges, transition issues from "Verified in Testing" to "Deployed to Production"

## Communication Style
- [No internal narration](memory/feedback_no_internal_narration.md) — never expose job IDs, tool mechanics, or implementation details in user-facing messages

## Key References
- Discord #general: `1478849414629032154`
- Slack #general-engineering-qa: `C0ALJS0M2NR`
- Obsidian: `/Users/ctcreel/Library/Mobile Documents/iCloud~md~obsidian/Documents/The Agency`
