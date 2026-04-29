---
name: dev-workflow
description: >
  General development workflow guidelines for the Botivation project.
  Auto-invoked when writing code, creating branches, committing, or opening PRs.
---

# Development Workflow Skill

## Branching

All changes on feature branches — never push to `main` directly.

**Naming:** `<type>/<scope>-<short-description>`
- Examples: `feat/inspectors-sentiment`, `fix/scheduler-duplicates`, `refactor/gemini-json-repair`

## Commits

[Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <short description>
```

**Types:** `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `style`

**Scopes:** `webhook`, `messaging`, `onboarding`, `scheduler`, `inspectors`, `admin`, `database`, `services`, `config`, `utils`, `gemini`, `claude`, `tools`, `prompts`, `deploy`, `tests`

Rules:
- Subject line under 72 characters
- Imperative mood ("add", not "added")

## CI Verification (Mandatory)

After every `git push`:

1. Find the triggered run via `gh run list`
2. Wait for completion via `gh run watch <run-id>`
3. If all jobs pass — done
4. If any job fails:
   - Fetch logs: `gh run view <run-id> --log-failed`
   - Diagnose root cause
   - Present fix to user — do not silently implement
   - After approval: fix, commit, push, repeat

Never skip this step. Never leave a push with failing CI.

## Pull Requests

Every PR must include:

```markdown
## Summary
<1-3 bullet points: what changed and why>

## Changes
<File-by-file or area-by-area breakdown>

## Test plan
- [ ] <Verification steps>
```

## Python Code Style

- **Formatting:** `ruff check` before committing
- **Type hints:** On all function signatures
- **Type checking:** `mypy`
- **Async:** Use async for webhook handlers and DB queries where possible
- **Imports:** stdlib → third-party → local, blank lines between groups
- **Naming:** `snake_case` functions/variables, `PascalCase` classes, `UPPER_SNAKE` constants

## Testing

- Place tests in `tests/` mirroring source structure
- Use `pytest-asyncio` for async, `freezegun` for time, `pytest-mock` for mocking
- Naming: `test_<what>_<expected_behavior>`

## Database Schema

`Botivation/database/schema.sql` is the single source of truth for all table definitions.

**Update it whenever you:**
- Add a new table → add the full `CREATE TABLE` block
- Add a column via migration → add the column inline with an `-- added via migration` comment
- Add or remove an index or constraint

Do this in the same commit as the migration script. Never let `schema.sql` drift from the actual DB.

## Error Handling

- Use `log_system_error()` for operational errors
- Every request gets a trace ID via `TraceIdMiddleware`
- Never hardcode credentials — use environment variables

## Clean Architecture (enforced patterns)

These patterns are enforced on every code review. Violations must be fixed before merging.

### SQL — separate constants file, named column access

- SQL strings belong in a dedicated `sql.py` (constants only). Execution functions in `queries.py` import from there. Never write inline SQL elsewhere.
- Never access result columns by index (`row[0]`). Use `row._mapping["col_name"]`.
- Column name strings are also constants — defined in `sql.py` as a small class and imported everywhere. Never hardcode column name strings at call sites.

### Domain constants / Enums — single source of truth

All status strings, trigger modes, and domain values live in one place and are imported everywhere. Never hardcode raw strings at call sites. When adding a new value, add it to the central class — not inline.

### Models — dedicated file, not in routes

Pydantic request/response models belong in a dedicated `models.py`, not inside `routes.py`. Routes import from models.

### Layer boundaries

```
routes (handlers)   →  dispatch only, no business logic
services/           →  orchestrate; no raw DB calls
database/queries    →  all SQL, all DB access
database/async_queries  →  async + cache-first wrappers around queries
```

- Services must not call the DB directly — go through the queries layer.
- Routes must not embed SQL or business logic — delegate to a service.

### Extract complex expressions to named functions

Any non-trivial inline expression must be extracted to a private function with a meaningful name that describes *what* it produces, not *how*.

### Cache-first DB access

All DB reads going through the async layer must check cache before hitting the DB.

```python
async def get_conversation_details_async(conversation_id: str):
    cache_key = f"conv_details:{conversation_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    details = await run_in_executor(get_conversation_details, conversation_id)
    if details:
        cache.set(cache_key, details)
    return details
```

## Pre-Commit Self-Review Checklist

**Run this against your diff before every `git commit`.** The `ruff`/`mypy` hook catches mechanical issues automatically — this checklist covers judgment-based violations that tools cannot detect.

```
[ ] No raw strings at call sites — domain values imported from a constants class?
[ ] No business logic inline in route handlers — delegated to a service/helper?
[ ] Non-trivial inline expressions extracted to a named private function?
[ ] Operational errors use log_system_error(), not bare logger.error()?
[ ] Layer boundaries respected (routes → services → queries)?
[ ] New dict key strings defined as class constants, not scattered literals?
[ ] SQL only in sql.py/queries.py, never inline elsewhere?
[ ] Pydantic models in models.py, not inside routes?
```

If any box is unchecked, fix before committing — not after review feedback.
