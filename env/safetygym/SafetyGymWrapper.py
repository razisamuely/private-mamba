import numpy as np
import safety_gymnasium
import torch


class SafetyGymWrapper:
    def __init__(self, env_name="SafetyPointMultiGoal1-v0"):
        self.env_name = env_name
        self.env = safety_gymnasium.make(
            env_name,
            render_mode="rgb_array",
            camera_name="topdown",
        )
        self.agents = self.env.agents
        self.n_agents = len(self.agents)
        self.agents_obs = {agent: self.env.observation_space(agent).shape[0] for agent in self.agents}
        self.n_obs = self.agents_obs["agent_0"]  # Assuming all agents have the same observation space
        self.agents_actions = {agent: self.env.action_space(agent).shape[0] for agent in self.agents}
        self.action_map = self.create_action_mapping()
        self.n_actions = len(self.action_map)
        self.agent_actions_discrete = {agent: self.n_actions for agent in self.agents}

    def get_avail_agent_actions(self, agent_id):
        """
        Continuous actions: always “available.”
        We return a vector of 1s with the same size as the action dim.
        """
        agent_name = self.agents[agent_id]
        return np.ones(self.agent_actions_discrete[agent_name], dtype=np.float32)

    def get_health(self, agent_id):
        """
        Safety-Gym doesn’t have HP, so we return a constant.
        This prevents the rendering loop from thinking someone "died."
        """
        return 1.0

    def obs_name_convertor(self, obs):
        """
        agent_0 to 0 agent_1 to 1, etc.
        """
        return {int(agent.split("_")[1]): obs[agent] for agent in obs}

    def to_dict(self, l):
        return {agent: l[i] for i, agent in enumerate(self.agents)}

    def reset(self):
        obs, _ = self.env.reset()
        obs = self.obs_name_convertor(obs)
        return obs

    def step(self, action_dict):
        action_dict = self.action_vector_to_maped_dict(action_dict)
        obs, reward, cost, terminated, truncated, info = self.env.step(action_dict)
        done = {agent: terminated[agent] or truncated[agent] for agent in self.agents}
        info["cost"] = cost
        # print("action_dict:", action_dict,
        #       "obs:", obs,
        #       "reward:", reward,
        #       "cost:", cost,
        #       "terminated:", terminated,
        #       "truncated:", truncated,
        #       "done:", done,
        #       "info:", info)
        obs = self.obs_name_convertor(obs)
        done = self.obs_name_convertor(done)
        return obs, reward, done, info

    def render(self, mode="human"):
        return self.env.render()

    def close(self):
        self.env.close()

    def create_env(self):
        return SafetyGymWrapper(self.env_name)

    def get_random_action(self):
        return {agent: self.env.action_space(agent).sample() for agent in self.agents}

    def get_random_action_discrete(self):
        """
        Get a random action for each agent in the discrete action space.
        """
        return [np.random.randint(0, self.n_actions) for _ in range(self.n_agents)]

    def create_action_mapping(self):
        return {
            0: (0.0, 0.0),  # Stop
            1: (0.8, 0.0),  # Forward
            2: (-0.8, 0.0),  # Backward
            3: (0.0, 0.8),  # Turn right
            4: (0.0, -0.8),  # Turn left
            5: (0.6, 0.6),  # Forward + turn right
            6: (0.6, -0.6),  # Forward + turn left
            7: (-0.6, 0.6),  # Backward + turn right
            8: (-0.6, -0.6),  # Backward + turn left
        }

    def action_vector_to_maped_dict(self, action_vector):
        """
        Convert a vector of actions to a dictionary mapping agent IDs to actions.
        """
        # if list of tensors, convert to numpy array
        if isinstance(action_vector, list) and isinstance(action_vector[0], torch.Tensor):
            action_vector = [action.item() for action in action_vector]
        return {agent: self.action_map[action] for agent, action in zip(self.agents, action_vector)}

    def get_random_action(self):
        return [np.random.randint(0, self.n_actions_discrete) for _ in range(self.n_agents)]


if __name__ == "__main__":
    env = SafetyGymWrapper()
    obs = env.reset()
    print("obs:", obs)
    print("env.n_obs:", env.n_obs)
    print("env.n_actions:", env.n_actions)
    print("env.n_agents:", env.n_agents)
    actions = env.get_random_action()
    print("random actions:", actions)
    print("obs keys:", obs.keys())
    for agent_id, agent_obs in obs.items():
        print(f"{agent_id} observation shape:", agent_obs.shape)
        print(f"{agent_id} partial observation:", agent_obs[:10])  # show just first few values

    print("agent_0 == agent_1 obs:", np.allclose(obs["agent_0"], obs["agent_1"]))
