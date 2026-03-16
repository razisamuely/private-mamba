# Security Service — Implementation Plan

Related: [draft.md](draft.md) | [interfaces.md](interfaces.md) | [package_structure.md](package_structure.md) | [schema_migration.md](schema_migration.md)

> **Living doc.** Step details deleted after implementation — only status table remains.

---

## Phase Tracking

- [x] **Phase 1:** Skeleton — all files, stubs, models, wiring. Zero logic. Service starts and responds to health check.
- [x] **Phase 2:** DB layer — schema migration + queries.py (12 queries)
- [x] **Phase 3:** Detectors — pure detection functions (oversized, gibberish, language, flood)
- [x] **Phase 4:** Core guard — message_guard.py + cache.py + config loading
- [x] **Phase 5:** Routes — HTTP endpoints (guard, flag, events, stats, unflag, reset)
- [x] **Phase 6:** Integration — security_client.py + security_gate.py + webhook wiring
- [x] **Phase 7:** Deployment — systemd, run.sh, deploy scripts
- [x] **Phase 8:** Admin UI — security tab, dashboard page, services health, logs tab

---

## Requirements

- [x] **Scale:** Low volume (<100 users), single server
- [x] **Latency:** Guard call < 5ms (localhost HTTP + cached flag + string ops)
- [x] **Reliability:** Fail-closed — service down → block all
- [x] **Deployment:** Separate service, port 8004, own systemd unit
- [x] **Extensibility:** Plugin pattern — add detector in 2 steps
- [x] **Config-driven:** All thresholds, windows, responses from config.json

---

## Definition of Done

- **Functionality:** All 8 phases complete, guard blocks attacks, admin can unflag/reset
- **Code quality:** Tests pass, no hardcoded values, type hints on all signatures
- **Reliability:** Fail-closed on service error, cache invalidation works
- **Deployment:** Service in run.sh/systemd/deploy scripts
- **Manual tests:** All 23 scenarios from manual_test_scenarios.md pass

---

## Guidelines

**From existing plans + general best practices:**

- **Small functions** — one function does one thing. If it needs a comment explaining what it does, split it
- **No hardcoded values** — thresholds, messages, ports, URLs → config.json or env vars. Zero magic numbers
- **Meaningful names** — `count_strikes_by_type` not `get_count`. `is_flagged` not `flag`. Names explain intent
- **Meaningful logging** — log guard decisions, flag changes, config loads, errors. Include user_id + event_type in every log
- **Responsibility isolation** — detectors don't know about DB. Guard doesn't know about HTTP. Routes don't contain logic
- **Pure where possible** — detectors and guard are pure functions (testable without DB/HTTP)
- **Defensive reads** — `.get()` with defaults for external data. Never trust input shapes
- **Config over code** — detector registry, thresholds, response texts all from config.json
- **Fail-closed** — when in doubt, block. Unlike subscription (fail-open), security must block on error
- **Type hints** — on all function signatures
- **No cross-imports** — security_service never imports from main app. Main app uses security_client (HTTP)

---

## TDD Workflow

Every step (Phase 2+) follows this order:

1. **Tests** — write assertions. Must all fail
2. **Verify failure** — `pytest tests/security_service/ -x -q`
3. **Implement** — minimal code to make tests pass
4. **Verify pass** — run tests, confirm green
5. **Mark done** — update status table

Phase 1 is structure-only — no TDD needed. Just files + stubs + service starts.

---

## Implementation Order

