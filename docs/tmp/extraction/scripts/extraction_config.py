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
