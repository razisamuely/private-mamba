# Task 1 — MAPPO-Lag on all environments — working notes

## Status (2026-09-15)

### SMAC

- **Batch A** (19597923–19598044, 07-27): pre winrate-logging → **superseded, ignore**
- **Batch B** (19601155–173, 07-28): 15 runs (2m_vs_1z, 8m, 1c3s5z c=0) → extracted
- **Batch C** (20816199–786, 09-01): 51 runs across all remaining maps → 41 finished,
  10 completed during extraction. All reached 5M steps.
  - 2 auto-restarted (3s_vs_3z c=0 s3, MMM c=0 s3) — crashed runs skipped at extraction
- **bane_vs_bane** (20905593–603, 09-06, 128G RAM): 5/6 COMPLETED at 5M,
  1 TIMEOUT (c=0 s1, 4.52M/5M, FPS=7). Used as-is — 90% done, converged.

### Extraction results (2026-09-15)

- 72 runs extracted at **5 checkpoints** (100k, 500k, 1M, 2M, 5M) via `extract_mappolag_smac.py`
- 12 maps × 2 cost limits × 3 seeds = 72 rows per checkpoint (incl. bane_vs_bane)
- CSVs: `mappolag_smac_per_seed{_100k,_500k,_1M,_2M,}.csv` + `mappolag_smac_agg{...}.csv`
- Appendix table updated: `docs/tmp/tables/appendix_full_comparison/appendix_table_corrected.pdf` (120 rows)

**Key findings:**
- Easy maps (2m_vs_1z, 3m, 2s_vs_1sc, 3s_vs_3z): converge by 500k–1M, ~100% WR, ~0 cost
- Medium maps (2s3z, 8m, 1c3s5z): jump 500k→1M, finish by 5M (97–100% WR)
- Late learners (MMM, 3s_vs_3z): 0% at 1M → 97–99% at 5M
- Hard maps (3s_vs_4z, 3s_vs_5z, 3s5z_vs_3s6z): 0% WR at all checkpoints — MAPPO-Lag cannot solve
- **bane_vs_bane**: 100% WR at 5M, cost ~5.2 (above limit, same pattern)
- **Cost limit has almost no effect** — c=0 vs nonzero barely changes WR or cost on any map
- Cost still above 0 on solved maps — same "above threshold" pattern as supervisor point 3

### Next steps
1. [x] Extract all SMAC runs at multiple checkpoints
2. [x] bane_vs_bane resubmission (128G) — done, extracted
3. [x] Add bane_vs_bane to appendix table
4. [ ] MAMuJoCo seed-count check: main Exp 8 CSV has only **1 MAPPO-Lag row per
       env** (HC 2x3, Ant 2x4, Ant 4x2) — verify how many seeds; if 1, run more
5. [ ] Update stale Exp 6 baseline_runs.md (Batch A marked RUNNING, superseded)

### Out of scope
- Shadow-hand (Exp 10) — not part of thesis
- Exp 9 no-comm SafeDreamer runs — deprioritized
