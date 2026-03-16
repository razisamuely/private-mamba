# Security Service — Schema Migration

## 1. New Table: `security_events`

```sql
CREATE TABLE security_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    event_type TEXT NOT NULL,
    message_body TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

`event_type` values: `message_flood`, `oversized_message`, `token_fuzzing`, `buffer_probe`, `lang_jailbreak`

`message_body` truncated to 500 chars at application level.

---

## 2. Alter Table: `users`

```sql
ALTER TABLE users ADD COLUMN is_flagged BOOLEAN NOT NULL DEFAULT FALSE;
```

---

## 3. Indexes

```sql
-- Strike counting: WHERE user_id + event_type + created_at > window
CREATE INDEX idx_security_events_user_type_time
    ON security_events (user_id, event_type, created_at);

-- Flood detection: WHERE user_id + created_at > window
CREATE INDEX idx_security_events_user_time
    ON security_events (user_id, created_at);

-- Flagged users list
CREATE INDEX idx_users_is_flagged
    ON users (is_flagged) WHERE is_flagged = TRUE;
```

---

## 4. Update `schema.sql`

Add `security_events` table and `users.is_flagged` column to `Botivation/database/schema.sql` (source of truth).

---

## Rollback

```sql
DROP TABLE IF EXISTS security_events;
ALTER TABLE users DROP COLUMN IF EXISTS is_flagged;
```