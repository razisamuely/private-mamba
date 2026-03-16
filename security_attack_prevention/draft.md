# Security & Attack Prevention — Draft

## Scope (Phase 1)

WhatsApp-side attacks only (via Twilio webhook). Direct endpoint attacks out of scope.

## Vectors

| # | Vector | Detection | Response | Strike weight |
|---|--------|-----------|----------|---------------|
| B1 | Message flood (20+ msgs in X min) | Per-user msg counter + time window | Skip AI, reply "slow down" once, then silence | 1 per burst |
| C1 | Oversized message | Message length > threshold | Reject entirely, reply "message too long" | 1 per message |
| D1a | Token/encoding fuzzing (`.-.-.-`, emojis) | Regex repeating patterns | Skip AI, reply "didn't understand" | 1 per message |
| D1b | Math/buffer probes (`9!`, `3123+3123...`) | Regex math expressions + repetition | Skip AI, reply "didn't understand" | 1 per message |
| D1c | Multilingual jailbreak (Chinese/Arabic) | Language detection (not Hebrew/English) | Skip AI, reply "didn't understand" | 1 per message |

## Strike System

- Each detected attack logs a **security event** and increments the user's strike count
- After **N strikes** (configurable per type) → user **flagged**
- Flagged user → **all messages ignored**, no AI, no response
- Unflag → **admin-only, manual** (no auto-cooldown)

## `security_events` Table

| Column | Type | Purpose |
|--------|------|---------|
| id | serial | PK |
| user_id | int | Who |
| event_type | text | `message_flood` / `oversized_message` / `token_fuzzing` / `buffer_probe` / `lang_jailbreak` |
| message_body | text | Evidence (truncated to 500 chars) |
| created_at | timestamp | When |

- Strike count = `COUNT(*) WHERE user_id = X AND event_type = Y AND created_at > window`
- Flag threshold configurable per event_type in config
- Admin sees full attack history per user in dashboard

## Config-Driven (all values tunable, no hardcoded)

```json
{
  "flood_window_minutes": 5,
  "flood_max_messages": 20,
  "max_message_length": 2000,
  "flag_thresholds": {
    "message_flood": 3,
    "oversized_message": 5,
    "token_fuzzing": 3,
    "buffer_probe": 3,
    "lang_jailbreak": 3
  },
  "responses": {
    "flood": "הודעות רבות מדי, אנא המתן מספר דקות",
    "oversized": "ההודעה ארוכה מדי, אנא קצר אותה",
    "suspicious": "לא הצלחתי להבין, אפשר לנסח אחרת?",
    "flagged": "החשבון שלך הוגבל. לבירור פנה לתמיכה: support@botivation.com"
  }
}
```

All thresholds, windows, and response texts updatable via config without code changes.

## Data Model

**`security_events` table** — attack evidence log:

| Column | Type | Purpose |
|--------|------|---------|
| id | serial | PK |
| user_id | int | Who |
| event_type | text | `message_flood` / `oversized_message` / `token_fuzzing` / `buffer_probe` / `lang_jailbreak` |
| message_body | text | Evidence (truncated 500 chars) |
| created_at | timestamp | When |

**`users` table** — add one field:

| Column | Type | Default | Purpose |
|--------|------|---------|---------|
| is_flagged | boolean | false | Fast gate — guard checks this first, no query needed (cached) |

**How they work together:**
- Each rejected message → row in `security_events`
- Strike count = `COUNT(*) FROM security_events WHERE user_id + event_type + time window`
- Strikes hit threshold → `is_flagged = true` on user
- Guard reads `is_flagged` (cached) → silence. No events table query needed for flagged users
- Admin unflags → `is_flagged = false`
- No separate counter or attacker table — events table is the counter, user table is the gate

## DB Queries

**Guard (core):**

