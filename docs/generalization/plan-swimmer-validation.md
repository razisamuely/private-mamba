# Swimmer validation & fix plan

Work branch: `feat/swimmer-action-fix` (from `feat/generalization-swimmer-port`).

## Two targets (in order)

1. **Actions** — Correct discrete → continuous mapping in `env/safety_gym/SwimmerWrapper.py` (full vector per agent, match `action_space(agent).shape`). Wrong actions invalidate everything else.
2. **Cost** — Same units from env → log → learner; set **limit / normalization** for Swimmer (do not reuse SMAC numbers blindly).

## Two runs (not three)

| Run | When | What it validates |
|-----|------|-------------------|
| **A** | After **target 1** only | Behavior + **`main/score`** / **`main/cost`** look plausible (controls OK). Log whatever exists; don’t over-interpret **λ** yet. |
| **B** | After **target 2** | **Same metrics** + **Agent/Lagrangian** — this run checks **1 + 2** together; constraint loop is believable. Prefer **≥ 50k steps**; **λ** should not drift up forever without a clear cause. |

Run **B** is the combined check — no separate “1+2 only” run after that unless you want a longer bake-off.

## After Run B

- **Lagrangian / `laglr`:** adjust only if actions and cost are already fixed and **λ** is still pathological.
- **W&B:** clear names for episode return vs win-style metrics; don’t compare Swimmer to SMAC on the same “winrate” panel.
- **Optional:** MACPO / SafePO comparison **only** with matching action + cost semantics.

## Definition of Done

- [ ] **Target 1** done + **Run A** completed and reviewed.
- [ ] **Target 2** done + **Run B** completed; score, cost, and Lagrangian interpretable on one time axis.
- [ ] **Optional:** baseline comparison as above.

Then this validation phase is **done**; full experiment grids are a **follow-up**.

---

## Token-lite summary (paste / reminders)

Branch `feat/swimmer-action-fix`. (1) Fix `SwimmerWrapper` continuous actions. (2) Align cost units + Swimmer `cost_limit`. Run **A** after (1): score/cost sanity. Run **B** after (2): full check incl. λ, ~50k+. Tune `laglr` only after B if needed.
