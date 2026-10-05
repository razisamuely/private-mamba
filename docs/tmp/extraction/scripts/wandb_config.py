# wandb_config.py — WandB API connection settings
WANDB_PROJECT = "raz-shmueli-corsound-ai/private-mamba"
WANDB_TIMEOUT = 60

try:
    from wandb_config_local import *  # noqa: F401,F403
except ImportError:
    pass
