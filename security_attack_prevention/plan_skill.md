# Project Planning Process — Skill Reference

How we go from "new idea" to "ready to implement". Reusable for any future project.

## Process Flow

```
Phase A: Draft (discuss + decide)
  1. Background Research    → web search, read existing code
  2. Draft Creation         → scope, requirements, open questions
  3. Q&A Alignment          → decide each question, update draft after each
  4. Data Model             → tables, fields, how they connect
  5. DB Queries             → list by name + purpose, grouped by caller
  6. Service Architecture   → port, auth, fail behavior, sync/async, cache
  7. Capabilities           → endpoints, who calls them, why
  8. Module Structure       → file tree, responsibilities
  9. Design Patterns        → extensibility, plugin patterns, contracts
  10. Integration Points    → flow position, client module, response flow
  11. Admin UI Touchpoints  → pages/tabs, what data, backing endpoints
  12. Scenarios             → trigger → expected (happy + edge + false positives + infra)

Phase B: Full Docs (expand draft, outside-in)
  13. Full Docs Order       → decide writing order
  14. overview.md           → what & why, key properties
  15. manual_test_scenarios.md → preconditions, setup, trigger, response, side effects, cleanup
  16. interfaces.md         → exact JSON shapes, field types, status codes
  17. integration_points.md → flow position, client/gate modules, code changes
  18. deployment_wiring.md  → systemd, run.sh, deploy scripts, env vars
  19. package_structure.md  → file tree + function/class names per file + dependency flow
  20. schema_migration.md   → SQL, indexes, rollback
  21. implementation_plan.md → phased TDD plan, skeleton-first, status table

Phase C: Implementation
  22. Phase 1: Skeleton     → all files, stubs, models, wiring. Zero logic. Service starts
  23. Phase 2+: TDD         → one function at a time (test → fail → implement → pass)
```

## Step Details

### Phase A: Draft

#### 1. Background Research
- Web search for domain best practices + known vectors
- Read existing codebase to understand current flow
- Output: `background.md` — short table with sources

#### 2. Draft Creation
- `draft.md` with scope, requirements table, open questions
- **Super short** — table format, no prose
- Every decision has a "why"

#### 3. Q&A Alignment
- One question at a time. User decides, Claude proposes options with tradeoffs
- Update draft after each decision — never batch
- Add to config anything that should be tunable

#### 4. Data Model
- Tables and fields needed, how they connect
- No redundant tables — reuse existing where possible
- Add fields to existing tables when possible

#### 5. DB Queries
- List all queries by name (not SQL), grouped by caller (core vs admin)
- Cross-check against capabilities & UI — every screen must have its queries

#### 6. Service Architecture
- Module vs service, port, auth, fail behavior
- Sync vs async split — what blocks response, what runs after
- Cache strategy — what's cached, TTL, invalidation rules

#### 7. Capabilities & Endpoints
- Group by purpose: core, automation, admin, infra
- For each: endpoint, caller, **why it exists**
- Cross-check against UI — every UI action needs a backing endpoint

#### 8. Module Structure
- File tree matching existing project conventions
- Each file: one-line purpose
- Separate pure logic from framework/HTTP code

#### 9. Design Patterns
- Where extensibility matters
- Config-driven activation: enable/disable/reorder without code changes
- Define contract (function signature, return type)

#### 10. Integration Points
- Exact position in existing flow
- Client module + gate module (same pattern as other services)
- **Response flow** — who returns what, who sends the actual message
- Fail behavior from caller's perspective

#### 11. Admin UI Touchpoints
- Every page/tab that needs changes
- Reuse existing UI patterns — avoid new patterns
- Cross-check: every UI element maps to a backing endpoint

#### 12. Scenarios
- Table: # | Scenario | Trigger | Expected
- Cover: each vector, escalation, admin actions, **false positives**, **infra failures**

### Phase B: Full Docs

#### 13. Full Docs Order
- Outside-in recommended: overview → scenarios → interfaces → integration → deployment → structure → schema → implementation plan
- Each doc references draft as source of truth

#### 14-20. Individual Docs
- Each doc takes a draft section and expands with implementation detail
- Draft stays as-is — it's the decision record
- **manual_test_scenarios.md pattern:** preconditions → setup (curl) → trigger (curl) → expected response → side effects → cleanup
- **interfaces.md:** exact JSON request/response shapes, field types, status codes, error format
- **package_structure.md:** file tree + every function/class name + one-line purpose + dependency flow
- **schema_migration.md:** SQL + indexes + rollback

#### 21. Implementation Plan
- **Skeleton-first:** Phase 1 = all files, stubs, models, wiring. Zero logic. Service starts
- **Then TDD:** one function per step (test → fail → implement → pass)
- Status table tracks every step
- Guidelines section: small functions, no hardcoded values, meaningful names/logging, responsibility isolation

## Key Principles

- **Short and accurate** — tables over prose, always
- **Decide then document** — never write docs before alignment
- **Config-driven** — if it might change, put it in config
- **Why before what** — every capability/table/field explains why it exists
- **Cross-check layers** — UI ↔ endpoints ↔ queries ↔ data model must all align
- **One decision at a time** — update draft after each, never batch
- **Outside-in** — user perspective first, internals last
- **Skeleton before logic** — structure works before any business logic
- **Response flow clarity** — always clarify who returns what and who sends the actual user-facing message
- **Scenarios include negatives** — false positives, infra failures, edge cases