| # | Name | Purpose |
|---|------|---------|
| 1 | `get_user_flag_status` | is_flagged check |
| 2 | `get_message_count_in_window` | flood detection (user + time range) |
| 3 | `insert_security_event` | log attack |
| 4 | `count_strikes_by_type` | threshold check (user + event_type + window) |
| 5 | `set_user_flagged` | flag user |

**Admin:**

| # | Name | Purpose |
|---|------|---------|
| 6 | `get_events_by_user` | attack history list |
| 7 | `get_strike_counts_by_user` | per-type breakdown |
| 8 | `get_flagged_users_with_last_event` | flagged list + why |
| 9 | `get_dashboard_stats` | totals, top attackers |
| 10 | `get_recent_attacks` | last N attacks with message preview |
| 11 | `delete_events_by_user` | reset strikes |
| 12 | `unset_user_flagged` | unflag |

## Service Architecture

**Port:** 8004 (8000=main, 8001=inspector, 8003=subscription)
**Auth:** `X-Internal-Secret` (same pattern as other services)
**Fail behavior:** Fail-closed — service down → block all messages
**Deployment:** Own systemd unit + run.sh + deploy scripts

### Sync vs Async Split

**Sync (blocks HTTP response):**
- Read `is_flagged` from cache → instant
- Run detectors (oversized, gibberish, language, flood) → ~1-5ms
- Return allow/block decision

**Async (fire-and-forget, after response returned):**
- Log event to `security_events` table
- Invalidate `is_flagged` cache
- Run flag threshold checker
- Update `is_flagged` in DB if needed
- Re-read `is_flagged` into cache

**Cache:** `is_flagged` per user, 24h TTL (configurable). On new attack → cache invalidated and refreshed.

**Tradeoff:** One extra message may slip through before flag catches up. Acceptable for fast response.

### Latency

All detectors are O(n) string ops. Localhost HTTP ~1-5ms total. Log request duration on every call to catch regressions.

## Capabilities & Endpoints

### Core — why the service exists

| # | Capability | Endpoint | Called by | Why |
|---|-----------|----------|-----------|-----|
| 1 | **Message guard** | `POST /guard` | Main webhook | The core gate — decides allow/block before AI runs. Without this, every message hits Gemini |
| 2 | **Flag cache** | (internal) | Guard | Instant flagged-user rejection from memory. Without this, every guard call would query DB |

### Strike & Flag — automated escalation

| # | Capability | Endpoint | Called by | Why |
|---|-----------|----------|-----------|-----|
| 3 | **Event logging** | (async internal) | Guard | Records attack evidence. Without this, no strike counting, no admin visibility |
| 4 | **Strike checker** | (async internal) | Guard | Counts events per user/type, flags when threshold hit. Without this, attackers never get blocked |
| 5 | **Flag management** | `POST /unflag/{user_id}` | Admin dashboard | Only way to restore a flagged user. Without this, flagged users are permanently locked out |
| 6 | **Reset strikes** | `DELETE /events/{user_id}` | Admin dashboard | Clear all security events for a user. Without this, old strikes keep counting after unflag |

### Admin — visibility & control

| # | Capability | Endpoint | Called by | Why |
|---|-----------|----------|-----------|-----|
| 7 | **Flag status** | `GET /flag/{user_id}` | Admin dashboard | Show if user is flagged + reason. Without this, admin can't see who's blocked |
| 8 | **Attack history** | `GET /events/{user_id}` | Admin dashboard | Full evidence log per user. Without this, admin can't review what happened before unflagging |
| 9 | **Strike counts** | `GET /events/{user_id}/count` | Admin dashboard | Breakdown per attack type. Without this, admin can't understand attack patterns |
| 10 | **Flagged users list** | `GET /flagged` | Admin dashboard | All flagged users with last attack event per user. Without this, admin can't see who's blocked or why |
| 11 | **Dashboard stats** | `GET /stats` | Admin dashboard | Total flagged users, events today, top attackers, last 10 attacks. Without this, no system-wide security overview |

### Infra

