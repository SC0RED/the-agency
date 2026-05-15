.PHONY: check-all

# the-agency is a config / template / memory repo with no executable
# test suite of its own; the clawndom + agency-tools repos each carry
# their own check-all. This target exists so the clawndom-installed
# pre-commit gate has a no-op to invoke (matching the pattern in
# winston-agency).
check-all:
	@echo "the-agency: no executable checks — config + templates only"
