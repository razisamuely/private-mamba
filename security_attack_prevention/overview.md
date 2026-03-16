# Security & Attack Prevention — Overview

## Problem

Every WhatsApp message hits Gemini AI — no gate. Attackers can:
- **Flood** messages → billing explosion (100 msgs = 100 AI calls)
- **Send oversized** text → token cost spike
- **Send gibberish/fuzzing** → wasted AI calls on nonsense
- **Use non-Hebrew/English** → jailbreak attempts bypass prompt rules

No detection, no blocking, no admin visibility.

## Solution

Standalone security service (port 8004) that gates every message **before** AI runs.

### How It Works

1. Main webhook calls `POST /guard` with user + message
2. Guard checks (short-circuit, cheapest first):
   - Is user flagged? → silence
   - Is message too long? → reject
   - Is message gibberish? → reject
   - Is message wrong language? → reject
   - Is user flooding? → reject
3. Block → canned Hebrew response. Allow → continue to AI
4. Each rejection logs a strike. Strikes hit threshold → user flagged
5. Flagged users are fully silenced. Admin unflags manually

### Key Properties

| Property | Decision |
|----------|----------|
| **Architecture** | Separate service, port 8004 |
| **Auth** | `X-Internal-Secret` (same as other services) |
| **Failure mode** | Fail-closed — service down → block all |
| **Sync path** | Flag check (cached) + detectors → ~1-5ms |
| **Async path** | Event logging + strike check + flag update |
| **Cache** | `is_flagged` per user, 24h TTL, invalidated on attack |
| **Config** | All thresholds, windows, responses in `config.json` |
| **Extensibility** | Plugin pattern — add detector in 2 steps, no guard changes |

### Scope (Phase 1)

WhatsApp-side attacks only (via Twilio webhook):

| Vector | Detection |
|--------|-----------|
| Message flood | Per-user rate in time window |
| Oversized message | Length > threshold |
| Token/encoding fuzzing | Unicode letter ratio |
| Math/buffer probes | Regex patterns |
| Multilingual jailbreak | Language detection (Hebrew/English only) |

Direct endpoint attacks, prompt injection, media abuse — out of scope (future phases).

## Related Docs

- [draft.md](draft.md) — decision record (Q&A alignment)
- [interfaces.md](interfaces.md) — API contract
- [integration_points.md](integration_points.md) — webhook flow changes
- [package_structure.md](package_structure.md) — module layout
- [schema_migration.md](schema_migration.md) — DB changes
- [deployment_wiring.md](deployment_wiring.md) — systemd, scripts
- [implementation_plan.md](implementation_plan.md) — phased TDD plan
- [manual_test_scenarios.md](manual_test_scenarios.md) — curl test commands
