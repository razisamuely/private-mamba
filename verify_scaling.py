from agent.learners.DreamerLearner import DreamerLearner
from environments import Env


class MockConfig:
    def __init__(self):
        self.COST_LIMIT = 25.0
        self.MAX_STEPS = 1000.0
        self.GAMMA = 0.99
        self.LAGRANGIAN_MULTIPLIER_INIT = 0.0001
        self.LAGRANGIAN_LR = 0.00001
        self.DEVICE = "cpu"
        self.MODEL_LR = 0.0002
        self.ACTOR_LR = 0.0005
        self.VALUE_LR = 0.0005
        self.CAPACITY = 100
        self.SEQ_LENGTH = 10
        self.ACTION_SIZE = 2
        self.IN_DIM = 10
        self.ENV_TYPE = Env.SAFETY_GYM
        self.USE_AVAILABLE_ACTIONS = False
        self.LOG_FOLDER = "mock_logs"
        self.HIDDEN = 256
        self.MODEL_HIDDEN = 256
        self.EMBED = 256
        self.N_CATEGORICALS = 32
        self.N_CLASSES = 32
        self.STOCHASTIC = 1024
        self.DETERMINISTIC = 256
        self.FEAT = 1280
        self.VALUE_LAYERS = 2
        self.VALUE_HIDDEN = 256
        self.ACTION_LAYERS = 2
        self.ACTION_HIDDEN = 256
        self.ENTROPY = 0.001
        self.N_SAMPLES = 1
        self.MIN_BUFFER_SIZE = 10
        self.MODEL_EPOCHS = 1
        self.EPOCHS = 1
        self.PPO_EPOCHS = 1
        self.MODEL_BATCH_SIZE = 1
        self.BATCH_SIZE = 1
        self.GRAD_CLIP = 10.0
        self.GRAD_CLIP_POLICY = 10.0
        self.NORMALIZE_ADVANTAGE = True
        self.ROLLOUT_WITH_TARGET_CRITIC = False


def verify():
    print("Verifying Horizon Scaling Logic...")

    # 1. Test Swimmer Scaling
    config = MockConfig()
    config.COST_LIMIT = 25.0
    config.MAX_STEPS = 1000.0
    config.GAMMA = 0.99

    # Expected: 25 * (100 / 1000) = 2.5
    eff_horizon = 1.0 / (1.0 - config.GAMMA)  # 100
    expected = config.COST_LIMIT * (eff_horizon / config.MAX_STEPS)

    # Mocking wandb to avoid crash
    import sys
    from unittest.mock import MagicMock

    sys.modules["wandb"] = MagicMock()

    # We need to mock DreamerModel and other components that might need CUDA/Big Memory
    import agent.learners.DreamerLearner

    agent.learners.DreamerLearner.DreamerModel = MagicMock()
    agent.learners.DreamerLearner.Actor = MagicMock()
    agent.learners.DreamerLearner.AugmentedCritic = MagicMock()
    agent.learners.DreamerLearner.DreamerMemory = MagicMock()
    agent.learners.DreamerLearner.initialize_weights = MagicMock()

    learner = DreamerLearner(config)

    actual = learner.lagrangian.cost_limit
    print(f"Swimmer Scaling (Limit=25, T=1000, Gamma=0.99):")
    print(f"  Expected Scaled Limit: {expected}")
    print(f"  Actual Scaled Limit:   {actual}")

    assert abs(actual - expected) < 1e-6, f"Mismatch: {actual} != {expected}"
    print("  SUCCESS!")

    # 2. Test StarCraft Scaling
    config.COST_LIMIT = 5.0
    config.MAX_STEPS = 400.0
    # Expected: 5 * (100 / 400) = 1.25
    expected = 5.0 * (100 / 400)
    learner = DreamerLearner(config)
    actual = learner.lagrangian.cost_limit
    print(f"StarCraft Scaling (Limit=5, T=400, Gamma=0.99):")
    print(f"  Expected Scaled Limit: {expected}")
    print(f"  Actual Scaled Limit:   {actual}")
    assert abs(actual - expected) < 1e-6, f"Mismatch: {actual} != {expected}"
    print("  SUCCESS!")


if __name__ == "__main__":
    verify()
