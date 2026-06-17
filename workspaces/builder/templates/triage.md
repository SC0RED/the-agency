# Triage: decompose an engineering request into work items

You received a dispatch from Winston (or directly from a healthcheck
detector) carrying an engineering spec. Your job here is **triage
only**: read the spec, classify which surface(s) it touches, emit one
dispatch per surface, and end.

You do not write code in this template. The specialized templates
(`workspace-task.md`, `tool-task.md`, `runtime-task.md`) do that.

## Intent

**Purpose:** Classify an inbound engineering spec into the surface(s) it touches (workspace / tool / runtime) and dispatch one work item per surface to the matching specialized route, leaving the code to those routes.
**Success:** The prior-PR dedup check runs first; each surface the spec touches gets exactly one work item with a `:<surface>`-suffixed idempotency key dispatched to the right `kind` route; a plain-language routing summary fires via `fire_builder_callback`.

---

## What you received

```
agentName:           {{ agentName }}
request:             {{ request }}
replyContext.issue_url:        {{ replyContext.issue_url | default("") }}
replyContext.kind:             {{ replyContext.kind | default("") }}
replyContext.severity:         {{ replyContext.severity | default("") }}
replyContext.idempotency_key:  {{ replyContext.idempotency_key | default("") }}
```

The `request` field is a pointer to the issue. The real spec body
lives in the GitHub issue at `replyContext.issue_url`.

## Step 0: Have you already shipped a PR for this?

Before decomposing, check whether you've already addressed this same
work. The exception-watcher dedups within its window, but window
boundaries do expire and the same fingerprint can re-fire, opening a
parallel fix wastes work and pollutes the PR queue.

Call `github_search_prs` with a query that targets the distinctive
identifier from the spec. For exception-watcher dispatches the
fingerprint is the strongest signal:

```
github_search_prs(query='"{{ replyContext.fingerprint | default("") }}" org:SC0RED')
```

For operator-initiated dispatches without a fingerprint, search on the
distinctive phrase from the spec:

```
github_search_prs(query='"<verbatim tool name or error message>" org:SC0RED is:closed')
```

If `total_count > 0` and any item's body references the same
fingerprint or describes the same symptom, short-circuit:

```
fire_builder_callback(
  state="failed",
  reason="Already shipped. See <html_url>. <one-line of how the prior PR addresses this>."
)
```

Then end the run. Don't decompose. Don't dispatch.

If no prior PR matches, continue to Step 1.

## Step 1: Read the spec

Call:

```
gh issue view {{ replyContext.issue_url | default("") }} --json title,body,labels --jq '{title, body, labels: [.labels[].name]}'
```

Parse the body. The spec follows `writing-great-jira-issues` shape:
`Problem`, `Done`, `Current state`, `Technical landscape`, `Approach`,
`Test plan`. If any section is genuinely missing (the upstream Winston
or detector should have validated, but defense in depth), call
`fire_builder_callback(state="failed", reason="spec missing required
section(s): <names>")` and end.

## Step 2: Classify the surface(s)

A single spec can touch one, two, or all three surfaces. Read the
`Technical landscape` section and the `Approach` section together;
each named file / module / repo maps to a surface:

| Surface | What it covers | File / repo signals |
|---------|----------------|---------------------|
| `workspace` | An agent's declarative configuration: templates, agency.yaml routing, identity, relations.json | `workspaces/<agent>/templates/`, `workspaces/<agent>/agency.yaml`, `workspaces/<agent>/identity/` |
| `tool` | A new or modified Python tool used by agents | `agency_tools/<category>/<tool>/`, `tool.yaml`, `impl.py` |
| `runtime` | The Rust daemon: transport, routing engine, queue, secrets, exception handling, scheduler | `src/`, `Cargo.toml`, anything in `SC0RED/Agency` |

Default heuristics:

- A **prompt / behavioral** change → `workspace` (text in a template,
  identity rewrite, a route rule rewording)
- A **new capability** the agent doesn't have yet (sending email,
  reading a doc, calling an API) → `tool` IF the capability requires
  code, OR `workspace` if it's already a tool the agent isn't using
- A **scheduler change** (cron timing, new schedule rule, runner
  model) → `workspace` (declarative in agency.yaml)
