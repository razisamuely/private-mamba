# extraction_config.py — metric extraction parameters
WINDOW_SIZE = 5000  # steps before target to average over
HISTORY_SAMPLES = 2_000_000  # max rows to fetch from wandb history
DEFAULT_TARGET_STEP = 500_000
METRIC_KEYS = ["main/score", "main/cost", "main/winrate"]
STEP_COL = "steps"  # env steps column (SafeDreamer parquet)
FALLBACK_STEP_COL = "_step"  # wandb internal step (MACPO history)

# WandB artifact
HISTORY_ARTIFACT_TYPE = "wandb-history"
HISTORY_ARTIFACT_NAME_SUBSTR = "history"

# CSV column names
CSV_COL_WANDB_LINK = "wandb_link"
CSV_COL_MAP = "map"
CSV_COL_ALGORITHM = "algorithm"
CSV_COL_COST_LIMIT = "cost_limit"
CSV_COL_SEED = "seed"

# WandB URL marker
WANDB_URL_MARKER = "wandb.ai"
WANDB_URL_RUNS_SEGMENT = "/runs/"

# Parquet file extension
PARQUET_EXT = ".parquet"

# Dead allies pipeline
DEAD_ALLIES_MAPS_ORDER = [
    "1c3s5z",
    "2m_vs_1z",
    "2s3z",
    "2s_vs_1sc",
    "3m",
    "3s5z_vs_3s6z",
    "3s_vs_3z",
    "3s_vs_4z",
    "3s_vs_5z",
    "8m",
    "MMM",
    "bane_vs_bane",
]
SAFEPO_STEP_LABEL = "5M"
SD_STEP_LABEL = "100k"
CSV_COL_REACHED = "reached_target"
COLLISION_MAPS_ORDER = [
    "2s_vs_1sc",
    "3m",
    "2s3z",
    "3s_vs_3z",
    "3s_vs_4z",
    "3s_vs_5z",
    "8m",
    "MMM",
    "3s5z_vs_3s6z",
    "bane_vs_bane",
]
MACPO_STEP_LABEL = {5_000_000: "5M", 100_000: "100k"}
TABLE_MISSING = "—"
TABLE_COL_SCORE = "score"
TABLE_COL_COST = "cost"
TABLE_COL_WINRATE = "winrate"
AGG_METRICS = [TABLE_COL_SCORE, TABLE_COL_COST, TABLE_COL_WINRATE]
