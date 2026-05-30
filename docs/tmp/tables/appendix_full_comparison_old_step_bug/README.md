# appendix_full_comparison_old_step_bug

## Status
`appendix_table_old_step_bug.pdf` has the correct structure but **stale SafeDreamer data**.

## The Bug
SafeDreamer metrics were extracted at `_step=100k` (WandB internal log counter), which corresponds to ~300k real env steps — results were inflated.

## The Fix
All SafeDreamer experiments were re-run. New runs are tracked in:
`docs/tmp/extraction/inputs/safe_dreamers_runs_adapted.csv`

Extraction uses the `steps` column from the parquet artifact (real env steps), not `_step`.

## TODO
Once new SafeDreamer runs reach 100k real env steps:
1. Run `docs/tmp/extraction/scripts/extract_metrics.py` on `safe_dreamers_runs_adapted.csv`
2. Merge with existing MACPO 5M data (unchanged from paper)
3. Regenerate this table
