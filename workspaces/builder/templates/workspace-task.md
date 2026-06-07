# Workspace task — declarative agent configuration changes

You received a workspace-surface work item from triage. Your job is
to make a small, focused change to **the dispatching agent's
workspace files**: templates (`templates/*.md`), routing config
(`agency.yaml`), identity files (`identity/*.md`), or relation data
(`relations.json`). Open a PR; let the auto-merge gate decide whether
it ships without review.

## What you received

```
kind:                       workspace_task
work_item.surface:          workspace
work_item.summary:          {{ work_item.summary }}
work_item.detail:           {{ work_item.detail }}
work_item.issue_url:        {{ work_item.issue_url }}
work_item.kind:             {{ work_item.kind }}
work_item.severity:         {{ work_item.severity }}
work_item.idempotency_key:  {{ work_item.idempotency_key }}
```

Resolve the dispatching agent against the registry. For Winston-
originated work, the registry entry names the repo
(`ctcreel/winston-agency`), the `path` scope (`workspaces/winston/`),
the base branch, branch-naming pattern, reviewer, and verify command.

## Step 1 — Authenticate first, then clone into cwd

Mint a per-repo App token before any git/gh against that repo:

```
export GH_TOKEN=$(python3 -m agency_tools.github.app_token <repo>)
gh auth setup-git
```

Clone into your current working directory with no path arg:

```
gh repo clone <repo>
cd <repo-name>
```

Never clone to `/tmp/<anything>` or any path outside the ephemeral
cwd. The per-run teardown only reclaims what's inside cwd; an
out-of-cwd checkout leaks host disk (INC-20260529, daily-healthcheck
detects this).

## Step 2 — Read the issue + existing code

```
gh issue view {{ work_item.issue_url }} --json body --jq .body
```

The full spec is there. Don't rely on `work_item.detail` alone —
the detail is triage's summary; the issue body is the source of
truth.

Then read the files you're about to change. Templates: read the
whole file before editing; subtle Jinja patterns matter. Routing:
read the surrounding routing rules to match the existing shape.

## Step 3 — Make the change

Per-surface guidance:

### Templates (`workspaces/<agent>/templates/*.md`)

Templates render through minijinja on every run; every line costs
tokens, attention, and risk of priming. Follow the template-
authoring-standard contract (codified in
`winston-agency/openspec/changes/template-authoring-standard/`):

- **Positive instruction only.** Tell the LLM what to do, not what
  to avoid. The lint forbids `do not`, `don't`, `never`, `must
  not`, `without this`, `otherwise X happens`, `if you are reading
  this`, `skip if` in template bodies. (One allowed exception: a
  section literally headed `## Anti-patterns` near the end of the
  template; that section is a reference catalog, not a behavioral
  instruction.)
- **No incident history.** Dates, operator names, PR numbers,
  ticket IDs, "X caught this on YYYY-MM-DD" — none of that in the
  template body. The lint forbids it explicitly. Reasons for the
  change belong in the commit message and PR description.
- **Reference identity, don't duplicate it.** When a template
  needs an operator address, a team list, or a protocol, reference
  the identity file or `shared/` JSON; don't paste the content
  inline.
- **One Jinja variable per use.** If you find yourself writing
  `{{ x or y or z }}` you've smuggled three conditionals into a
  Jinja expression — extract the branching into an explicit step
  in the prose.

Lint locally before pushing:

```
bash scripts/lint-templates.sh
```

A clean lint is the ship gate for template-only changes. Any hit
blocks the PR until rewritten to positive framing.

### Routing (`workspaces/<agent>/agency.yaml`)

The YAML is loaded by the Rust runtime. Validate parsing before
pushing:

```
python3 -c 'import yaml; yaml.safe_load(open("workspaces/<agent>/agency.yaml"))'
```

Match the existing rule shape:

- `name:` is the route's stable identifier
- `condition:` is the matcher (look at adjacent rules for the shape)
- `messageTemplate:` is the path under `workspaces/<agent>/`
- `tools:` is the LLM-available allowlist; `preRunTools:` is the
  deterministic preRun list (those tools run from the runtime
  before the LLM prompt is assembled)
- `identity:` controls which identity files are loaded

The tools list is the security boundary: don't add a tool the LLM
shouldn't call. If the spec describes behavior the LLM should AVOID,
the structural fix is to leave the tool out of the list, not to add a
template warning.

### Identity files

Identity (`identity/IDENTITY.md`, `identity/SOUL.md`,
`identity/protocols/*.md`) is the agent's voice and reference
material. Changes here affect every run that loads the file. Be
conservative: small additions, not rewrites.

### Relations (`relations.json`)

A graph of entity → entity links. Edit by appending entries
matching the existing JSON shape. Never reformat the whole file in
a small-PR change.

## Step 4 — Auto-merge classification

Run `git diff --name-status main...HEAD` and check each line.

**Auto-merge eligible** when ALL hold:

- Every changed line is under the agent's `path` scope from the
  registry (e.g. `workspaces/winston/`)
- Only `M` lines (no files added or deleted)
- No changes to `agency.yaml` `tools:` blocks, `preRunTools:` blocks,
  routing rule names, identity file loads, or anything that defines
  an interface the agent exposes
- The `verifyCommand` ran clean

Templates and identity edits under the agent's path are typical
auto-merge candidates. Anything that touches a tool allowlist or
the runtime contract holds for review.

If review-required: `gh pr edit --add-reviewer <codeowners>` per
the registry and mark testable. Reviewer is named in the registry,
not in this template.

## Step 5 — Open the PR + emit the testable callback

```
gh pr create --draft \
  --title "<kebab-case-summary>" \
  --body "Refs {{ work_item.issue_url }}

<plan body, decisions log, open questions>" \
  --base <baseRef> --head <branch>
```

Run the verify command, mark the PR ready, then:

```
fire_builder_callback(
  state="testable",
  pr_url="<the PR URL>",
  auto_merge_eligible=<verdict>
)
```

If auto-merge eligible, also call `gh pr merge --squash --delete-branch`
before firing the callback.

## Anti-patterns

- **Cloning to /tmp.** The teardown only reclaims cwd. INC-20260529
  was 3GB of orphaned cargo target after exactly this; today's
  daily-healthcheck detects it but you're upstream of detection.
- **Lint-bypassing in the workspace surface.** The template lint is
  the ship gate. If you hit a violation in your edit, rewrite to
  positive framing; don't `|| true` it.
- **Pattern-by-pattern rewrites.** A `do not call gmail_search`
  warning often points at a tool that doesn't belong in the
  allowlist. Removing the tool from `tools:` is the structural fix;
  rephrasing the warning is the surface fix. Default to structural.
- **Editing live files on the host.** Always through a PR clone in
  cwd, never `sudo vim` on the running workspace dir.