```
Phase 1: Skeleton (zero logic, service starts)
  Step 1  → config.json + config loader
  Step 2  → Pydantic models (request/response)
  Step 3  → File stubs (all .py files with pass)
  Step 4  → FastAPI app + health endpoint + router mount
  Step 5  → Detector base + registry (stubs)
  Step 6  → Verify: service starts, GET /health returns ok

Phase 2: DB layer
  Step 7  → Schema migration (security_events table + users.is_flagged)
  Step 8  → get_user_flag_status
  Step 9  → insert_security_event
  Step 10 → get_message_count_in_window
  Step 11 → count_strikes_by_type
  Step 12 → set_user_flagged
  Step 13 → get_events_by_user
  Step 14 → get_strike_counts_by_user
  Step 15 → get_flagged_users_with_last_event
  Step 16 → get_dashboard_stats
  Step 17 → get_recent_attacks
  Step 18 → delete_events_by_user

Phase 3: Detectors (pure functions)
  Step 19 → oversized.detect
  Step 20 → gibberish.detect
  Step 21 → language.detect
  Step 22 → flood.detect
  Step 23 → Detector registry (load + run from config)

Phase 4: Core guard
  Step 24 → cache.FlagCache (get/set/invalidate with TTL)
  Step 25 → message_guard.guard (loop detectors, check flag, return result)
  Step 26 → Async post-guard (log event, check threshold, flag if needed, refresh cache)

Phase 5: Routes
  Step 27 → POST /guard
  Step 28 → GET /flag/{user_id}
  Step 29 → POST /unflag/{user_id}
  Step 30 → DELETE /events/{user_id}
  Step 31 → GET /events/{user_id}
  Step 32 → GET /events/{user_id}/count
  Step 33 → GET /flagged
  Step 34 → GET /stats

Phase 6: Integration (main app)
  Step 35 → security_client.py (HTTP client, fail-closed)
  Step 36 → security_gate.py (gate logic, send response_text)
  Step 37 → webhook/api.py wiring (insert gate before subscription)

Phase 7: Deployment
  Step 38 → systemd template + installer script
  Step 39 → run.sh + deploy_remote.sh changes
  Step 40 → .env.example update

Phase 8: Admin UI
  Step 41 → User detail security tab
  Step 42 → Users list flagged column
  Step 43 → Security dashboard page
  Step 44 → Services page health row
  Step 45 → Logs page security tab
```

---

## Status

| Step | What | Test file | Status |
|------|------|-----------|--------|
| 1 | config.json + loader | — | done |
| 2 | Pydantic models | — | done |
| 3 | File stubs | — | done |
| 4 | FastAPI app + health | — | done |
| 5 | Detector base + registry stubs | — | done |
| 6 | Service starts | — | done |
| 7 | Schema migration | — | done |
| 8 | get_user_flag_status | test_security_queries.py | done |
| 9 | insert_security_event | test_security_queries.py | done |
| 10 | get_message_count_in_window | test_security_queries.py | done |
| 11 | count_strikes_by_type | test_security_queries.py | done |
| 12 | set_user_flagged | test_security_queries.py | done |
| 13 | get_events_by_user | test_security_queries.py | done |
| 14 | get_strike_counts_by_user | test_security_queries.py | done |
| 15 | get_flagged_users_with_last_event | test_security_queries.py | done |
| 16 | get_dashboard_stats | test_security_queries.py | done |
| 17 | get_recent_attacks | test_security_queries.py | done |
| 18 | delete_events_by_user | test_security_queries.py | done |
| 19 | oversized.detect | test_detector_oversized.py | done |
| 20 | gibberish.detect | test_detector_gibberish.py | done |
| 21 | language.detect | test_detector_language.py | done |
| 22 | flood.detect | test_detector_flood.py | done |
| 23 | Detector registry | test_detector_registry.py | done |
| 24 | FlagCache | test_security_cache.py | done |
| 25 | message_guard.guard | test_message_guard.py | done |
| 26 | Async post-guard | test_message_guard.py | done |
| 27 | POST /guard | test_security_routes.py | done |
| 28 | GET /flag/{user_id} | test_security_routes.py | done |
| 29 | POST /unflag/{user_id} | test_security_routes.py | done |
| 30 | DELETE /events/{user_id} | test_security_routes.py | done |
| 31 | GET /events/{user_id} | test_security_routes.py | done |
| 32 | GET /events/{user_id}/count | test_security_routes.py | done |
| 33 | GET /flagged | test_security_routes.py | done |
| 34 | GET /stats | test_security_routes.py | done |
| 35 | security_client.py | test_security_client.py | done |
| 36 | security_gate.py | test_security_gate.py | done |
| 37 | webhook wiring | — | done |
| 38 | systemd + installer | — | done |
| 39 | run.sh + deploy | — | done |
| 40 | .env.example | — | done (no file, default in code) |
| 41 | User detail security tab | — | done |
| 42 | Users list flagged column | — | done |
| 43 | Security dashboard page | — | done |
| 44 | Services health row | — | done |
| 45 | Logs security tab | — | done |
