# Runtime task: Rust daemon changes in SC0RED/Agency

You received a runtime-surface work item from triage. Your job is to
make a focused change to the Rust Agency daemon: transport, routing
engine, queue, secrets, exception handling, scheduler, dashboard.
Runtime PRs are high blast-radius (one binary runs every agent on
both EC2 boxes), always review-required.

## Intent

**Purpose:** Make a focused, review-required change to the Rust Agency daemon (transport, routing engine, queue, secrets, scheduler, dashboard), cloning only into cwd, and open a non-auto-merge PR for the codeowners reviewer.
**Success:** The disk precheck passes before cloning; `make check` runs clean locally; the PR is opened with `auto_merge_eligible=false`, the codeowners reviewer requested, and disk readings captured in the body.

---

## What you received

```
kind:                       runtime_task
work_item.surface:          runtime
work_item.summary:          {{ work_item.summary | default("") }}
work_item.detail:           {{ work_item.detail | default("") }}
work_item.issue_url:        {{ work_item.issue_url | default("") }}
work_item.kind:             {{ work_item.kind | default("") }}
work_item.severity:         {{ work_item.severity | default("") }}
work_item.idempotency_key:  {{ work_item.idempotency_key | default("") }}
```

## Step 1: Disk-space precheck

The runtime repo's `target/` directory grows to ~1.5-2GB on every
`make check`. INC-20260529 was a stop-writes Redis outage caused by
cargo target leaking out of an ephemeral cwd onto the production
volume. The daily-healthcheck detects this leak class today, but
you're upstream of detection, handle disk yourself.

Before cloning:

```
df -h / | awk 'NR==2 {print "available: " $4}'
```

If `available` is under 5GB, abort with a `fire_builder_callback(
state="failed", reason="insufficient disk for runtime build:
<usage>")` and end. Do not proceed; you'll cause the next outage.

## Step 2: Authenticate first, then clone into cwd

Mint a per-repo App token before any git/gh:

```
export GH_TOKEN=$(python3 -m agency_tools.github.app_token SC0RED/Agency)
gh auth setup-git
gh repo clone SC0RED/Agency
cd Agency
```

Clone into the ephemeral cwd. Never to `/tmp/<anything>`. Never to
`~/Agency-fix`. Never anywhere outside cwd. The teardown only
reclaims cwd; an out-of-cwd checkout plus its `target/` survives
the run. Cwd-only is non-negotiable for this surface.

## Step 3: Read the spec + map the territory

```
gh issue view {{ work_item.issue_url | default("") }} --json body --jq .body
```

The spec's `Technical landscape` section should name the modules
involved. Map them to the repo's layout:

| Concern | Module |
|---------|--------|
| HTTP routes (inbound webhooks, admin endpoints) | `src/http/*.rs` |
| Routing engine (rule matching, condition evaluation) | `src/routing/*.rs` |
| Tool bridge (Python subprocess invocation, env injection) | `src/tools/bridge.rs` |
| Event store / event sink | `src/events/*.rs` |
| Runners (Claude CLI, ephemeral dir lifecycle) | `src/runners/*.rs` |
| Scheduler (cron rule firing) | `src/schedule/*.rs` |
| Secrets resolution (1Password, env files) | `src/secrets/*.rs` |
| Exception watcher | `src/events/exception_handler.rs` |
| Dashboard | `src/http/dashboard/*.rs` |

Read the affected modules end-to-end before editing. Runtime code
has invariants that aren't obvious from a single file (e.g. the
ephemeral.rs Drop must reclaim the cwd for the per-run cleanup
contract to hold; an "improvement" that delays cleanup breaks the
invariant).

## Step 4: Make the change

Patterns:

- **No defensive Option fallthrough on init.** Use
  `LazyLock<T>` with `process::abort()` on impossible init failure
  rather than `LazyLock<Option<T>>` that silently degrades. The
  exception watcher Normalizer is the canonical example.
- **Use sqlx for DB access.** The events table and watermark tables
  are PostgreSQL via sqlx. Compile-time-checked queries are
  preferred; runtime-only queries get a clear comment naming why.
