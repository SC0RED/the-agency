.PHONY: check-all no-symlinks deploy deploy-shared deploy-all

# the-agency is a config / template / memory repo with no executable
# test suite of its own; the clawndom + agency-tools repos each carry
# their own check-all. This target exists so the clawndom-installed
# pre-commit gate has something to invoke (matching the pattern in
# winston-agency). We hang the workspace-symlink guard off it so the
# pre-commit gate catches a planted symlink before it can be committed.
check-all: no-symlinks
	@echo "the-agency: no executable checks — config + templates only"

# Shared docs are deployed as a REAL directory inside each agent's
# workspace (see workspaces/shared/README.md). The Agency runtime rejects
# any symlink whose target resolves outside the workspace root, so a
# committed `shared -> ../shared` symlink breaks the agent on boot
# ("symlink escape?"). Fail loudly if anyone reintroduces a symlink
# anywhere under workspaces/.
no-symlinks:
	@found=$$(find workspaces -type l); \
	if [ -n "$$found" ]; then \
		echo "ERROR: symlink(s) found under workspaces/ — the Agency runtime"; \
		echo "rejects symlinks that escape the workspace root. Deploy shared"; \
		echo "docs as a real directory (make deploy) instead. Offending paths:"; \
		echo "$$found"; \
		exit 1; \
	fi; \
	echo "no-symlinks: OK — no symlinks under workspaces/"

# Deploy an agent's workspace to its box. Shared docs live ONCE per box
# as a sibling of every agent that opted in via `systemDocRoots:
# [../shared]` in its `agency.yaml` — see
# `openspec/changes/add-system-doc-roots/` in SC0RED/Agency and
# `workspaces/shared/README.md` for the contract.
#
#   make deploy-all              # every agent to its box (use this)
#   make deploy-all DRY_RUN=1    # preview every agent, no writes
#   make deploy AGENT=patch      # one agent; host resolved from the map
#   make deploy AGENT=builder HOST=winston-agent   # explicit host override
#   make deploy-shared HOST=clawndom               # just the sibling shared dir
#
# The fleet's knowledge of WHICH AGENT LIVES WHERE belongs here, not in an
# operator's head — that memory dependency is what broke the box. To add an
# agent: drop its workspace under workspaces/, add it to AGENTS, map it
# to a host below, and (if it references `{{system-doc:shared/...}}`)
# include it in AGENTS_USE_SHARED. `make deploy-all` carries it automatically.
AGENTS := patch scarlett builder
HOST_patch    := clawndom
HOST_scarlett := clawndom
HOST_builder  := winston-agent

# Agents whose templates reference shared docs (`{{system-doc:shared/X}}`).
# Each such agent's `agency.yaml` MUST declare `systemDocRoots: [../shared]`
# so the runtime knows to consult the sibling. `make deploy AGENT=<x>` for
# any agent in this list pulls the sibling shared dir to that agent's box
# in the same pass.
AGENTS_USE_SHARED := patch scarlett

# HOST defaults to the agent's mapped host; pass HOST=... to override (or
# HOST= empty + DEST=/tmp/... for a local dry-run with no ssh).
HOST ?= $(HOST_$(AGENT))

DEFAULT_DEST := /home/ubuntu/agency-workspaces
DEST ?= $(DEFAULT_DEST)
RSYNC_EXCLUDES := --exclude='.DS_Store' --exclude='._*' --exclude='.AppleDouble' \
	--exclude='__pycache__/' --exclude='*.pyc' --exclude='.openclaw/'
RSYNC := rsync -a$(if $(DRY_RUN),n)v
TARGET = $(if $(HOST),$(HOST):)$(DEST)/$(AGENT)
SHARED_TARGET = $(if $(HOST),$(HOST):)$(DEST)/shared

# Deploy every agent to its mapped host. One command, no per-agent memory.
deploy-all:
	@for a in $(AGENTS); do \
		$(MAKE) --no-print-directory deploy AGENT=$$a DRY_RUN=$(DRY_RUN) DEST=$(DEST) || exit 1; \
	done

deploy:
	@test -n "$(AGENT)" || { echo "usage: make deploy AGENT=<$(AGENTS)> [HOST=<host>]   (or: make deploy-all)"; exit 1; }
	@test -d "workspaces/$(AGENT)" || { echo "no such workspace: workspaces/$(AGENT)"; exit 1; }
	@if [ -z "$(HOST)" ] && [ "$(DEST)" = "$(DEFAULT_DEST)" ]; then \
		echo "no host mapped for AGENT=$(AGENT) — refusing to deploy to a prod path locally."; \
		echo "add HOST_$(AGENT) to the Makefile, or pass HOST=<host>."; \
		exit 1; \
	fi
	@echo "==> deploying $(AGENT) to $(TARGET)$(if $(DRY_RUN), [DRY RUN])"
	# Agent workspace only — no inner shared/ for agents that consume the
	# sibling. --delete keeps the box clean of stale templates.
	$(RSYNC) --delete $(RSYNC_EXCLUDES) \
		workspaces/$(AGENT)/ $(TARGET)/
	# Pull the sibling shared dir for agents that opted into the runtime
	# `systemDocRoots: [../shared]` resolution. Idempotent — deploying
	# patch and scarlett to the same box stages shared/ once.
	@if echo " $(AGENTS_USE_SHARED) " | grep -q " $(AGENT) "; then \
		$(MAKE) --no-print-directory deploy-shared HOST=$(HOST) DEST=$(DEST) DRY_RUN=$(DRY_RUN); \
	fi
	@echo "==> done: $(AGENT)"

# Sync the sibling `shared/` directory to the box (one copy per host,
# consumed by every agent on that host whose yaml lists `../shared` in
# `systemDocRoots`). NO --delete: a partial deploy can never blow away
# docs that aren't in this manifest.
deploy-shared:
	@if [ -z "$(HOST)" ] && [ "$(DEST)" = "$(DEFAULT_DEST)" ]; then \
		echo "usage: make deploy-shared HOST=<host>   (or DEST=/tmp/... for local dry-run)"; \
		exit 1; \
	fi
	@echo "==> staging shared/ at $(SHARED_TARGET)$(if $(DRY_RUN), [DRY RUN])"
	$(RSYNC) $(RSYNC_EXCLUDES) workspaces/shared/ $(SHARED_TARGET)/
