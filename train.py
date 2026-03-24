import argparse
import time
from pathlib import Path

import wandb
from agent.runners.DreamerRunner import DreamerRunner
from agent.workers.DreamerWorker import DreamerWorker
from configs import (
    DeadlockPunishmentConfig,
    Experiment,
    NearRewardConfig,
    RewardsComposerConfig,
    SimpleObservationConfig,
)
from configs.dreamer.DreamerControllerConfig import DreamerControllerConfig
from configs.dreamer.DreamerLearnerConfig import DreamerLearnerConfig
from configs.EnvConfigs import EnvCurriculumConfig
from configs.flatland.RewardConfigs import FinishRewardConfig
from configs.flatland.TimetableConfigs import AllAgentLauncherConfig
from env.flatland.params import LotsOfAgents, PackOfAgents, SeveralAgents

# from env.mpe.vmas_simple_spread import VmasSpread
from env.safety_gym.SwimmerWrapper import SwimmerWrapper as SafetyGymWrapper

# from env.starcraft.StarCraft import StarCraft
from env.starcraft.StarCraft_safe import StarCraft
from env.vmas.balance import VmasBalance
from environments import FLATLAND_ACTION_SIZE, FLATLAND_OBS_SIZE, Env, FlatlandType

# from env.safetygym.SafetyGymWrapper import SafetyGymWrapper


def run_one_process_one_env_debug(exp):

    learner = exp.learner_config.create_learner()
    dreamer_single_worker = DreamerWorker(0, exp.env_config, exp.controller_config)

    cur_steps, cur_episode = 0, 0

    import wandb

    wandb.define_metric("steps")
    wandb.define_metric("reward", step_metric="steps")
    wandb.define_metric("cost", step_metric="steps")
    wandb.define_metric("score", step_metric="steps")

    while True:

        rollout, info = dreamer_single_worker.run(learner.params())

        learner.step(rollout)

        cur_steps += info["steps_done"]
        cur_episode += 1

        wandb.log({"reward": info["reward"], "steps": cur_steps})
        wandb.log({"cost": info["cost"], "steps": cur_steps})
        wandb.log({"score": info["score"], "steps": cur_steps})
        print(
            f"Episode {cur_episode}, Samples {learner.total_samples}, Reward {info['reward']}, Cost {info['cost']}, Score {info['score']}"
        )

        if cur_episode >= exp.episodes or cur_steps >= exp.steps:
            break

        if cur_episode % 10 == 0:
            model_path = Path(wandb.run.dir) / f"model_episode_{cur_episode}.pt"
            model_path = f"model_episode_{cur_episode}.pt"
            learner.save_model(model_path)


def parse_args():
    parser = argparse.ArgumentParser()
    # parser.add_argument("--env", type=str, default="simple_spread", help="Flatland or SMAC env")
    # parser.add_argument("--env_name", type=str, default="simple_spread", help="Specific setting")
    # parser.add_argument("--env", type=str, default="balance", help="Flatland or SMAC env")
    # parser.add_argument("--env_name", type=str, default="balance", help="Specific setting")
    parser.add_argument("--env", type=str, default="starcraft", help="Flatland or SMAC env")
    parser.add_argument("--env_name", type=str, default="8m", help="Specific setting")
    parser.add_argument("--cost_type", type=str, default="dead_allies_incremental", help="Specific setting")
    # parser.add_argument("--env", type=str, default="safety_gym", help="Flatland or SMAC env")
    # parser.add_argument("--env_name", type=str, default="SafetyPointMultiGoal1-v0", help="Specific setting")
    parser.add_argument("--n_workers", type=int, default=4, help="Number of workers")
    parser.add_argument("--cost_limit", type=float, default=25.0, help="Cost limit for Lagrangian methods")
    parser.add_argument("--seed", type=int, default=23, help="Random seed")
    parser.add_argument("--algo_name", type=str, default="safedreamer", help="Algorithm name")
    parser.add_argument("--laglr", type=float, default=0.00001, help="Lagrangian learning rate")
    parser.add_argument("--cost_priority", type=float, default=0.0, help="Cost prioritized sampling ratio")
    parser.add_argument("--slurm_id", type=str, default="none", help="Slurm Job ID")
    parser.add_argument("--branch", type=str, default="unknown", help="Git branch name")
    parser.add_argument("--steps", type=int, default=10**10, help="Total number of steps")
    parser.add_argument("--episodes", type=int, default=50000, help="Total number of episodes")
    return parser.parse_args()


def train_dreamer(exp, n_workers, debug=True):
    if debug:
        run_one_process_one_env_debug(exp)
        return

    runner = DreamerRunner(exp.env_config, exp.learner_config, exp.controller_config, n_workers)
    runner.run(exp.steps, exp.episodes)


def get_env_info(configs, env):
    for config in configs:
        config.IN_DIM = env.n_obs
        config.ACTION_SIZE = env.n_actions
    env.close()


def get_env_info_flatland(configs):
    for config in configs:
        config.IN_DIM = FLATLAND_OBS_SIZE
        config.ACTION_SIZE = FLATLAND_ACTION_SIZE


