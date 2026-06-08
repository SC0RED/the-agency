# Shared docs

Cross-agent prose every engineering agent references — the engineering
pipeline, anti-patterns, issue-writing guides, jira/github auth, TOOLS.md,
etc. Templates pull these in with `{{system-doc:shared/<file>.md}}`, which
resolves relative to the agent's own workspace root.

## Deploy as a real directory — never a symlink

This is the canonical copy. At deploy time it is **copied into each agent's
workspace as a real directory** (`agency-workspaces/<agent>/shared/`), so
every workspace sees the docs at `shared/` without a second copy in source.

**Do not symlink.** The old pattern (`agency-workspaces/<agent>/shared ->
../shared`) is gone. The Agency runtime enforces a symlink-escape check on
workspace reads: any symlink whose target resolves outside the workspace
root is rejected —

```
ServiceError { kind: Configuration,
  detail: "system-doc path 'shared/<x>.md' rejected:
           resolves outside the configured root (symlink escape?)" }
```

That rejection is a **feature** — it stops a planted symlink in a template
from reading `/etc/passwd`. A `shared -> ../shared` symlink escapes the
workspace root and gets rejected, so the agent fails to boot.

## How it gets there

`make deploy-all` rsyncs every agent's workspace to its mapped host, then
copies this directory into each as a real `shared/`. The agent→host map
lives in the repo-root `Makefile` (not in anyone's head), so adding an
agent is a one-line edit, not a thing to remember. `make deploy AGENT=<x>`
does a single agent; `DRY_RUN=1` previews without writing.

Two guards keep symlinks from coming back:

- `make no-symlinks` (run by `make check-all`, which the clawndom
  pre-commit gate invokes) fails on any symlink under `workspaces/`.
- The `No workspace symlinks` GitHub Action runs the same check on every
  push and PR.