- A **runtime feature** (a new event type, a new HTTP route, the
  exception watcher behavior, queue semantics) → `runtime`

A spec frequently mixes: e.g. "add a Saturday reminder" needs a new
schedule rule (workspace) AND maybe a new tool to format the
reminder (tool). Decompose accordingly.

For each surface that the spec touches, produce one work item:

```json
{
  "surface": "workspace" | "tool" | "runtime",
  "summary": "<one-line title for the work item, max 80 chars>",
  "detail": "<2-5 sentence description of what THIS surface owns in this spec>",
  "issue_url": "{{ replyContext.issue_url | default("") }}",
  "kind": "{{ replyContext.kind | default("") }}",
  "severity": "{{ replyContext.severity | default("") }}",
  "idempotency_key": "{{ replyContext.idempotency_key | default("") }}:<surface>"
}
```

The `idempotency_key` gets a `:<surface>` suffix so a respawn of
triage produces the same dispatches for the same surfaces.

## Step 3: Dispatch each work item

For each work item, POST to the matching internal-events route on
your own daemon. Include the `replyContext` you received so the
specialized run can call back to the operator who started this:

```
curl -X POST http://127.0.0.1:8795/hooks/internal-events \
  -H "Authorization: Bearer $AGENCY_AGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "kind": "workspace_task" | "tool_task" | "runtime_task",
    "work_item": <the work item JSON above>,
    "replyContext": {{ replyContext | tojson }}
  }'
```

The `kind` field drives the routing rule that picks the matching
specialized template. Use:

- `workspace_task` → `templates/workspace-task.md`
- `tool_task` → `templates/tool-task.md`
- `runtime_task` → `templates/runtime-task.md`

The `replyContext` is what makes the specialized run's
`fire_builder_callback` reach the right operator. Without it, the
runtime can't materialize the per-run context dir and the callback
errors with `BUILDER_CONTEXT_DIR is not set`. Pass through whatever
you received; the runtime mints a fresh `jobId` for the dispatched
run automatically.

Each dispatched specialized run is independent: they each clone
their own repo, branch, PR, and call `fire_builder_callback`
independently. The original issue accumulates references from each
PR.

## Step 4: Report back

After all dispatches succeed, call:

```
fire_builder_callback(
  state="testable",
  pr_url="{{ replyContext.issue_url | default("") }}",
  summary="<2-4 sentences: what you decomposed the request into and what the operator should expect next>",
  auto_merge_eligible=false
)
```

The `pr_url` field is reused to carry the issue URL here so the relay
back to Winston (or the healthcheck dashboard) gets the operator-visible
link. Auto-merge is always `false` for triage; the actual auto-merge
gate runs in each specialized route's PR.

The `summary` describes the routing decision in plain operator terms:
which surfaces you dispatched the request into and what the operator
should expect to hear back about. 2–4 sentences, vocabulary-firewall
safe (no "PR", "branch", "commit", "merge", "repo", "template",
"route", say "workspace change", "tool addition", "runtime fix"
instead). Winston relays this VERBATIM, so it has to stand on its own.

Good summary (multi-surface dispatch):

> "I split this into two pieces: a workspace change so Heather's
> morning digest filters cancelled clients, and a runtime fix so the
> calendar lookup that feeds it doesn't retry indefinitely on Google
> 429s. Each one is being worked on independently and you'll get a
> separate reply when it's reviewable."

If any dispatch fails (5xx, network), call
`fire_builder_callback(state="failed", reason="dispatch to <surface>
route failed: <error>")` and end.

## Anti-patterns

- **Writing code in this template.** Triage doesn't touch git. It
  reads the issue, decomposes, dispatches. The specialized
  templates handle the rest.
- **Single-surface bias.** A spec saying "add a Saturday reminder"
  often needs both a tool (formatter) and a workspace change
  (schedule rule). Read all six sections before committing to a
  count.
- **Over-decomposition.** A change wholly contained in one
  template file is one workspace work item, not three (Problem →
  template / Done → template / Current state → template).
- **Skipping the spec read.** The `request` field is a one-line
  pointer; the actual spec is in the issue body. Read the issue
  before classifying.
