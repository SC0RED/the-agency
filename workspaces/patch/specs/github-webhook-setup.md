# GitHub Webhook → Clawndom Setup Spec

## Overview

Add a GitHub webhook provider to Clawndom so CI failures on Patch's PRs get routed back for automated remediation.

## Changes Required

### 1. GitHub Webhook (per repo)

Create a webhook in each repo's Settings → Webhooks:

- **Repos:** SC0RED/Platform-Frontend, SC0RED/Platform-Backend, SC0RED/assessment_engine
- **Payload URL:** `https://mac-pro.tail708f46.ts.net/hooks/github`
- **Content type:** `application/json`
- **Secret:** Generate a new HMAC secret, store in 1Password Engineering vault
- **Events:** Select "Check runs" only (individual events → Check runs)
- **Active:** Yes

### 2. Tailscale Funnel Route

Add a new funnel route:

```bash
tailscale funnel --bg --https=443 /hooks/github http://127.0.0.1:8793/hooks/github
```

### 3. Clawndom PROVIDERS_CONFIG

Add a `github` provider to the JSON array in the LaunchAgent plist. The routing rules filter to:
- Only `check_run` events where `action` = `completed`
- Only `conclusion` = `failure`
- Only branches matching `fix/SPE-*` (Patch's branches)

```json
{
  "name": "github",
  "routePath": "/hooks/github",
  "hmacSecret": "<from 1Password>",
  "signatureStrategy": "github",
  "openclawHookUrl": "http://unused",
  "routing": {
    "rules": [
      {
        "strategy": "compound",
        "conditions": [
          {"field": "action", "value": "completed"},
          {"field": "check_run.conclusion", "value": "failure"},
          {"field": "check_run.check_suite.head_branch", "pattern": "^fix/SPE-"}
        ],
        "agentId": "patch",
        "messageTemplate": "{{doc:/Users/ctcreel/.openclaw/workspace-patch/templates/github-ci-failure.md}}"
      }
    ]
  },
  "modelRules": [
    {
      "field": "check_run.conclusion",
      "matches": ["failure"],
      "model": "anthropic/claude-opus-4-6"
    }
  ]
}
```

**Note:** The `compound` strategy and `pattern` matching may not exist in Clawndom yet. Clawndom currently supports `field-equals` only. Options:
- **Option A:** Add `compound` and `pattern` strategies to Clawndom (small feature)
- **Option B:** Use `field-equals` on `action`=`completed` and let the template itself filter on conclusion and branch name (simpler, no Clawndom changes)

**Recommendation:** Option B for now. The template already checks the branch name to extract the ticket key. Add a conclusion check at the top: if `check_run.conclusion` != `failure`, reply NO_REPLY.

### 4. Deduplication

GitHub fires multiple `check_run` events per push (one per check in the suite). To avoid spawning multiple fix sessions for the same failure:

**Option A (Clawndom feature):** Add dedup key based on `check_run.check_suite.head_sha` — skip if a job with the same dedup key was processed in the last 10 minutes.

**Option B (Template-level):** Accept that multiple sessions may fire. The first one that pushes a fix will change the HEAD SHA, making subsequent sessions' checkouts stale. They'll see the fix is already pushed and stop.

**Recommendation:** Option A is cleaner but requires Clawndom changes. Option B works today.

### 5. Model Override Authorization

**IMPORTANT:** This is also blocking the existing Jira webhooks right now. The gateway rejects Clawndom's `modelRules` with `"provider/model overrides are not authorized for this caller."` The OpenClaw gateway config needs to authorize the Clawndom hook token for model overrides, OR modelRules should be removed from all providers.

This must be fixed before ANY of this works — including the existing Jira pipeline.

## Implementation Order

1. **Fix Clawndom → gateway auth** (model override authorization OR remove modelRules) — unblocks existing Jira pipeline
2. **Add SonarCloud local scan to ready-for-dev template** — ✅ already done
3. **Update pipeline doc** — ✅ already done
4. **Set up GitHub webhook** — requires Chris to add webhooks in repo settings
5. **Add funnel route** — one command
6. **Update PROVIDERS_CONFIG** — LaunchAgent plist edit + restart
7. **Test end-to-end** — intentionally break a build, verify the fix cycle works
