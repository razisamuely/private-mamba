import argparse
from pathlib import Path

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
from env.mpe.vmas_simple_spread import VmasSpread
from env.safetygym.SafetyGymWrapper import SafetyGymWrapper
from env.starcraft.StarCraft import StarCraft
from env.vmas.balance import VmasBalance
from environments import FLATLAND_ACTION_SIZE, FLATLAND_OBS_SIZE, Env, FlatlandType


def run_one_process_one_env_debug(exp):

    learner = exp.learner_config.create_learner()
    dreamer_single_worker = DreamerWorker(0, exp.env_config, exp.controller_config)

    cur_steps, cur_episode = 0, 0

    import wandb

    wandb.define_metric("steps")
    wandb.define_metric("reward", step_metric="steps")
    wandb.define_metric("cost", step_metric="steps")

    while True:

        rollout, info = dreamer_single_worker.run(learner.params())

        learner.step(rollout)

        cur_steps += info["steps_done"]
        cur_episode += 1

        wandb.log({"reward": info["reward"], "steps": cur_steps})
        wandb.log({"cost": info["cost"], "steps": cur_steps})
        print(f"Episode {cur_episode}, Samples {learner.total_samples}, Reward {info['reward']}")

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
    # parser.add_argument("--env", type=str, default="starcraft", help="Flatland or SMAC env")
    # parser.add_argument("--env_name", type=str, default="2s_vs_1sc", help="Specific setting")
    parser.add_argument("--env", type=str, default="safety_gym", help="Flatland or SMAC env")
    parser.add_argument("--env_name", type=str, default="SafetyPointMultiGoal1-v0", help="Specific setting")
    parser.add_argument("--n_workers", type=int, default=4, help="Number of workers")
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


def prepare_starcraft_configs(env_name):
    agent_configs = [DreamerControllerConfig(), DreamerLearnerConfig()]
    env_config = StarCraft(env_name)
    get_env_info(agent_configs, env_config.create_env())
    return {
        "env_config": (env_config, 100),
        "controller_config": agent_configs[0],
        "learner_config": agent_configs[1],
        "reward_config": None,
        "obs_builder_config": None,
    }


def prepare_simple_spread_configs(env_name):
    agent_configs = [DreamerControllerConfig(), DreamerLearnerConfig()]
    env_config = VmasSpread(env_name)
    get_env_info(agent_configs, env_config.create_env())
    return {
        "env_config": (env_config, 100),
        "controller_config": agent_configs[0],
        "learner_config": agent_configs[1],
        "reward_config": None,
        "obs_builder_config": None,
    }


def prepare_vmas_balance_configs(env_name):
    agent_configs = [DreamerControllerConfig(), DreamerLearnerConfig()]
    env_config = VmasBalance(env_name, n_agents=2, device="cpu", seed=42, max_steps=100)
    get_env_info(agent_configs, env_config.create_env())
    return {
        "env_config": (env_config, 100),
        "controller_config": agent_configs[0],
        "learner_config": agent_configs[1],
        "reward_config": None,
        "obs_builder_config": None,
    }


def prepare_safety_gym_configs(env_name):
    agent_configs = [DreamerControllerConfig(), DreamerLearnerConfig()]
    env_config = SafetyGymWrapper(env_name)
    # get_env_info(agent_configs, env_config.create_env())
    for config in agent_configs:
        config.IN_DIM = 152  # From your output
        config.ACTION_SIZE = 9
    return {
        "env_config": (env_config, 100),
        "controller_config": agent_configs[0],
        "learner_config": agent_configs[1],
        "reward_config": None,
        "obs_builder_config": None,
    }


def prepare_flatland_configs(env_name):
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
    agent_configs = [DreamerControllerConfig(), DreamerLearnerConfig()]
    get_env_info_flatland(agent_configs)
    return {
        "env_config": (env_config, 100),
        "controller_config": agent_configs[0],
        "learner_config": agent_configs[1],
        "reward_config": reward_config,
        "obs_builder_config": obs_builder_config,
    }


if __name__ == "__main__":
    RANDOM_SEED = 23
    args = parse_args()
    if args.env == Env.FLATLAND:
        configs = prepare_flatland_configs(args.env_name)
    elif args.env == Env.STARCRAFT:
        configs = prepare_starcraft_configs(args.env_name)
    elif args.env == Env.SIMPLE_SPREAD:
        configs = prepare_simple_spread_configs(args.env_name)
    elif args.env == Env.VMAS_BALANCE:
        configs = prepare_vmas_balance_configs(args.env_name)
    elif args.env == Env.SAFETY_GYM:
        configs = prepare_safety_gym_configs(args.env_name)
    else:
        raise Exception("Unknown environment")
    configs["env_config"][0].ENV_TYPE = Env(args.env)
    configs["learner_config"].ENV_TYPE = Env(args.env)
    configs["controller_config"].ENV_TYPE = Env(args.env)

    exp = Experiment(
        steps=10**10,
        episodes=50000,
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
