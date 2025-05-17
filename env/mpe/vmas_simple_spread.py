from vmas import make_env

from configs.Config import Config


class VmasSpread(Config):

    def __init__(self, env_name, device="cpu", seed=0, **kwargs):

        self.env_name = env_name
        self.device = device
        self.seed = seed
        self.kwargs = kwargs
        self.env = make_env(
            scenario=self.env_name,
            num_envs=1,
            device=device,
            continuous_actions=True,
            dict_spaces=False,
            seed=seed,
            terminated_truncated=True,
            **kwargs
        )
        self.n_obs = self.env.observation_space
        self.n_actions = self.env.action_space
        self.n_agents = self.env.n_agents

    def to_dict(self, l):
        # return {i: e for i, e in enumerate(l)}
        pass

    def step(self, action_dict):
        # reward, done, info = self.env.step(action_dict)
        # return (
        #     self.to_dict(self.env.get_obs()),
        #     {i: reward for i in range(self.n_agents)},
        #     {i: done for i in range(self.n_agents)},
        #     info,
        # )
        pass

    def reset(self):
        observations = self.env.reset()
        return {i: obs.cpu().numpy() for i, obs in enumerate(observations)}

    def render(self, mode="human"):
        # return self.env.render(mode=mode)
        pass

    def close(self):
        # no need to close the environment
        pass

    def get_avail_agent_actions(self, handle):
        # return self.env.get_avail_agent_actions(handle)
        pass

    def is_natural_termination(self, info, steps_done):
        # return "episode_limit" not in info
        pass

    def create_env(self):
        return VmasSpread(self.env_name, self.device, self.seed, **self.kwargs)


if __name__ == "__main__":
    env = VmasSpread("simple_spread")
    obs = env.reset()
    print("env.n_obs = ", obs)
    print("env.n_obs = ", env.n_obs)
    print("env.n_actions = ", env.n_actions)
    print("env.n_agents = ", env.n_agents)
    env.close()

    created_env = env.create_env()
    print("Created env.n_obs = ", created_env.n_obs)
    print("Created env.n_actions = ", created_env.n_actions)
    print("Created env.n_agents = ", created_env.n_agents)
    created_env.close()