| # | Capability | Endpoint | Called by | Why |
|---|-----------|----------|-----------|-----|
| 12 | **Health check** | `GET /health` | Monitoring/deploy | Service liveness. Without this, can't detect if guard is down (fail-closed = all blocked) |
| 13 | **Config loader** | (internal) | All | Reads thresholds/responses from config.json. Without this, every change requires code deploy |
| 14 | **Request timing** | (internal) | Guard | Logs guard call duration. Without this, can't detect latency regressions |

## Module Structure

```
Botivation/security_service/
  __init__.py               # docstring only
  __main__.py               # uvicorn entry point, port 8004
  app.py                    # FastAPI app, health endpoint, router mount
  routes.py                 # HTTP endpoints: guard, flag, events, stats, unflag
  message_guard.py          # core logic: guard(user, message) → allow/block (pure, no framework imports)
  detectors/
    __init__.py             # registry: auto-discovers detectors, runs by config order
    base.py                 # DetectionResult model + detect() signature contract
    flood.py                # B1 — per-user message rate in time window
    oversized.py            # C1 — message length check
    gibberish.py            # D1a/D1b — unicode letter ratio + regex patterns
    language.py             # D1c — Hebrew/English only (langdetect)
  queries.py                # security_events CRUD + is_flagged read/write
  cache.py                  # in-memory is_flagged cache, 24h TTL, invalidation
  config.json               # all thresholds, windows, response texts, detector registry
```

## Detector Plugin Pattern

Every detector is a function with the same signature:

```python
def detect(message: str, config: dict) -> DetectionResult | None
```

Registry in `config.json` controls which run and in what order:

```json
{
  "detectors": [
    {"name": "oversized", "enabled": true, "order": 1},
    {"name": "gibberish", "enabled": true, "order": 2},
    {"name": "language", "enabled": true, "order": 3},
    {"name": "flood", "enabled": true, "order": 4}
  ]
}
```

Guard loops enabled detectors in order — first match → block.

**Adding a new detector = 2 steps:**
1. Create `detectors/new_thing.py` with `detect()` function
2. Add entry to `config.json`

No code changes in guard. Enable/disable/reorder from config without deploy.

Follows same pattern as `subscription_service/` and `inspector_service/`.

## Where It Runs

```
1. Normalize phone
2. Get/create user (cached)
3. message_guard.guard(user, message)  ← ONE call, checks everything
4. Subscription gate
5. AI call
```

### Guard Flow (short-circuit, cheapest first)

```
1. Is user flagged?           → silence
2. Is message too long?       → reject + strike
3. Is message gibberish?      → reject + strike
4. Is message wrong language? → reject + strike
5. Is user flooding?          → reject + strike
6. Did strikes hit threshold? → flag user + send "account restricted" once
7. All clear                  → allow
```

Single call after user exists. Checks message content (oversized, gibberish, language) + user state (flood, strikes, flagged) in one pass. User lookup is cached — no extra DB cost.

Block → canned response or silence. Allow → continue to AI.

Today: local module. Tomorrow: extract to HTTP service, same interface.

## Scenarios

