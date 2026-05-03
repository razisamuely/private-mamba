# paths_config.py — file path locations
from pathlib import Path

_SCRIPTS = Path(__file__).parent  # docs/tmp/extraction/scripts/
_EXTRACTION = _SCRIPTS.parent  # docs/tmp/extraction/
_TMP = _EXTRACTION.parent  # docs/tmp/

DEFAULT_INPUT_CSV = _EXTRACTION / "inputs" / "safe_dreamers_runs_adapted.csv"
DEFAULT_CONFIG_JSON = _SCRIPTS / "map_steps_config.json"
DEFAULT_OUTPUT_CSV = _TMP / "aggregated" / "extracted_metrics.csv"
