# Task 1 — MAPPO-Lag on all environments — working notes

## Status (2026-09-01)

### SMAC (current focus)
- Two batches of MAPPO-Lag SMAC runs found on cluster (SafePO repo
  `~/workspace/Safe-Policy-Optimization-Modified`, 5M steps, cost =
  dead_allies_incremental):
  - **Batch A** (19597923–19598044, 07-27): pre winrate-logging → **superseded, ignore**
  - **Batch B** (19601155–173, 07-28): with winrate logging → **canonical**
- Batch B status: 15/18 COMPLETED — 2m_vs_1z (c=0,1 ×3 seeds), 8m (c=0,4 ×3),
  1c3s5z (c=0 ×3)
- bane_vs_bane (c=0 ×3): **OOM in both batches** — 4G RAM, killed at ~1.6M/5M
  steps (32%), FPS≈13. Fix when resumed: mem 16–32G, longer walltime (~5+ days),
  maybe fewer --num-envs. **Parked for later review.**

### Extraction results (2026-09-01)
- 15 Batch B runs extracted via `extract_mappolag_smac.py` →
  `mappolag_smac_per_seed.csv` + `mappolag_smac_agg.csv`
- All near-perfect winrate; **cost over limit at c=0 on 1c3s5z (0.44) and 8m
  (0.90)** — same "not under threshold" issue as supervisor point 3
- ⚠️ 2m_vs_1z c=0 seed1 (wandb "failed") logged only to 3.01M/5M steps, but
  fully converged (score 20, cost 0) — kept
- Main CSVs / PDFs NOT updated yet (deliberate)

### Next steps
1. [x] Extract 15 Batch B SMAC runs from WandB
2. [ ] MAMuJoCo seed-count check: main Exp 8 CSV has only **1 MAPPO-Lag row per
       env** (HC 2x3, Ant 2x4, Ant 4x2) vs 12 for SafeDreamer — verify how many
       seeds behind each row; if 1 seed, run more. **Do right after SMAC.**
3. [ ] bane_vs_bane resubmission — later
4. [ ] Update stale Exp 6 baseline_runs.md (Batch A marked RUNNING, superseded)

### Out of scope
- Shadow-hand (Exp 10) — not part of thesis
- Exp 9 no-comm SafeDreamer runs — deprioritized
