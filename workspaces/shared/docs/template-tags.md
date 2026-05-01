# Template tags — system vs body, and when to use which

Clawndom's template engine recognizes two tiers of doc-injection tags. The tier you choose decides whether the injected content participates in Anthropic's prompt cache or pays full input-token rates on every webhook firing.

(Throughout this doc, tags are written in prose form — `system-doc:<path>`, `shared:<path>`, etc. The actual template syntax wraps each one in double mustache braces, the same form Nunjucks uses; this doc avoids the literal braces because shared docs may be injected into templates and a literal mustache pair inside an injected doc gets parsed by the renderer.)

## The four tags

| Prose form | Resolves under | Where the content lands | Cacheable? |
|---|---|---|---|
| `system-doc:<path>` | this agent's workspace | `--system-prompt` (system slot) | **yes** — Anthropic prompt cache, 1h TTL |
| `system-shared:<path>` | `workspaces/shared/<path>` | `--system-prompt` (system slot) | **yes** |
| `doc:<path>` | this agent's workspace | rendered body (`-p` user prompt) | no |
| `shared:<path>` | `workspaces/shared/<path>` | rendered body (`-p` user prompt) | no |

## The decision rule

**Ask: would the rendered content be byte-identical between two runs of this template within the cache TTL window?**

- **Yes → `system-doc:` / `system-shared:`.** IDENTITY, SOUL, anti-patterns, estimation, the engineering pipeline, the writing-great-* guides, jira-ids-reference, jira-write-auth, jira-as-<agent>, github-access, TOOLS, hook-session-protocol — all stable across runs of the same template. Same bytes every render → cache hits on every run after the first within an hour.
- **No → `doc:` / `shared:`.** Anything that varies per webhook event: the rendered template body itself (Steps, payload table), Nunjucks expressions referencing the webhook payload (`issue.fields.*`, `payload.*`), memory-recall fragments, anything embedding event-specific values.

When in doubt, run the doc through this filter: open it and search for double-mustache Nunjucks expressions or any other render-time variables. If the rendered output varies between two `renderTemplate` calls of the same template, it's per-event content and belongs in the body tier.

## Why it matters

Anthropic's prompt cache engages on the system slot of the request — content passed via `claude --system-prompt`. Cached prefix reads cost ~10% of normal input-token rates with a 1-hour TTL by default (`ephemeral_1h_input_tokens`). For Patch's webhook patterns (multiple Jira transitions in a window) the cache warms naturally. Empirical numbers from SPE-1997 verification: a ~21K-token system prompt cost $0.13 cold on the first run and $0.011 warm on a second within the hour — a 91.6% drop on the cached portion.

Bytes that sit in the body (legacy `doc:` / `shared:`) pay full input-token rates every run, even when they're identical to the previous run. Anthropic's cache cannot reach them — the cache only sees the system slot.

## Anti-patterns

- **Per-event variables inside `system-*` content.** A doc that references render-time Nunjucks variables (the webhook payload, event metadata) will produce different bytes per run. The cache key changes; you pay the cache-write penalty without the read benefit. Net loss vs leaving it in the body. Keep these in `doc:` / `shared:`.
- **Reordering `system-*` tags between renders.** Anthropic's cache keys on the system-prompt prefix. The template engine concatenates `system-*` content in document order; reordering the tags between renders rotates the cache key. Pick an order and keep it.
- **Memory-recall fragments in `system-*`.** Memory retrieval results vary per run by design (the query depends on the event). They belong in the body. The two `system-*` directives are opt-in, not retroactive — leaving memory in `doc:` is correct.
- **Path-escape attempts.** A `system-shared:` path that resolves outside `workspaces/shared/` is rejected by the engine, same as `shared:`. The check is identical between the body and system tiers — there's no security difference, just a cache-eligibility difference.

## Migration checklist (when porting a new doc to `system-*`)

1. **Search the doc for double-mustache expressions.** If it has any literal Nunjucks expressions referencing payload-derived variables (e.g. `issue.fields.*`, `payload.*` wrapped in mustaches), it's per-event — leave it in `doc:` / `shared:`. The engine renders system content through Nunjucks too, so unrendered mustache literals inside an injected doc will be evaluated.
2. **Confirm the doc is template-stable, not run-stable.** Per-agent stable docs (IDENTITY, SOUL, jira-as-<agent>) only get cached when the *same agent's same template* runs again — that's still a cache hit on Patch's repeating Plan webhooks. Org-wide stable docs (anti-patterns, estimation) cache across templates of the same agent.
3. **Rename the tag in every template that injects it.** A mixed migration where one template uses `system-shared:` and another uses `shared:` for the same doc is fine — but within a single template, every reference to a stable doc should use the system tier.
4. **No content edits during the rename.** A pure tag rename keeps the diff mechanical and reviewable. Content edits go in a separate PR.

## Operational details

- **Engine:** `clawndom/src/lib/template/template-engine.ts` — `extractSystemTags` collects `system-*` content in document order and returns it alongside the rendered body. `RenderedTemplate = { systemPrompt, body }`.
- **Runner:** `claude-cli.runner.ts` joins per-run `systemPrompt` with any static `ClaudeCliRunnerConfig.systemPrompt` and forwards via `--system-prompt`. When the joined value is empty, the `--system-prompt` flag is omitted entirely (templates with no `system-*` tags render byte-identically before and after).
- **Verification:** `total_cost_usd` on the `result` event of the stream-json output reports the per-run cost. Bursty days should show second-and-later runs at a substantial discount versus the cold-cache run.