- **Tokio broadcast for internal events.** The exception watcher /
  internal-event subscriber pattern uses `tokio::sync::broadcast`
  for fan-out within the daemon. Per-subscriber retention is
  bounded; lagging subscribers are dropped without panicking.
- **No `unwrap()` on operator-facing paths.** Internal invariants
  use `expect("...")` with a descriptive message. Operator-facing
  paths (HTTP handlers, scheduled rule firing) return structured
  errors.
- **Function cap.** Same rule as other surfaces: decompose helpers
  rather than growing one function past 50 lines.

## Step 5: Verify locally (full make check)

The verify command for the runtime repo is `make check`. This runs:

- `cargo fmt --check`
- `cargo clippy -- -D warnings`
- `cargo test`
- `cargo deny check`
- 90% line-coverage gate (writes `lcov.info` for SonarQube)

Run it:

```
make check
```

A clean `make check` is the gate for marking testable. If you mark a
PR testable with a failing make check, you'll burn the merge cycle
when CI catches it. Run it locally; fix; mark testable.

**Disk note:** cargo's incremental cache grows. If `du -sh target/`
is over 3GB at the end of a run, the next run's `make check` may
hit ENOSPC. The daily-healthcheck flags this; you don't need to
hand-prune mid-run.

## Step 6: Auto-merge classification

Runtime PRs are **always review-required**. The auto-merge gate's
"path under agent scope" check doesn't apply here, the runtime is
shared across all agents. The auto-merge gate is structurally
disabled for this surface in the registry; passing
`auto_merge_eligible=false` is the only correct call.

Request the registry's `codeOwners` reviewer:

```
gh pr edit <pr-number> --add-reviewer <handle>
```

## Step 7: Open the PR

```
gh pr create --draft \
  --title "feat(<module>): <one-line summary>" \
  --body "Closes {{ work_item.issue_url | default("") }}

## Summary
<2-4 bullets>

## Test plan
- [x] make check clean locally
- [x] <any integration scenarios exercised>

## Disk usage
target/ size: <reading from \`du -sh target\`>
host disk usage: <reading from \`df -h /\`>"
```

Then `gh pr ready` and:

```
fire_builder_callback(
  state="testable",
  pr_url="<the PR URL>",
  summary="<2-4 sentences, plain language, see contract below>",
  auto_merge_eligible=false
)
```

The `summary` contract: 2-4 sentences, vocabulary-firewall safe
(no "PR", "branch", "commit", "merge", "repo", filenames, identifier
names). Winston relays it VERBATIM to the operator. Runtime changes
are often invisible to the operator (latency, reliability, infra),
so anchor on the user-visible symptom your change resolves or
prevents. Always `auto_merge_eligible=false` for runtime changes,
so the summary always lands in a reviewer email alongside the PR link.

Good summary (runtime fix):

> "Patches were occasionally retrying themselves silently after a
> Postgres blip, which left duplicate Jira comments on the same
> issue. The retry path now treats the blip as a transient error
> and waits for the next webhook instead of re-running. Existing
> work-in-flight is not affected."

## Step 8: Post-PR disk check

Before exiting, capture the final state:

```
du -sh target/
df -h /
```

Include the readings in the PR body's "Disk usage" section above.
This makes leak-pattern regressions traceable from PR history.

## Anti-patterns

- **Cloning anywhere except cwd.** INC-20260529 was 3GB of
  orphaned cargo target after exactly this. Daily-healthcheck
  detects the leak today, but you're upstream of detection. Cwd
  only.
- **Bypassing `make check`.** The gate exists because runtime
  bugs are observable across every agent on every fire. A "lint
  is whining about one thing" message in PR review is the gate
  working as designed; rewrite the offending line.
- **Defensive null-checks against internal Rust types.** Rust's
  type system eliminates most of those checks; a `match Some(_) =>
  ..., None => panic!()` on a value guaranteed `Some` by the
  surrounding code is dead code.
- **`unwrap()` on HTTP-handler paths.** Operator-facing paths use
  `?` + a typed error; `unwrap` is for internal contracts.
