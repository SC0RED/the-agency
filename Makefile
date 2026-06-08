.PHONY: check-all no-symlinks deploy deploy-all

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

# Deploy an agent's workspace to its box, then materialize the shared
# docs as a REAL directory inside it — never a symlink (see
# workspaces/shared/README.md).
#
#   make deploy-all              # every agent to its box (use this)
#   make deploy-all DRY_RUN=1    # preview every agent, no writes
#   make deploy AGENT=patch      # one agent; host resolved from the map
#   make deploy AGENT=builder HOST=winston-agent   # explicit host override
#
# The fleet's knowledge of WHICH AGENT LIVES WHERE belongs here, not in an
# operator's head — that memory dependency is what broke the box. To add an
# agent: drop its workspace under workspaces/, add it to AGENTS, and map it
# to a host below. `make deploy-all` then carries it automatically.
AGENTS := patch scarlett builder
HOST_patch    := clawndom
HOST_scarlett := clawndom
HOST_builder  := winston-agent

# HOST defaults to the agent's mapped host; pass HOST=... to override (or
# HOST= empty + DEST=/tmp/... for a local dry-run with no ssh).
HOST ?= $(HOST_$(AGENT))

DEFAULT_DEST := /home/ubuntu/agency-workspaces
DEST ?= $(DEFAULT_DEST)
RSYNC_EXCLUDES := --exclude='.DS_Store' --exclude='._*' --exclude='.AppleDouble' \
	--exclude='__pycache__/' --exclude='*.pyc' --exclude='.openclaw/'
RSYNC := rsync -a$(if $(DRY_RUN),n)v
TARGET = $(if $(HOST),$(HOST):)$(DEST)/$(AGENT)

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
	# Agent workspace: --delete keeps the box clean, but exclude shared/ so
	# this pass never touches the shared docs.
	$(RSYNC) --delete $(RSYNC_EXCLUDES) --exclude='shared/' \
		workspaces/$(AGENT)/ $(TARGET)/
	# Shared docs: copied in as a real directory. NO --delete here, so a
	# partial deploy can never blow away docs that aren't in this manifest.
	$(RSYNC) $(RSYNC_EXCLUDES) \
		workspaces/shared/ $(TARGET)/shared/
	@echo "==> done: $(AGENT) (shared/ materialized as a real directory)"
