# Baselines at 1M — same-budget comparison (MACPO + MAPPO-Lag)

## Why
Table 3 currently compares CA-MAMBA at 1M steps vs MACPO/MAPPO-Lag at 10M steps.
Adding the baselines' own 1M checkpoints gives a direct same-budget comparison
(reviewers 1QgC/upmo fairness): "same budget we win clearly" + "10x more steps,
they barely catch up". No new runs needed — the 10M WandB histories should
already contain the 1M point.

## Scripts / locations
- Extraction: incremental pattern — import `extract_all`/`aggregate` from
  `docs/tmp/extraction/scripts/mamujoco_pipeline_experiment8.py`
- Main CSV: `docs/tmp/tables/mamujoco_comparison_experiment8/comparison_table_real_20260628_144800.csv` (117 rows)
- Overleaf: `~/workspace/overleaf/thesis` — vendored CSV `data/mamujoco_experiment8_phase5_full.csv`,
  generator `scripts/generate_mamujoco_tables.py`, tests `tests/test_generate_mamujoco_tables.py`

## Steps
1. [x] Pull overleaf repo (`git pull`) — report any supervisor changes
2. [x] Verify WandB coverage at ~1M for the MACPO (6) + MAPPO-Lag (3) runs
3. [x] Extract at `target_steps=1M`, sources `MACPO Run (1M)` / `MAPPO-Lag Run (1M)`.
       SCOPE CHANGE (Raz): results stay in THIS folder only
       (`baselines_1m_per_seed.csv`, `baselines_1m_aggregated.csv`) — main CSV
       NOT touched, no append, no re-render
4. [x] Review numbers with Raz — CA-MAMBA wins 3/3 at matched 1M by 2.8-12x
5. [x] Overleaf: `aaai_additions/` ONLY — `sections/mappo_baseline.tex` table
       (+1M rows) + takeaway, `data/baselines_1m/` vendored CSVs + README,
       `render_test.pdf` rebuilt (12 pages), additions README updated.
       Paper chapters / generated tables / vendored main CSV NOT touched —
       supervisor decides if 1M rows enter Table 3
6. [ ] Commit+push both repos (one informative commit each, after OK)

## Definition of done
`mappo_baseline.tex` shows matched-budget (1M) + 10M rows per env; data vendored
in `aaai_additions/data/baselines_1m/`; render_test.pdf rebuilt; supervisor
notes updated; main paper untouched.
