"""Smoke test: run a few episodes on HalfCheetah and Ant, check no crash/NaN."""

import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import torch  # noqa: E402

import wandb  # noqa: E402

wandb.init = MagicMock()
wandb.log = MagicMock()
wandb.define_metric = MagicMock()

from configs.dreamer.DreamerControllerConfig import (  # noqa: E402
    DreamerControllerConfig,
)
from configs.dreamer.DreamerLearnerConfig import DreamerLearnerConfig  # noqa: E402
from env.safety_gym.MAMuJoCoWrapper import MAMuJoCoWrapper  # noqa: E402


def run_smoke(env_name, n_episodes=3):
    print(f"\n=== Smoke test: {env_name} ({n_episodes} episodes) ===")

    env_wrapper = MAMuJoCoWrapper(env_name, action_type="continuous")
    env = env_wrapper.create_env()
    obs = env.reset()

    # Configure
    ctrl_cfg = DreamerControllerConfig()
    learn_cfg = DreamerLearnerConfig(cost_limit=25.0)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    for cfg in [ctrl_cfg, learn_cfg]:
        cfg.IN_DIM = obs[0].shape[0]
        cfg.ACTION_SIZE = env.n_actions
        cfg.ACTION_TYPE = "continuous"
        cfg.USE_AVAILABLE_ACTIONS = False
        if hasattr(cfg, "DEVICE"):
            cfg.DEVICE = device

    from environments import Env

    ctrl_cfg.ENV_TYPE = Env.SAFETY_GYM
    learn_cfg.ENV_TYPE = Env.SAFETY_GYM

    # Create controller (non-Ray, debug mode)
    learn_cfg.create_learner()  # initializes wandb etc
    controller = ctrl_cfg.create_controller()

    all_rewards = []
    all_actions = []
    nan_detected = False

    for ep in range(n_episodes):
        obs_dict = env.reset()
        controller.init_rnns()
        controller.init_buffer()
        done = {i: False for i in range(env.n_agents)}
        ep_reward = 0.0
        steps = 0

        while not all(done.values()) and steps < 200:
            observations = torch.cat(
                [
                    (
                        obs_dict[i].unsqueeze(0)
                        if isinstance(obs_dict[i], torch.Tensor)
                        else torch.tensor(obs_dict[i]).float().unsqueeze(0)
                    )
                    for i in range(env.n_agents)
                ]
            ).unsqueeze(0)
            actions = controller.step(observations, None, None)

            # Check for NaN in actions
            if torch.isnan(actions).any():
                print(f"  NaN in actions at step {steps}!")
                nan_detected = True
                break

            all_actions.append(actions.detach().cpu())
            action_list = [actions[i].detach().cpu().numpy() for i in range(env.n_agents)]
            obs_dict, rewards, dones, info = env.step(action_list)
            done = dones
            ep_reward += sum(rewards.values()) / env.n_agents
            steps += 1

        all_rewards.append(ep_reward)
        print(f"  Episode {ep+1}: reward={ep_reward:.2f}, steps={steps}")

    env.close()

    # Assertions
    assert not nan_detected, "NaN detected in actions!"

    actions_cat = torch.cat(all_actions, dim=0)
    mean_action = actions_cat.mean().item()
    max_action = actions_cat.abs().max().item()
    print(f"  Action stats: mean={mean_action:.4f}, max_abs={max_action:.4f}")

    # Actions should be in (-1, 1) from tanh
    assert max_action <= 1.0 + 1e-6, f"Actions out of bounds: max_abs={max_action}"

    # Actions should NOT be all compressed near 0
    assert actions_cat.abs().mean().item() > 0.01, "Actions too compressed near 0"

    # Reward should be non-zero (agent is doing something)
    assert any(r != 0 for r in all_rewards), "All rewards are zero — agent may not be acting"

    print(f"  PASS: {env_name}")
    return True


if __name__ == "__main__":
    ok = True
    for env_name in ["Safety2x3HalfCheetahVelocity-v0", "Safety2x4AntVelocity-v0"]:
        try:
            run_smoke(env_name, n_episodes=3)
        except Exception as e:
            print(f"  FAIL: {env_name} — {e}")
            import traceback

            traceback.print_exc()
            ok = False

    if ok:
        print("\nAll smoke tests passed.")
    else:
        print("\nSome smoke tests FAILED.")
        sys.exit(1)
