# Security Service — Integration Points

## Webhook Flow Position

```
1. Twilio POST → /webhook/twilio
2. Normalize phone, get/create user (cached)
3. ★ Security gate (NEW) — call POST /guard
4. Subscription gate (existing)
5. AI call (Gemini/Claude)
6. Send response via WhatsApp
```

Security gate runs **before** subscription gate. Blocked user never reaches subscription check or AI.

---

## New Files in Main App

| File | Purpose | Pattern |
|------|---------|---------|
| `Botivation/services/security_client.py` | HTTP client for security service | Same as `subscription_client.py` |
| `Botivation/webhook/security_gate.py` | Gate logic in webhook flow | Same as `subscription_gate.py` |

---

## security_client.py

Calls security service (port 8004) with `X-Internal-Secret` auth.

```python
class SecurityClient:
    async def check_guard(user_id: int, message: str) -> GuardResult
    async def get_flag_status(user_id: int) -> FlagStatus
    async def unflag_user(user_id: int) -> bool
    async def reset_events(user_id: int) -> int
    async def get_events(user_id: int) -> list
    async def get_strike_counts(user_id: int) -> dict
    async def get_flagged_users() -> list
    async def get_stats() -> dict
    async def health() -> bool
```

**Fail-closed:** If service unreachable → return `GuardResult(action="block", reason="service_down")`.

---

## security_gate.py

Called from `webhook/api.py` after user lookup, before subscription gate.

```python
async def check_security_gate(user_id: int, phone_number: str, message: str) -> str | None:
    """Returns None (allow) or GATE_BLOCKED."""
    client = SecurityClient()
    result = await client.check_guard(user_id, message)

    if result.action == "allow":
        return None

    if result.response_text:
        await send_freeform(phone_number, result.response_text)

    return GATE_BLOCKED
```

**Flow:**
- `allow` → return None → webhook continues to subscription gate
- `block` + `response_text` → send canned Hebrew message → return blocked
- `block` + `null response_text` → silence (flagged user) → return blocked

---

## webhook/api.py Changes

Insert security gate call between user lookup and subscription gate:

```python
# After user lookup (line ~455)
security_result = await check_security_gate(
    user_id=db_user["id"],
    phone_number=normalized_phone,
    message=incoming_message,
)
if security_result == GATE_BLOCKED:
    return PlainTextResponse('<?xml version="1.0" encoding="UTF-8"?><Response></Response>')

# Existing subscription gate (line ~456)
gate_result = await check_subscription_gate(...)
```

Same empty TwiML pattern as subscription gate.

---

## Admin Routes (Existing Files)

| File | Change |
|------|--------|
| `admin/routes_users.py` | Add security tab to user detail page (calls security client) |
| `admin/routes_services.py` | Add security service health check row |
| `admin/routes_logs.py` | Add security service log tab |
| `admin/routes_security.py` | **New file** — security dashboard page (`/admin/security`) |

---

## Environment Variable

```
SECURITY_SERVICE_URL=http://127.0.0.1:8004
```

Added to `.env.example` and `config/`.