def prepare_starcraft_configs(args):
    agent_configs = [DreamerControllerConfig(), DreamerLearnerConfig(cost_limit=args.cost_limit)]
    for config in agent_configs:
        if hasattr(config, "LAGRANGIAN_LR"):
            config.LAGRANGIAN_LR = args.laglr
        if hasattr(config, "COST_PRIORITY_RATIO"):
            config.COST_PRIORITY_RATIO = args.cost_priority
    env_config = StarCraft(args.env_name, args.cost_type)
    get_env_info(agent_configs, env_config.create_env())
    return {
        "env_config": (env_config, 100),
        "controller_config": agent_configs[0],
        "learner_config": agent_configs[1],
        "reward_config": None,
        "obs_builder_config": None,
    }


def prepare_simple_spread_configs(env_name, cost_limit=180.0):
    agent_configs = [DreamerControllerConfig(), DreamerLearnerConfig(cost_limit=cost_limit)]
    env_config = VmasSpread(env_name)
    get_env_info(agent_configs, env_config.create_env())
    return {
        "env_config": (env_config, 100),
        "controller_config": agent_configs[0],
        "learner_config": agent_configs[1],
        "reward_config": None,
        "obs_builder_config": None,
    }


def prepare_vmas_balance_configs(env_name, cost_limit=180.0):
    agent_configs = [DreamerControllerConfig(), DreamerLearnerConfig(cost_limit=cost_limit)]
    env_config = VmasBalance(env_name, n_agents=2, device="cpu", seed=42, max_steps=100)
    get_env_info(agent_configs, env_config.create_env())
    return {
        "env_config": (env_config, 100),
        "controller_config": agent_configs[0],
        "learner_config": agent_configs[1],
        "reward_config": None,
        "obs_builder_config": None,
    }


def prepare_safety_gym_configs(args):
    """Refined dynamic configuration for Safety-Gymnasium tasks."""
    agent_configs = [DreamerControllerConfig(), DreamerLearnerConfig(cost_limit=args.cost_limit)]
    env_config = SafetyGymWrapper(args.env_name)

    # Initialize real env briefly to capture meta-data (n_obs, n_actions)
    real_env = env_config.create_env()
    real_env._initialize_env()
    get_env_info(agent_configs, real_env)

    return {
        "env_config": (env_config, 100),
        "controller_config": agent_configs[0],
        "learner_config": agent_configs[1],
        "reward_config": None,
        "obs_builder_config": None,
    }


def prepare_flatland_configs(env_name, cost_limit=180.0):
    if env_name == FlatlandType.FIVE_AGENTS:
        env_config = SeveralAgents(RANDOM_SEED + 100)
    elif env_name == FlatlandType.TEN_AGENTS:
        env_config = PackOfAgents(RANDOM_SEED + 100)
    elif env_name == FlatlandType.FIFTEEN_AGENTS:
        env_config = LotsOfAgents(RANDOM_SEED + 100)
    else:
        raise Exception("Unknown flatland environment")
    obs_builder_config = SimpleObservationConfig(
        max_depth=3, neighbours_depth=3, timetable_config=AllAgentLauncherConfig()
    )
    reward_config = RewardsComposerConfig(
        (FinishRewardConfig(finish_value=10), NearRewardConfig(coeff=0.01), DeadlockPunishmentConfig(value=-5))
    )
    agent_configs = [DreamerControllerConfig(), DreamerLearnerConfig(cost_limit=cost_limit)]
    get_env_info_flatland(agent_configs)
    return {
        "env_config": (env_config, 100),
        "controller_config": agent_configs[0],
        "learner_config": agent_configs[1],
        "reward_config": reward_config,
        "obs_builder_config": obs_builder_config,
    }


if __name__ == "__main__":
    args = parse_args()
    RANDOM_SEED = args.seed

    current_run_time = time.strftime("date%m-%d-hr%H-%M-%S", time.localtime())
    # temp_config = DreamerLearnerConfig()

    # Standardized Naming Convention
    # {algo}_{costtype}_{env}_{laglr}_{costlim}_{map}_{seed}_{time}_{slurm_id}_{branch}
    sanitized_branch = args.branch.replace("/", "-")
    run_name = (
        f"{args.algo_name}_{args.cost_type}_{args.env}_"
        f"lag{args.laglr}_{args.cost_limit}_{args.env_name}_"
        f"s{args.seed}_{current_run_time}_{args.slurm_id}_{sanitized_branch}"
    )

    wandb.init(
        name=run_name,
        id=run_name,
    )
    if args.env == Env.FLATLAND:
        configs = prepare_flatland_configs(args.env_name, args.cost_limit)
    elif args.env == Env.STARCRAFT:
        configs = prepare_starcraft_configs(args)
    elif args.env == Env.SIMPLE_SPREAD:
        configs = prepare_simple_spread_configs(args.env_name, args.cost_limit)
    elif args.env == Env.VMAS_BALANCE:
        configs = prepare_vmas_balance_configs(args.env_name, args.cost_limit)
    elif args.env == Env.SAFETY_GYM:
        configs = prepare_safety_gym_configs(args)
    else:
        raise Exception("Unknown environment")
    configs["env_config"][0].ENV_TYPE = Env(args.env)
    configs["learner_config"].ENV_TYPE = Env(args.env)
    configs["controller_config"].ENV_TYPE = Env(args.env)

    exp = Experiment(
        steps=args.steps,
        episodes=args.episodes,
        random_seed=RANDOM_SEED,
        env_config=EnvCurriculumConfig(
            *zip(configs["env_config"]),
            Env(args.env),
            obs_builder_config=configs["obs_builder_config"],
            reward_config=configs["reward_config"],
        ),
        controller_config=configs["controller_config"],
        learner_config=configs["learner_config"],
    )

    train_dreamer(exp, n_workers=args.n_workers, debug=False)
