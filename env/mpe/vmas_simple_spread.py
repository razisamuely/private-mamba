from typing import Dict, List

import torch
from vmas import make_env

from configs.Config import Config


class VmasSpread(Config):

    def __init__(self, env_name, device="cpu", seed=None, max_steps=100, **kwargs):

        self.env_name = env_name
        self.device = device
        self.seed = seed
        self.kwargs = kwargs
        self.env = make_env(
            scenario=self.env_name,
            num_envs=1,
            device=device,
            continuous_actions=False,
            dict_spaces=False,
            seed=seed,
            terminated_truncated=True,
            max_steps=max_steps,
            **kwargs,
        )
        self.n_obs = self.env.observation_space[0].shape[0]
        self.n_actions = self.env.action_space[0].n
        self.n_agents = self.env.n_agents

    def to_dict(self, l):
        return {i: e[0] if e.dim() > 1 else e for i, e in enumerate(l)}

    def step(self, action: List[torch.Tensor]) -> Dict[str, List[torch.Tensor]]:
        action = self._ensure_correct_action_dimensions(action)
        obs, rewards, terminated, truncated, infos = self.env.step(action)
        dones = [terminated or truncated for i in range(self.env.n_agents)]
        return (
            self.to_dict(obs),
            self.to_dict(rewards),
            self.to_dict(dones),
            {"terminated": terminated, "truncated": truncated, "infos": infos},
        )

    def reset(self):
        observations = self.env.reset()
        return {i: obs.cpu().numpy()[0] for i, obs in enumerate(observations)}

    def render(self, mode="human"):
        if mode == "human":
            return self.env.render(mode=mode)
        elif mode == "rgb_array":
            return self.env.render(mode=mode)
        else:
            raise ValueError(f"Unknown render mode: {mode}")

    def close(self):
        # no need to close the environment
        pass

    def get_avail_agent_actions(self, handle):
        # all actions are available
        return [1] * self.n_actions

    def is_natural_termination(self, info, steps_done):
        return info["terminated"] or info["truncated"]

    def create_env(self):
        return VmasSpread(self.env_name, self.device, self.seed, **self.kwargs)

    def get_random_action(self):
        actions = []
        for i in range(self.env.n_agents):
            a = self.env.action_space[i].sample()
            a_tensor = torch.tensor([[a]], dtype=torch.float32, device=self.env.device)
            actions.append(a_tensor)

        return actions

    def _ensure_correct_action_dimensions(self, action: List[torch.Tensor]) -> List[torch.Tensor]:
        """Ensure all actions have the correct dimensions for the environment."""
        for i, a in enumerate(action):
            if not isinstance(a, torch.Tensor):
                raise ValueError(f"Action {i} is not a tensor")

            if a.dim() == 0:
                action[i] = self._add_batch_dimensions(a)

        return action

    def _add_batch_dimensions(self, tensor: torch.Tensor) -> torch.Tensor:
        """Add batch dimensions to a scalar tensor to match [batch_size, action_dim] format."""
        return tensor.unsqueeze(0).unsqueeze(0)


if __name__ == "__main__":
    env = VmasSpread("simple_spread")
    obs = env.reset()

    print("env.n_obs = ", obs)
    print("env.n_obs = ", env.n_obs)
    print("env.n_actions = ", env.n_actions)
    print("env.n_agents = ", env.n_agents)
    env.close()

    env2 = env.create_env()
    print("Created env.n_obs = ", env2.n_obs)
    print("Created env.n_actions = ", env2.n_actions)
    print("Created env.n_agents = ", env2.n_agents)
    env2.close()

    observations = env2.reset()
    for i in range(100):
        random_action = env2.get_random_action()
        observations, rewards, dones, info = env2.step(random_action)
        env2.render(mode="human")
        print("random_action:", random_action)
