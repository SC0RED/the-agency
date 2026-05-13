# Handling CodeRabbit feedback

CodeRabbit auto-skips review when the PR author is a bot (`sc0red-patch[bot]`). You must trigger it manually after every push, then triage the resulting comments — applying the legitimate ones and pushing back on the ones that conflict with our standards.

## Step 1 — Trigger the review

After `gh pr create` (or after any subsequent force-push that materially changes the diff):

```bash
gh pr comment <PR-NUMBER> --repo <OWNER>/<REPO> --body "@coderabbitai review"
```

CodeRabbit posts an inline review within ~2 minutes.

## Step 2 — Fetch the review

```bash
gh pr view <PR-NUMBER> --repo <OWNER>/<REPO> --comments
gh api repos/<OWNER>/<REPO>/pulls/<PR-NUMBER>/comments | jq '.[] | select(.user.login | test("coderabbit"; "i")) | {path, line, body}'
```

Read every comment. Don't just count them.

## Step 3 — Triage, don't capitulate

CodeRabbit is a junior reviewer with strong opinions and zero context. Some of its findings are real defects you need to fix. Others are textbook "best practices" that **violate our standards** in `shared/anti-patterns.md` and the project's `CLAUDE.md`. Apply or contest each one based on the rules below — never accept a suggestion just because it's there.

### Apply

- **Real defects** — null-deref, off-by-one, missed edge case in payload validation at a real boundary, broken regex.
- **Security findings with teeth** — hardcoded secrets, command injection via shell interpolation of untrusted input, weak crypto on identifiers that need to be unguessable (`Math.random()` for security tokens, etc.).
- **Type safety improvements** that don't introduce `any` or `as` casting — narrowing an over-broad type, exhaustive switch handling.
- **Concrete bug patterns** — `.sort()` without a compare function on strings, `String#replace` with global regex (use `replaceAll`), `await` in a forEach.
- **Pinning floating refs** — `@master`, `@latest`, unpinned action versions where reproducibility matters.
- **Real path-mismatch findings** — config that points at directories that don't exist, hooks excluded by the wrong filename pattern.

### Contest (push back in a PR comment, then resolve)

- **"Add defensive null checks for internal data"** — violates [anti-patterns.md "The Defensive Programming Trap"](./anti-patterns.md). Internal code trusts internal contracts. Validate at system boundaries only. Reply with: *"Internal contract — caller already guarantees non-null. Per project anti-patterns, defensive checks on internal code mask bugs rather than prevent them."*
- **"Add try/catch around X"** — almost always defensive. Only catch when you have a *specific* recovery action. "Log and continue" is not recovery.
- **"Add a fallback value"** — fallbacks on data that should always be present hide bugs.
- **"Use isinstance / hasattr / typeof checks before calling"** — duck-typing internal interfaces is doubt, not safety. If the type system says it's there, it's there.
- **"Re-validate this Pydantic / Zod model"** — schemas are validated once at the boundary. Re-validating internally costs latency and adds nothing.
- **"Extract this 30-line block into a helper function"** — premature abstraction. Three similar lines is better than a helper used once. Functions only get factored out when there's a *real* second caller, not a hypothetical one.
- **"Add unit tests for callability without behavior"** — tests that only assert "no exception thrown" are rejected. Tests must validate *behavior*, not just execute code.
- **"Add a backwards-compat shim"** — for unused exports, removed code, deleted flags. We delete cleanly. No `_unused` renames, no `// removed` comments.
- **"Make this configurable"** — if there's no concrete second caller asking for the knob, don't add it. YAGNI.
- **Vague suggestions** ("consider improving error handling", "this could be more robust") — ask CodeRabbit to be specific or skip.

### When in doubt

If a suggestion is borderline — small enough to apply cleanly, doesn't smell defensive, and the "risk if you don't" is real — apply it. Borderline finds tend to be cheap to fix and free signal for human reviewers.

## Step 4 — Reply on contested items

For each contested finding, post a reply directly on the inline comment so the resolution is visible. Use:

```bash
gh api repos/<OWNER>/<REPO>/pulls/<PR-NUMBER>/comments/<COMMENT-ID>/replies \
  -f body="<your-reply>"
```

…or use the GitHub web UI's "Reply" affordance. Keep replies tight: one sentence stating the rule it violates, link to `anti-patterns.md` if relevant. Then **resolve the conversation** — don't leave it open as if it's pending. Resolved-with-reason beats open-and-ignored.

## Step 5 — Push fixes if any landed

If you applied any of CodeRabbit's suggestions:

```bash
git commit --amend --no-edit && git push --force-with-lease
```

…then optionally trigger another CodeRabbit pass on the new diff if the changes were substantive. For one or two trivial fixes, skip the re-review.

## Step 6 — Stop iterating

Two CodeRabbit passes is enough. If round 2 still complains about defensive style, that's a sign of policy disagreement, not a defect. Note the disagreement in the PR description, transition the ticket, move on. Humans handle the final call.

## Anti-pattern: capitulation cycles

The failure mode here is iterating with CodeRabbit until it stops complaining — which it never will, because some of what it wants is the very thing our standards forbid. Your job is to ship code that meets *our* bar. CodeRabbit is one signal among several. If applying its suggestion would make the diff worse by our rules, it's wrong and we move on.
