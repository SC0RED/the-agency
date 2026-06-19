# Tool task: forge or modify a Python tool in agency-tools

You received a tool-surface work item from triage. Your job is to
forge a new tool, or modify an existing one, in `SC0RED/agency-tools`.
A tool is a Python module at `agency_tools/<category>/<name>/` with
`tool.yaml` (the contract) and `impl.py` (the implementation), plus
unit tests.

## Intent

**Purpose:** Forge a new Python tool, or modify an existing one, in agency-tools, with its contract, implementation, and tests, then open a PR.
**Success:** `tool.yaml` carries a clear When-to-call / When-NOT-to-call contract; `impl.py` returns a structured dict using the package's `_identity` and `urllib` patterns; every happy-path and error branch is tested and `make test` (or `pytest`) runs clean.

---

## What you received

```
kind:                       tool_task
work_item.surface:          tool
work_item.summary:          {{ work_item.summary | default("") }}
work_item.detail:           {{ work_item.detail | default("") }}
work_item.issue_url:        {{ work_item.issue_url | default("") }}
work_item.kind:             {{ work_item.kind | default("") }}
work_item.severity:         {{ work_item.severity | default("") }}
work_item.idempotency_key:  {{ work_item.idempotency_key | default("") }}
```

## Step 1: Authenticate first, then clone into cwd

Mint a per-repo App token before any git/gh:

```
export GH_TOKEN=$(python3 -m agency_tools.github.app_token SC0RED/agency-tools)
gh auth setup-git
gh repo clone SC0RED/agency-tools
cd agency-tools
```

Clone into the ephemeral cwd; never to `/tmp/<anything>` or any
absolute path outside cwd (INC-20260529, the teardown only
reclaims what's inside cwd, and a cargo / pytest cache outside
cwd is a multi-GB leak).

## Step 2: Read the spec + the closest sibling tool

```
gh issue view {{ work_item.issue_url | default("") }} --json body --jq .body
```

Then pick the closest existing tool to your target shape and read it
end-to-end. The package follows a strict per-directory pattern:

- `agency_tools/<category>/<tool_name>/`
- `tool.yaml`: name, description, args, secrets
- `impl.py`: `invoke(*, ...) -> dict` is the entry point
- `__init__.py`: re-exports `invoke`
- `tests/test_<tool_name>.py`: covers the impl

Categories (existing): `google` (Gmail/Calendar/Drive), `github`,
`slack`, `calendly`, `twilio`, `zoom`, `xero`, `stripe`, `entity`,
`memory`, `scheduled_tasks`, `recovery`, `predicate`, etc. A new
category is created only when the new tool genuinely doesn't fit any
existing one.

## Step 3: Design the contract first (`tool.yaml`)

`tool.yaml` IS the contract. The LLM sees this on every run that
loads the tool; everything in it costs tokens, attention, and
shapes call behavior. Optimize for clarity:

- **`description`**: a long-form description with the When-to-call
  / When-NOT-to-call / Argument shapes pattern (see existing tools
  for the canonical shape). The When-NOT-to-call section is the most
  load-bearing: it prevents the model from misusing the tool when a
  better tool exists.
- **`args`**: every arg gets a `type:` and a `description:` that
  states the structural contract (e.g. "Repo in `owner/name` form").
  Optional args get `optional: true`. Do not encode behavior
  decisions in arg defaults: make the caller choose.
- **`secrets`**: list the env vars the runtime should resolve into
  this arg from secrets storage. The first env in the list wins;
  fallbacks come next. `agent_token` is the standard arg name for
  the calling agent's bearer credential.

## Step 4: Build impl.py

Patterns the package depends on:

- **Read env via `_identity` helpers**: never `os.environ["X"]`
  directly for runtime contract vars (`AGENCY_AGENT_TOKEN`,
  `AGENCY_REQUEST_ID`, `AGENCY_AGENT_ID`). Use
  `agency_tools._identity.calling_agent_token()` etc. The helpers
  raise a clear `RuntimeError` when an env is missing instead of
  the opaque `KeyError` a direct read produces.
- **HTTP via stdlib `urllib`, not third-party `requests`**: the
  package keeps its dependency surface minimal. The `github/_http.py`
  helper is the model.
- **Function size ≤ 50 lines**: the codebase has a hard cap (see
  the linter config). Decompose helpers liberally.
- **No defensive code against internal contracts**: internal
  callers are trusted. Validate at system boundaries (user input,
  external APIs); inside the package, let bad data fail loudly.
- **No silent error swallowing**: every `except` either re-raises
  or returns a result with a structured `reason` field naming the
  failure mode.

The shape of `invoke`:

```python
def invoke(
    *,
    arg_1,
    arg_2,
    agent_token,  # standard last; injected by the runtime from secrets
    optional_arg=None,
) -> dict[str, Any]:
    ...
    return {"<structured result>": ...}
```

Return a dict whose keys document the result. Never return naked
strings or ints, downstream callers parse the dict.

## Step 5: Tests (`tests/test_<tool_name>.py`)

Required coverage:

- **Happy path**: the call returns the expected result
- **Every error branch**: each `return {"reason": "..."}` path
  has a test
- **External calls mocked**: `mock.patch.object(impl, "_request")`
  or equivalent; tests must not hit real HTTP

Run locally before pushing:

```
PYTHONPATH=. python3 -m pytest tests/test_<tool_name>.py -v
```

## Step 6: Auto-merge classification

Tool changes are almost always review-required: a new tool is a new
capability the agent exposes; modifying an existing tool changes the
contract every caller depends on. The auto-merge gate (registry
`verifyCommand` clean + only `M` lines under the agent's path) does
not apply to tool work: there is no per-agent path scope; tools
serve every agent.

Mark testable with `auto_merge_eligible=false` and request the
registry's `codeOwners` reviewer.

## Step 7: Open the PR

```
gh pr create --draft \
  --title "feat(<category>): <one-line summary>" \
  --body "Closes {{ work_item.issue_url | default("") }}

## Summary

<2-4 bullets>

## Tests

<count of test cases>; \`make test\` or \`pytest tests/test_<name>.py\` clean."
```

Run `make test` (or the registry's `verifyCommand`), then
`gh pr ready`, then:

```
fire_builder_callback(
  state="testable",
  pr_url="<the PR URL>",
  summary="<2-4 sentences, plain language, what new capability this gives the operator>",
  auto_merge_eligible=false
)
```

The `summary` contract: 2–4 sentences, vocabulary-firewall safe (no
"PR", "branch", "commit", "merge", "repo", filenames, identifier
names). Winston relays it VERBATIM to the operator, so describe the
new capability in terms a non-engineer can act on. Tool tasks always
ship with `auto_merge_eligible=false`, so the summary lands in a
reviewer email alongside the PR link.

Good summary (tool addition):

> "Winston can now look up which clinician owns a Google calendar
> event without you having to tell him. He reads the event's host
> directly from the calendar, so eval intakes coming off Bethany's
> calendar get routed to Bethany automatically."

## Anti-patterns

- **Adding third-party deps for stdlib-solvable problems.** `urllib`
  handles 90% of what the package needs. `requests` only appears in
  tools that genuinely need its multipart / session features.
- **Wrapping every call in try/except RuntimeError**. Trust internal
  contracts; let `_identity` errors surface as the contract
  violations they are.
- **A tool that wraps another tool with no value-add.** If your new
  tool is just `existing_tool(...)` plus a constant arg, the right
  fix is a workspace-level prompt update so the agent calls the
  existing tool correctly.
- **Cloning to /tmp.** Always cwd. INC-20260529.
