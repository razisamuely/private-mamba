# Security Service — API Interfaces

Base: `http://localhost:8004`
Auth: `X-Internal-Secret` header (all endpoints except `/health`)

---

## POST /guard

Message gate — allow or block before AI runs.

**Request:**
```json
{"user_id": 1, "message": "שלום"}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| user_id | int | yes | |
| message | str | yes | Raw message text |

**Response (allow):**
```json
{"action": "allow"}
```

**Response (block):**
```json
{
  "action": "block",
  "reason": "oversized_message",
  "response_text": "ההודעה ארוכה מדי, אנא קצר אותה",
  "flagged": false
}
```

| Field | Type | Notes |
|-------|------|-------|
| action | `"allow"` \| `"block"` | |
| reason | str \| null | `oversized_message` / `token_fuzzing` / `buffer_probe` / `lang_jailbreak` / `message_flood` / `flagged` |
| response_text | str \| null | Hebrew canned response. null for flagged users (silence) |
| flagged | bool | true if this request triggered flagging |

**Status codes:** `200` always (block is not an error). `401` missing/wrong secret. `500` internal error.

---

## GET /flag/{user_id}

Check if user is flagged.

**Response:**
```json
{"user_id": 1, "is_flagged": true, "last_event": {"event_type": "token_fuzzing", "message_body": ".-.-.-...", "created_at": "2026-03-10T12:00:00Z"}}
```

| Field | Type | Notes |
|-------|------|-------|
| user_id | int | |
| is_flagged | bool | |
| last_event | object \| null | Most recent security event (null if not flagged) |

---

## POST /unflag/{user_id}

Unflag a user (admin action).

**Response:**
```json
{"success": true, "user_id": 1, "is_flagged": false}
```

---

## DELETE /events/{user_id}

Reset all strikes for a user (admin action).

**Response:**
```json
{"success": true, "user_id": 1, "deleted_count": 5}
```

---

## GET /events/{user_id}

Attack history for a user.

**Response:**
```json
{
  "user_id": 1,
  "events": [
    {
      "id": 42,
      "event_type": "token_fuzzing",
      "message_body": ".-.-.-.-.-.-.-",
      "created_at": "2026-03-10T12:00:00Z"
    }
  ]
}
```

---

## GET /events/{user_id}/count

Strike counts per attack type.

**Response:**
```json
{
  "user_id": 1,
  "counts": {
    "token_fuzzing": 2,
    "oversized_message": 1,
    "message_flood": 0,
    "buffer_probe": 0,
    "lang_jailbreak": 0
  }
}
```

---

## GET /flagged

All flagged users with last attack event.

**Response:**
```json
{
  "flagged_users": [
    {
      "user_id": 1,
      "phone": "+972...",
      "flagged_since": "2026-03-10T12:00:00Z",
      "last_event": {
        "event_type": "token_fuzzing",
        "message_body": ".-.-.-...",
        "created_at": "2026-03-10T12:00:00Z"
      }
    }
  ]
}
```

---

## GET /stats

Dashboard stats.

**Response:**
```json
{
  "flagged_count": 3,
  "events_today": 42,
  "top_attackers": [
    {"user_id": 1, "phone": "+972...", "event_count": 15}
  ],
  "recent_attacks": [
    {
      "user_id": 1,
      "event_type": "token_fuzzing",
      "message_body": ".-.-.-...",
      "created_at": "2026-03-10T12:00:00Z"
    }
  ]
}
```

| Field | Type | Notes |
|-------|------|-------|
| flagged_count | int | Total flagged users |
| events_today | int | Events since midnight |
| top_attackers | list | Top N users by event count |
| recent_attacks | list | Last 10 attacks. Content attacks show truncated message_body, flood shows description (e.g. "20 messages in 5 min") |

---

## GET /health

No auth required.

**Response:**
```json
{"status": "ok"}
```

**Status codes:** `200` healthy. `503` unhealthy.

---

## Error Format

All error responses:
```json
{"error": "description", "status_code": 401}
```
