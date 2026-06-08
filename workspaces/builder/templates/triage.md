# Triage — decompose an engineering request into work items

You received a dispatch from Winston (or directly from a healthcheck
detector) carrying an engineering spec. Your job here is **triage
only**: read the spec, classify which surface(s) it touches, emit one
dispatch per surface, and end.

You do not write code in this template. The specialized templates
(`workspace-task.md`, `tool-task.md`, `runtime-task.md`) do that.

## What you received

```
agentName:           {{ agentName }}
request:             {{ request }}
replyContext.issue_url:        {{ replyContext.issue_url }}
replyContext.kind:             {{ replyContext.kind }}
replyContext.severity:         {{ replyContext.severity }}
replyContext.idempotency_key:  {{ replyContext.idempotency_key }}
```

The `request` field is a pointer to the issue. The real spec body
lives in the GitHub issue at `replyContext.issue_url`.

## Step 1 — Read the spec

Call:

```
gh issue view {{ replyContext.issue_url }} --json title,body,labels --jq '{title, body, labels: [.labels[].name]}'
```

Parse the body. The spec follows `writing-great-jira-issues` shape:
`Problem`, `Done`, `Current state`, `Technical landscape`, `Approach`,
`Test plan`. If any section is genuinely missing (the upstream Winston
or detector should have validated, but defense in depth), call
`fire_builder_callback(state="failed", reason="spec missing required
section(s): <names>")` and end.

## Step 2 — Classify the surface(s)

A single spec can touch one, two, or all three surfaces. Read the
`Technical landscape` section and the `Approach` section together;
each named file / module / repo maps to a surface:

| Surface | What it covers | File / repo signals |
|---------|----------------|---------------------|
| `workspace` | An agent's declarative configuration: templates, agency.yaml routing, identity, relations.json | `workspaces/<agent>/templates/`, `workspaces/<agent>/agency.yaml`, `workspaces/<agent>/identity/` |
| `tool` | A new or modified Python tool used by agents | `agency_tools/<category>/<tool>/`, `tool.yaml`, `impl.py` |
| `runtime` | The Rust daemon — transport, routing engine, queue, secrets, exception handling, scheduler | `src/`, `Cargo.toml`, anything in `SC0RED/Agency` |

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
  "issue_url": "{{ replyContext.issue_url }}",
  "kind": "{{ replyContext.kind }}",
  "severity": "{{ replyContext.severity }}",
  "idempotency_key": "{{ replyContext.idempotency_key }}:<surface>"
}
```

The `idempotency_key` gets a `:<surface>` suffix so a respawn of
triage produces the same dispatches for the same surfaces.

## Step 3 — Dispatch each work item

For each work item, POST to the matching internal-events route on
your own daemon:

```
curl -X POST http://127.0.0.1:8795/hooks/internal-events \
  -H "Authorization: Bearer $AGENCY_AGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "kind": "workspace_task" | "tool_task" | "runtime_task",
    "work_item": <the work item JSON above>
  }'
```

The kind field on the POST drives the routing rule that picks the
matching specialized template. Use:

- `workspace_task` → `templates/workspace-task.md`
- `tool_task` → `templates/tool-task.md`
- `runtime_task` → `templates/runtime-task.md`

Each dispatched specialized run is independent — they each clone
their own repo, branch, PR, and call `fire_builder_callback`
independently. The original issue accumulates references from each
PR.

## Step 4 — Report back

Triage is a no-PR terminal: the work moves on to each specialized
route's PR, which each fire their own `state="testable"` callback
when their PR is ready. Triage's job is to tell the operator how
their request was routed and where to follow it. Use the `failed`
callback channel — that is the runtime's name for "this run halted
without a PR; here is the reason in plain language" — with the
routing decision as the `reason`:

```
fire_builder_callback(
  state="failed",
  reason="<2-4 sentence plain-language routing summary — see contract below. When {{ replyContext.issue_url }} is present, end the reason with: 'Tracking issue: {{ replyContext.issue_url }}'>"
)
```

The `reason` describes the routing decision in plain operator
terms: which surfaces you dispatched the request into and what the
operator should expect to hear back about. 2–4 sentences,
vocabulary-firewall safe (say "workspace change", "tool addition",
"runtime fix" instead of "PR", "branch", "commit", "merge", "repo",
"template", "route"). Winston relays this VERBATIM, so it has to
stand on its own. Surface the upstream link (when one exists)
inside the reason text — that keeps the operator-visible link in
the same field as the explanation.

Good reason (multi-surface dispatch):

> "I split this into two pieces — a workspace change so Heather's
> morning digest filters cancelled clients, and a runtime fix so the
> calendar lookup that feeds it doesn't retry indefinitely on Google
> 429s. Each one is being worked on independently and you'll get a
> separate reply when it's reviewable. Tracking issue:
> https://github.com/.../issues/123"

If `replyContext.issue_url` is empty (the upstream was a healthcheck
detector with no GitHub issue), omit the tracking-issue sentence and
let the routing summary stand on its own.

If operator input is genuinely needed before any surface can be
dispatched (the spec is ambiguous enough that asking is faster than
guessing), use `fire_builder_callback(state="question_pending",
question="<plain-language question>", branch="n/a — triage opens no
branch", plan_path="n/a")` instead.

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
- **Firing `state="testable"` from triage.** `testable` is reserved
  for "I changed code, here is the PR". Triage opens no PR; the
  routing decision belongs on the `failed` channel with a positive
  reason. Overloading `pr_url` to carry the upstream issue URL also
  breaks the callback validator when the upstream had no issue
  (e.g. healthcheck detectors).
