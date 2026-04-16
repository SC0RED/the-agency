# Clawndom Audit — Full Code Review

**Reviewed:** 2026-03-30 by Patch
**Repo:** `/Volumes/SSD/Code/Github/sc0red/clawndom`
**Branch on disk:** `main` @ `11b81e3`
**Running binary:** `dist/server.js` — built from `main` (HTTP fire-and-forget mode)

---

## What's Built and Working (in production right now)

### Webhook Ingestion
- Express server on port 8793 (launchd: `com.openclaw.clawndom`)
- Per-provider route registration from `PROVIDERS_CONFIG` env var
- Currently one provider configured: `jira` at `/hooks/jira`

### HMAC Signature Validation
- Strategy pattern: `websub` (Jira's `X-Hub-Signature`) and `github` (`X-Hub-Signature-256`)
- Timing-safe comparison via `timingSafeEqual`
- This is the one thing OpenClaw genuinely cannot do natively

### BullMQ Queue
- Redis-backed, per-provider queue (`webhooks:jira`)
- Concurrency: 1 worker per provider
- `removeOnComplete: 100`, `removeOnFail: 100`
- Webhook accepted → 202 → enqueued → worker picks up

### Agent Routing
- Strategy pattern: `field-equals`, `regex`, `default`
- Dot-notation field path resolution on payload
- Currently routes based on `issue.fields.assignee.displayName`, `issue.fields.status.name`
- Falls back to `"patch"` as default

### Worker (current behavior — `worker.service.ts`)
- Parses payload, resolves agent, builds envelope
- **HTTP POST to `http://127.0.0.1:18789/hooks/agent`** with bearer token
- Gets 200 back → job done
- **This is fire-and-forget.** No completion tracking. No retry on agent failure.

### Infrastructure
- launchd plist installed at `~/Library/LaunchAgents/com.openclaw.clawndom.plist`
- Logs to `/usr/local/var/log/clawndom.log`
- Tailscale Funnel exposes `/hooks/jira` publicly

### Supporting Code
- Structured logging with correlation IDs (`x-correlation-id` header)
- Error handler middleware with RFC 7807 error responses
- Zod validation middleware
- Custom exception hierarchy (`ClawndomError` → client/server errors)
- TTL cache utility (not used by any service currently)
- Retry decorator utility (not used by any service currently)
- CloudWatch metrics utility (not used — requires AWS SDK, not available locally)
- Health endpoint at `/api/health` (currently only checks "application alive")

---

## What's Built But NOT Wired Up

### GatewayClient (`src/services/gateway-client.ts`)
- Full WebSocket client for OpenClaw gateway
- Implements protocol v3 handshake (connect → challenge/response)
- `runAndWait(params, timeoutMs)` method:
  1. Sends `agent` RPC → gets `runId`
  2. Sends `agent.wait` RPC → blocks until terminal state
  3. Returns `{ runId, status: 'ok'|'error'|'timeout', startedAt, endedAt }`
- **Not imported by anything.** Worker uses raw HTTP `fetch` instead.
- **History:** Built in `eed1edc`, wired into worker, then deliberately removed in `a91bd0e` by Chris:
  > "Removed GatewayClient WS dependency (WS agent.wait deferred until protocol verified)"

### Session-File Polling (`feature/SPE-1602-session-file-polling` — PR #10, NOT merged)
- `SessionMonitor` service that reads OpenClaw's `sessions.json` file
- Polls for session idle detection (updatedAt unchanged for configurable threshold)
- Content-hash deduplication to prevent Jira retry duplicates
- AbortSignal support for graceful shutdown
- **This is an alternative to GatewayClient** — same goal (know when a run finishes), different mechanism (file polling vs WebSocket)
- Commit `87ee0f7` — PR merged to a feature branch but NOT to main

### Retry Decorator (`src/lib/utils/retry.ts`)
- Exponential backoff with jitter
- Configurable max attempts, delays
- `RetryExhaustedError` with attempt count
- **Not used anywhere.** BullMQ has its own retry mechanism, and the worker doesn't use this either.

### TTL Cache (`src/lib/utils/cache.ts`)
- In-memory TTL cache with LRU eviction and hit/miss stats
- Function wrapper decorator version
- **Not used anywhere.**

### CloudWatch Metrics (`src/lib/observability/metrics.ts`)
- `publishMetric()` and `publishMetricsBatch()`
- Lazy-loads `@aws-sdk/client-cloudwatch`
- **Not used anywhere.** SDK not installed locally.

---

## What's Missing

### 1. Completion Tracking (the critical gap)
The worker POSTs to OpenClaw and considers the job done on HTTP 200. It has **zero visibility** into whether the agent session ran successfully, timed out, or crashed.

**Two solutions were built but neither is active:**
- `GatewayClient` (WS-based) — in source, not imported
- `SessionMonitor` (file-polling) — in unmerged PR #10

### 2. Retry on Agent Failure
Since the worker doesn't know if the agent succeeded, it can't retry. BullMQ's retry only fires if the HTTP POST itself fails (network error, 5xx from gateway). If the gateway accepts the job but the agent stalls for 2 hours, the BullMQ job is already marked complete.

### 3. Dead Letter Queue
No DLQ configuration. Failed jobs are kept (count: 100) but nothing alerts on them or re-processes them.

### 4. Health Check Depth
README promises Redis, WS, and per-queue health checks. Actual implementation only checks "application alive." No Redis ping, no queue depth, no gateway connectivity.

### 5. Global Concurrency Semaphore
README and proposal mention a Redis-backed global semaphore across all providers. Not implemented. Current serialization is per-provider via BullMQ `concurrency: 1`, which happens to work because there's only one provider.

### 6. Graceful Shutdown
`server.ts` shutdown handler just calls `process.exit(0)`. No worker drain, no in-flight job completion, no Redis disconnect.

---

## What's Redundant with OpenClaw

| Capability | OpenClaw Native | Clawndom |
|---|---|---|
| Webhook endpoint | `/hooks/agent` with bearer auth | `/hooks/:provider` with HMAC |
| Payload templating | `transform.template` in hook config | N/A (passes raw payload) |
| Agent routing | Static `agentId` in hook config | Dynamic routing via payload fields |
| Session serialization | `maxConcurrent` in agent config | BullMQ concurrency: 1 |
| Queue persistence | None (in-memory) | Redis-backed BullMQ |

**Clawndom's unique value:**
1. HMAC signature validation (OpenClaw can't do this)
2. Redis-backed queue persistence (survives restarts — OpenClaw's queue doesn't)
3. Dynamic agent routing from payload content (OpenClaw needs JS transform module)
4. Completion tracking + retry (WHEN wired up — not currently active)

---

## Config (what's actually deployed)

```
PORT=8793
OPENCLAW_HOOK_URL=http://127.0.0.1:18789/hooks/agent
OPENCLAW_AGENT_ID=patch
OPENCLAW_TOKEN=f102d0f3... (bearer token)
REDIS_URL=redis://127.0.0.1:6379
PROVIDERS_CONFIG=[{"name":"jira", ...routing rules...}]
```

**Notable:** `OPENCLAW_GATEWAY_WS_URL` is in the plist template but NOT in the deployed plist. Config schema doesn't even have a field for it. The WS URL was removed when GatewayClient was disconnected.

---

## Git History (what happened)

1. `a146129` — Initial HMAC proxy + BullMQ (fire-and-forget POST)
2. `eed1edc` — GatewayClient built, completion-aware worker via WS
3. `20fd026` (PR #9) — WebSocket completion serialization (merged to feature branch)
4. `87ee0f7` (PR #10) — Replaced WS with session-file polling (NOT merged to main)
5. `a91bd0e` — **Reverted to HTTP fire-and-forget for local deploy.** GatewayClient removed from worker. Reason: "WS agent.wait deferred until protocol verified"
6. `11b81e3` — Agent routing strategy added (current main)

**The completion story:** It was built twice (WS and file-polling), neither approach stuck, and the system shipped without it.

---

## Recommendations

### Immediate (fix the stall problem)
1. **Wire up `GatewayClient.runAndWait()` in the worker.** It's already built. The `agent` and `agent.wait` RPCs are real OpenClaw protocol — the WS handshake was the issue, and GatewayClient already implements protocol v3.
2. **OR merge PR #10** (session-file polling) if the WS approach is still unverified.
3. Either way: when the agent run returns `error` or `timeout`, let the BullMQ job throw → BullMQ retries automatically.

### Short-term
4. Add BullMQ job retry config: `attempts: 3, backoff: { type: 'exponential', delay: 30000 }`
5. Wire up health checks: Redis ping, queue depth, gateway WS connectivity
6. Graceful shutdown: drain workers before `process.exit()`

### Later
7. Dead letter alerting (post to Slack/Discord when a job exhausts retries)
8. Drop the unused utilities or wire them in (cache, retry decorator, CloudWatch metrics)
9. Global concurrency semaphore if we add a second provider
