# GitHub access — cloning and pushing from the EC2

The EC2 has a GitHub App (`sc0red-patch`, install id `125627395`) with Contents + Pull Requests read/write on `SC0RED/Platform-Frontend`, `SC0RED/Platform-Backend`, `SC0RED/assessment_engine`. The install token is short-lived (1 hour) — generate a fresh one at the start of every task.

## Generating a token

From Patch's workspace directory, the script is at `../shared/tools/generate-github-app-token.sh`:

```bash
export GH_TOKEN=$(bash ../shared/tools/generate-github-app-token.sh)
```

If you expect to work longer than an hour, re-run the one-liner before the next `git push` or `gh` call — tokens don't auto-refresh.

## Cloning a private SC0RED repo

`/tmp` is your scratch space (`PrivateTmp=true` on the systemd unit — wiped on restart, isolated from other services).

```bash
cd /tmp && rm -rf Platform-Frontend
git clone https://x-access-token:${GH_TOKEN}@github.com/SC0RED/Platform-Frontend.git
cd Platform-Frontend
```

Swap `Platform-Frontend` for whichever of the three repos the task touches. Multi-repo tasks clone each in turn.

## Keeping clones fresh

`/tmp` is `PrivateTmp=true` on the clawndom systemd unit — scratched only when the service restarts, **not** between hook-triggered subprocesses. That means repos in `/tmp` can be days old from a previous run. Stale code leads to stale investigations: a bug already fixed in `development` can waste an entire Plan cycle.

**Before reading code in any task, refresh the target repo.** Idempotent pattern — clone if absent, hard-reset to `origin/development` if present:

```bash
export GH_TOKEN=$(bash ../shared/tools/generate-github-app-token.sh)
REPO=<repo-name>   # Platform-Frontend | Platform-Backend | assessment_engine
cd /tmp
if [ -d "$REPO/.git" ]; then
  cd "$REPO"
  git fetch origin
  git reset --hard origin/development
else
  git clone https://x-access-token:${GH_TOKEN}@github.com/SC0RED/$REPO.git
  cd "$REPO"
  git checkout development
fi
```

`reset --hard` wipes any uncommitted state from a previous run. For Ready-for-Dev work that needs its own branch, branch off `development` *after* the refresh (`git checkout -b fix/...`).

## Pushing a branch + opening a PR

`gh` is installed and picks up `GH_TOKEN` automatically — no `gh auth login` needed:

```bash
git push -u origin fix/SPE-XXXX-<short-slug>
gh pr create --base development --title "..." --body "..."
```

The PR author will appear as `sc0red-patch[bot]`. Linked to you via commit author (your local `git config user.*`), so commits are attributed to Patch but the PR is opened as the bot.

## What the App *can't* do

- Reach any repo outside the three it's installed on
- Write to branch protections, org settings, secrets, or Actions
- Sign commits (use regular git author; CodeRabbit + SonarCloud don't care)

If you hit a permissions error that looks like "Resource not accessible by integration," the App needs an additional permission toggle in its GitHub settings — flag that as a blocker on the ticket rather than working around it.
