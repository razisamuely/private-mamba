# paths_config.py — file path locations
from pathlib import Path

_SCRIPTS = Path(__file__).parent  # docs/tmp/extraction/scripts/
_EXTRACTION = _SCRIPTS.parent  # docs/tmp/extraction/
_TMP = _EXTRACTION.parent  # docs/tmp/

DEFAULT_INPUT_CSV = _EXTRACTION / "inputs" / "safe_dreamers_runs_adapted.csv"
COLLISION_INPUT_CSV = _EXTRACTION / "inputs" / "collision_runs_adapted.csv"
DEFAULT_CONFIG_JSON = _SCRIPTS / "map_steps_config.json"
DEFAULT_OUTPUT_CSV = _TMP / "aggregated" / "extracted_metrics.csv"
COLLISION_AGG_CSV = _TMP / "aggregated" / "collision_agg.csv"
DEAD_ALLIES_AGG_CSV = _TMP / "aggregated" / "dead_allies_agg.csv"
COLLISION_TEX = _TMP / "tables" / "collision_comparison" / "collision_safedreamer_100k_vs_macpo_5m.tex"
COLLISION_TEX_100K = _TMP / "tables" / "collision_comparison" / "collision_safedreamer_100k_vs_macpo_100k.tex"
DEAD_ALLIES_TEX_DIR = _TMP / "tables" / "appendix_full_comparison"
SAFEPO_AGG_CSV = _TMP / "aggregated" / "all_agg_corrected.csv"
SAFE_DREAMERS_INPUT_CSV = _EXTRACTION / "inputs" / "safe_dreamers_runs_adapted.csv"
