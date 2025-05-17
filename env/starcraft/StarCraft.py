from smac.env import StarCraft2Env

from configs.Config import Config


class StarCraft(Config):

    def __init__(self, env_name):
        self.env_name = env_name
        self.env = StarCraft2Env(map_name=env_name, continuing_episode=True, difficulty="7")
        env_info = self.env.get_env_info()

        self.n_obs = env_info["obs_shape"]
        self.n_actions = env_info["n_actions"]
        self.n_agents = env_info["n_agents"]

    def to_dict(self, l):
        return {i: e for i, e in enumerate(l)}

    def step(self, action_dict):
        reward, done, info = self.env.step(action_dict)
        return (
            self.to_dict(self.env.get_obs()),
            {i: reward for i in range(self.n_agents)},
            {i: done for i in range(self.n_agents)},
            info,
        )

    def reset(self):
        self.env.reset()
        return {i: obs for i, obs in enumerate(self.env.get_obs())}

    def render(self, mode="human"):
        return self.env.render(mode=mode)

    def close(self):
        self.env.close()

    def get_avail_agent_actions(self, handle):
        return self.env.get_avail_agent_actions(handle)

    def is_natural_termination(self, info, steps_done):
        return "episode_limit" not in info

    def create_env(self):
        return StarCraft(self.env_name)


# # MPE wrapper implementation
# def is_natural_termination(self, info, steps_done):
#     return not info.get("truncated", False)

if __name__ == "__main__":
    env = StarCraft("3m")
    obs = env.reset()
    print("obs", obs)
    print("env.n_obs = ", env.n_obs)
    print("env.n_actions = ", env.n_actions)
    print("env.n_agents = ", env.n_agents)
