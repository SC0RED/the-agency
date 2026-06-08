# Shared docs

Cross-agent prose every engineering agent references — the engineering
pipeline, anti-patterns, issue-writing guides, jira/github auth, TOOLS.md,
etc. Templates pull these in with `{{system-doc:<file>.md}}` (no
`shared/` prefix — see below).

## Directive shape: no `shared/` prefix

Pull a file in with `{{system-doc:anti-patterns.md}}` — the relative
path is resolved against the workspace directory first, then against
each entry in `systemDocRoots`. The leading `shared/` segment that the
previous deploy shape required is no longer needed (the sibling
directory IS `shared/`; adding the segment again would search
`../shared/shared/X.md`).

## Deployment shape: one copy per box

This is the canonical copy. At deploy time it is **rsynced once per box**
to `agency-workspaces/shared/`, as a sibling of every agent on that box.
Each consuming agent declares the sibling as an extra system-doc root in
its `agency.yaml`:

```yaml
systemDocRoots:
  - ../shared
```

The Agency runtime resolves `{{system-doc:shared/<file>.md}}` against
the workspace directory first, and falls back to `../shared/` for misses.
The per-root escape check still runs against each root independently —
see `openspec/changes/add-system-doc-roots/` in SC0RED/Agency for the
contract.

The per-agent inner `shared/` copy that the prior deploy pattern stamped
into every workspace is **gone**: shared docs live exactly once on disk
per box. On clawndom that saves ~140 KB per consuming agent; the bigger
win is that an update to a shared doc is visible to every consumer the
moment one rsync completes, with no per-agent drift risk.

## Do not symlink

The old pattern (`agency-workspaces/<agent>/shared -> ../shared`) is
gone. The Agency runtime enforces a symlink-escape check on workspace
reads:

```
ServiceError { kind: Configuration,
  detail: "system-doc path 'shared/<x>.md' rejected:
           resolves outside the configured root (symlink escape?)" }
```

A `shared -> ../shared` symlink escapes the workspace root and gets
rejected, so the agent fails to boot. Configure `systemDocRoots`
instead — it's the supported shape, and the per-root escape check keeps
its security guarantee in place.

## How it gets there

`make deploy-all` rsyncs every agent's workspace to its mapped host. For
every host where at least one deployed agent appears in the Makefile's
`AGENTS_USE_SHARED` list, the same pass also rsyncs this directory to
that host as a sibling (idempotent — patch and scarlett share one copy
on clawndom). `make deploy AGENT=<x>` does a single agent and pulls
shared if that agent opted in. `make deploy-shared HOST=<host>` syncs
just the sibling.

Two guards keep symlinks from coming back:

- `make no-symlinks` (run by `make check-all`, which the clawndom
  pre-commit gate invokes) fails on any symlink under `workspaces/`.
- The `No workspace symlinks` GitHub Action runs the same check on every
  push and PR.
