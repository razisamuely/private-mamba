# Security Service — Package Structure

## File Tree

```
Botivation/security_service/
  __init__.py
  __main__.py
  app.py
  routes.py
  message_guard.py
  detectors/
    __init__.py
    base.py
    flood.py
    oversized.py
    gibberish.py
    language.py
  queries.py
  cache.py
  config.json
```

---

## Module Details

### `__init__.py`
Docstring only. No exports.

### `__main__.py`
Uvicorn entry point.
- `PORT = int(os.getenv("SECURITY_PORT", 8004))`
- Runs `app:app` on `0.0.0.0:PORT`

### `app.py`
FastAPI app setup.
- `app` — FastAPI instance
- `startup()` — load config, init cache, init DB pool
- `GET /health` — returns `{"status": "ok"}`
- Mounts `routes.router`

### `routes.py`
All HTTP endpoints.
- `router` — APIRouter
- `post_guard(request: GuardRequest) -> GuardResponse` — message gate
- `get_flag(user_id: int) -> FlagStatus` — flag check
- `post_unflag(user_id: int) -> UnflagResult` — unflag user
- `delete_events(user_id: int) -> ResetResult` — reset strikes
- `get_events(user_id: int) -> EventList` — attack history
- `get_event_counts(user_id: int) -> StrikeCounts` — per-type breakdown
- `get_flagged() -> FlaggedUserList` — all flagged users
- `get_stats() -> DashboardStats` — system-wide stats

**Models (Pydantic):**
- `GuardRequest(user_id: int, message: str)`
- `GuardResponse(action: str, reason: str | None, response_text: str | None, flagged: bool)`
- `FlagStatus(user_id: int, is_flagged: bool, last_event: dict | None)`
- `UnflagResult(success: bool, user_id: int, is_flagged: bool)`
- `ResetResult(success: bool, user_id: int, deleted_count: int)`
- `EventList(user_id: int, events: list[dict])`
- `StrikeCounts(user_id: int, counts: dict[str, int])`
- `FlaggedUserList(flagged_users: list[dict])`
- `DashboardStats(flagged_count: int, events_today: int, top_attackers: list, recent_attacks: list)`

### `message_guard.py`
Core guard logic. **Pure Python — no FastAPI, no DB imports.**
- `guard(user_id: int, message: str, config: dict, cache: FlagCache, detectors: list) -> GuardResult`
- `GuardResult(action: str, reason: str | None, response_text: str | None, flagged: bool)`
- Loops detectors in order, short-circuits on first match
- After block: fires async event logging + strike check

### `detectors/__init__.py`
Detector registry.
- `load_detectors(config: dict) -> list[Detector]` — reads config, imports enabled detectors by name, returns sorted list
- `run_detectors(message: str, user_id: int, config: dict, detectors: list) -> DetectionResult | None` — loop + short-circuit

### `detectors/base.py`
Contract for all detectors.
- `DetectionResult(event_type: str, response_key: str)` — dataclass
- `detect(message: str, config: dict) -> DetectionResult | None` — signature contract (not a base class, just convention)

### `detectors/oversized.py`
- `detect(message: str, config: dict) -> DetectionResult | None`
- Checks `len(message) > config["max_message_length"]`

### `detectors/gibberish.py`
- `detect(message: str, config: dict) -> DetectionResult | None`
- Unicode letter ratio via `unicodedata.category()`
- Returns `token_fuzzing` or `buffer_probe` based on regex match

### `detectors/language.py`
- `detect(message: str, config: dict) -> DetectionResult | None`
- Uses `langdetect` library
- Allows Hebrew (`he`) and English (`en`) only

### `detectors/flood.py`
- `detect(message: str, config: dict, *, user_id: int, get_count: Callable) -> DetectionResult | None`
- Needs `user_id` + DB callback to check message count in window
- Note: different signature — takes extra kwargs vs content detectors

### `queries.py`
All DB operations (async, SQLAlchemy).
- `get_user_flag_status(user_id: int) -> bool`
- `get_message_count_in_window(user_id: int, window_minutes: int) -> int`
- `insert_security_event(user_id: int, event_type: str, message_body: str) -> None`
- `count_strikes_by_type(user_id: int, event_type: str, window_minutes: int) -> int`
- `set_user_flagged(user_id: int, flagged: bool) -> None`
- `get_events_by_user(user_id: int) -> list[dict]`
- `get_strike_counts_by_user(user_id: int) -> dict[str, int]`
- `get_flagged_users_with_last_event() -> list[dict]`
- `get_dashboard_stats() -> dict`
- `get_recent_attacks(limit: int) -> list[dict]`
- `delete_events_by_user(user_id: int) -> int`

### `cache.py`
In-memory flag cache.
- `FlagCache` class
- `get(user_id: int) -> bool | None` — returns cached value or None (miss)
- `set(user_id: int, flagged: bool) -> None` — store with TTL
- `invalidate(user_id: int) -> None` — remove entry
- `TTL` — configurable, default 24h

### `config.json`
All thresholds, windows, response texts, detector registry. See draft for full structure.

---

## Dependency Flow

```
__main__.py → app.py → routes.py → message_guard.py → detectors/*
                                  → queries.py
                                  → cache.py
                                  → config.json
```

- `routes.py` depends on `message_guard`, `queries`, `cache`
- `message_guard.py` depends on `detectors` only (pure logic)
- `detectors/*` depend on nothing (pure functions)
- `queries.py` depends on DB (SQLAlchemy)
- `cache.py` depends on nothing (stdlib only)

**Testability:** `message_guard.py` and all detectors are pure — testable without DB or FastAPI.
