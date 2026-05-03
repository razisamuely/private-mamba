# Table Generation Guide

## Tables location
`docs/tmp/tables/` — all generated tables (tex + pdf)

## Table types

### 1. dead_allies_incremental full comparison (SafeDreamers vs SafePO)
**Source**: `docs/tmp/aggregated/all_agg_150k.csv` (or 100k/200k variants)  
**Template**: `docs/tmp/tables/appendix_full_comparison_old_step_bug/appendix_table_old_step_bug.tex` (structure only — data is old/buggy)

### 2. collision comparison (SafeDreamers vs MACPO)
**Source**: `docs/tmp/extraction/inputs/collision_runs_adapted.csv` → run `extract_metrics.py` → aggregate  
**Current table**: `docs/tmp/tables/collision_comparison/collision_safedreamer_vs_macpo.{tex,pdf}`  
**Status**: partial — several MACPO runs cancelled, need resubmission (see below)

### 3. bug fix step axis tables
**Source**: `docs/tmp/aggregated/all_agg_{100k,150k,200k}.csv`  
**Output**: `docs/tmp/tables/bug_fix_step_axis/bug_impact_{100k,150k,200k}.{tex,pdf}`

### 4. lag fix comparison
**Source**: `docs/tmp/aggregated/old_agg_corrected.csv` vs `new_agg.csv`  
**Output**: `docs/tmp/tables/lag_fix_comparison/lag_cost_fix_vs_lag_episode_cost.{tex,pdf}`

---

## How to extract metrics

```bash
export WANDB_API_KEY=$(grep WEIGHT_AND_BIASES /home/corsound/workspace/overleaf/.env | cut -d= -f2)
cd /home/corsound/workspace/private-mamba/docs/tmp/extraction/scripts

# Edit map_steps_config.json to set target steps per map, then:
/home/corsound/workspace/overleaf/thesis/venv/bin/python3 extract_metrics.py \
    --config map_steps_config.json \
    2>/dev/null | tee extracted_Xk.txt
```

## How to compile a tex fragment to PDF

```bash
cat > /tmp/compile.tex << 'EOF'
\documentclass{article}
\usepackage{booktabs,longtable,xcolor,geometry}
\geometry{margin=1cm,landscape}
\begin{document}
\input{/path/to/your_table.tex}
\end{document}
EOF
pdflatex -interaction=nonstopmode /tmp/compile.tex
```

---

## Collision MACPO run status (as of 2026-05-03)

Most MACPO collision jobs were cancelled before 5M steps. Completed: MMM s2 (10M) ✅, 8m s3 (10M) ✅

| Map | Seeds needing resubmission |
|-----|---------------------------|
| MMM | s3 (cancelled at 5.7M) |
| 3s5z_vs_3s6z | s1, s2, s3 (cancelled at 2.8–7.2M) |
| bane_vs_bane | s1, s2 (cancelled <1M); s3 still running |
| 8m | s1, s2 (cancelled) |

To resubmit:
```bash
cd /home/corsound/workspace/Safe-Policy-Optimization
python3 sbatch_scripts/submit_baseline.py \
    --tasks MMM 3s5z_vs_3s6z bane_vs_bane 8m \
    --seeds 1 2 3 \
    --cost_limits 0.0 \
    --cost_type collision
```