| # | Scenario | Trigger | Expected |
|---|----------|---------|----------|
| 1 | Normal user sends message | Regular Hebrew text | AI responds normally, no event logged |
| 2 | User sends 20 msgs in 5 min | Rapid messages | First N processed, then "slow down" reply, then silence |
| 3 | User sends 3 flood bursts | 3× scenario 2 | User flagged, all messages ignored |
| 4 | User sends 3000-char message | One oversized message | Rejected, "message too long" reply |
| 5 | User sends 5 oversized msgs | Repeated oversized | User flagged after 5th |
| 6 | User sends `.-.-.-.-.-.-.-` | Token fuzzing pattern | Skip AI, "didn't understand" reply, strike logged |
| 7 | User sends `3123+3123+3123...` | Buffer probe pattern | Skip AI, "didn't understand" reply, strike logged |
| 8 | User sends Chinese jailbreak prompt | Non-Hebrew/English text | Skip AI, "didn't understand" reply, strike logged |
| 9 | User hits 3 fuzzing strikes | 3× scenario 6/7/8 | User flagged |
| 10 | Flagged user sends normal message | Any message | No response, no AI call |
| 11 | Admin unflags user | Manual unflag in dashboard | User can interact again normally |
| 12 | Mixed attack — flood then fuzzing | B1 + D1a | Strikes accumulate across types, flag after total threshold |
| 13 | Short repeating pattern (legit) | "haha" or "ok ok ok" | Not flagged — regex should have minimum length/repetition threshold |
| 14 | Long Hebrew message (legit) | 1500-char Hebrew text (under limit) | AI responds normally |
| 15 | Emoji-only message (short, legit) | "👍" or "😂😂" | AI responds normally — not flagged |
| 16 | Emoji spam (attack) | 200+ random emojis in one message | Skip AI, strike logged |
| 17 | Random non-letter gibberish | `k$2ñ▶︎9ü!çΩ∆` random symbols with no structure | Skip AI, "didn't understand", strike logged |
| 18 | Random charset salad | `aÜ7#🔥кд+ñ3€` mixed scripts/symbols/numbers no pattern | Skip AI, strike logged |
| 19 | Mixed emoji + signs (attack) | `🔥@ü9!▲кд.-3€🎭` random noise | Skip AI, strike logged |
| 20 | Single emoji (legit) | "👍" or "❤️" | AI responds normally |
| 21 | Security service down | Service stopped | Fail-closed — all messages blocked, no AI calls |
| 22 | Security service slow (>100ms) | High latency response | Message still processed, latency warning logged |
| 23 | Admin unflags user via API | `POST /unflag/{user_id}` | `is_flagged=false`, cache invalidated, user can interact again |
| 24 | Admin views attack history | `GET /events/{user_id}` | Full event list with type, message body, timestamp |
| 25 | Admin views dashboard stats | `GET /stats` | Flagged user count, events today, top attackers |
| 26 | User gets flagged (first time) | Strikes hit threshold | "Account restricted, contact support" sent once, then silence |

## Integration Points

- Security guard runs **before** subscription gate (step 3, after user lookup)
- Client module: `Botivation/services/security_client.py` — same pattern as subscription client
- Gate module: `Botivation/webhook/security_gate.py` — same pattern as `subscription_gate.py`
- Fail-closed: client returns block if service unreachable
- **Response flow:** security service returns `response_text` → main webhook sends it via existing messaging layer (`send_freeform`). Flagged users get `null` response_text → silence (empty TwiML, no message sent)

## Admin UI Touchpoints

| # | Where | What | Details |
|---|-------|------|---------|
| 1 | **User Detail** (`/admin/users/{id}`) | New "Security" tab | Flag status badge, unflag + reset strikes button, events history table, strike counts per type |
| 2 | **Users List** (`/admin/users`) | Flagged in state column | Show "flagged" alongside existing states (active/suspended) — no new column |
| 3 | **Security Dashboard** (`/admin/security`) | New page | Total flagged users, events today, top attackers list, recent events feed, **last 10 attacks** — content attacks (oversized/gibberish/language) show truncated message body, non-content attacks (flood) show description text (e.g. "20 messages in 5 min") |
| 4 | **Services** (`/admin/services`) | Health row | Security service (port 8004) status — same pattern as other services |
| 5 | **Logs** (`/admin/logs`) | New "Security" tab | Security service logs — same pattern as other service log tabs |

## Full Docs Order (outside-in)

1. `overview.md` — what & why
2. `manual_test_scenarios.md` — expected behavior (the contract)
3. `interfaces.md` — API request/response shapes
4. `integration_points.md` — where it hooks into existing code
5. `deployment_wiring.md` — how to run it
6. `package_structure.md` — what's inside
7. `schema_migration.md` — DB changes
8. `implementation_plan.md` — phased TDD plan (references all above)
