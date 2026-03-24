import numpy as np

try:
    from safety_gymnasium.tasks.safe_multi_agent.safe_mujoco_multi import SafeMAEnv
except ImportError:
    try:
        from safety_gymnasium.tasks.safe_multi_agent.tasks.velocity.safe_mujoco_multi import (
            SafeMAEnv,
        )
    except ImportError:
        # Some versions use a different structure
        from safety_gymnasium.tasks.safe_multi_agent.tasks.safe_mujoco_multi import (
            SafeMAEnv,
        )


class SwimmerWrapper:
    """
    Architecture Generalized Wrapper for MACE (Safety-Gymnasium)
    Specifically for Safety2x1SwimmerVelocity-v0.
    """

    def __init__(self, env_name="Safety2x1SwimmerVelocity-v0"):
        self.env_name = env_name
        self.env = None

        # Scenario details (Matching SafePO)
        self.scenario = "Swimmer"
        self.agent_conf = "2x1"

        # Initial dummy values, will be updated in _initialize_env
        self.n_agents = 2
        self.n_obs = 10
        self.n_actions = 9  # Matching discrete mapping
        self.agents = [i for i in range(self.n_agents)]

        # For Safe Dreamer compatibility, we must map Discrete actions to Continuous
        self.n_actions_discrete = 9
        self.action_map = self._create_action_mapping()

    def _initialize_env(self):
        if self.env is None:
            # Using the same underlying engine as SafePO
            self.env = SafeMAEnv(scenario=self.scenario, agent_conf=self.agent_conf)
            self.n_agents = len(self.env.possible_agents)
            self.agents = list(range(self.n_agents))

            # Update observation size from real state
            _ = self.env.reset()
            state = self.env.state()
            self.n_obs = state.shape[0] + self.n_agents  # Matching ShareEnv.py from SafePO

    def _create_action_mapping(self):
        """Map 9 discrete indices to 2D continuous control (-1.0 to 1.0)"""
        return {
            0: (0.0, 0.0),  # Stop
            1: (1.0, 0.0),  # Agent-1 forward
            2: (-1.0, 0.0),  # Agent-1 backward
            3: (0.0, 1.0),  # Agent-2 forward
            4: (0.0, -1.0),  # Agent-2 backward
            5: (1.0, 1.0),  # Both forward
            6: (-1.0, -1.0),  # Both backward
            7: (0.5, 0.5),  # Slow forward
            8: (-0.5, -0.5),  # Slow backward
        }

    def _get_obs_dict(self):
        """Prepare observations for each agent (Match SafePO ShareEnv style)"""
        state = self.env.state()
        obs_dict = {}
        for a in range(self.n_agents):
            agent_id_feats = np.zeros(self.n_agents, dtype=np.float32)
            agent_id_feats[a] = 1.0
            obs_i = np.concatenate([state, agent_id_feats])
            # Simple normalization matching SafePO
            obs_i = (obs_i - np.mean(obs_i)) / (np.std(obs_i) + 1e-8)
            obs_dict[a] = obs_i
        return obs_dict

    def reset(self):
        self._initialize_env()
        self.env.reset()
        return self._get_obs_dict()

    def step(self, action_vector):
        """
        Input: list/array of discrete action indices per agent.
        """
        # Convert discrete indices to continuous dict for SafeMAEnv
        # Swimmer 2x1 is a peculiar case: SafeMAEnv might expect actions partitioned.
        # However, for the MAMBA agent, we assume it's like SMAC.

        # We'll map the FIRST action index to BOTH agents for simplicity in Phase 2
        # Or better: treat them independently if we have multiple actions.

        # For simplicity, we assume action_vector is [idx_agent0, idx_agent1]
        dict_actions = {}
        for i, agent in enumerate(self.env.possible_agents):
            discrete_idx = int(action_vector[i])
            # The continuous action space for Swimmer is 2 per agent?
            # We'll map to the space expected by the underlying task.
            dict_actions[agent] = np.zeros(self.env.action_space(agent).shape)
            # Map discrete idx to part of the continuous space
            # (In MuJoCo, usually first 2 joint velocities etc.)
            val = self.action_map.get(discrete_idx, (0.0, 0.0))
            dict_actions[agent][:] = val[0]  # Very simple mapping for now

        _, rewards, costs, terminations, truncations, infos = self.env.step(dict_actions)

        obs_dict = self._get_obs_dict()
        reward_dict = {i: rewards[agent] for i, agent in enumerate(self.env.possible_agents)}
        done_dict = {i: terminations[agent] or truncations[agent] for i, agent in enumerate(self.env.possible_agents)}

        # Prepare cost/info for DreamerWorker
        cost_dict = {i: costs[agent] for i, agent in enumerate(self.env.possible_agents)}
        infos["cost"] = cost_dict

        return obs_dict, reward_dict, done_dict, infos

    def get_avail_agent_actions(self, agent_id):
        return np.ones(self.n_actions_discrete)

    def get_health(self, agent_id):
        return 1.0

    def is_natural_termination(self, info, steps_done):
        return True  # Swimmer doesn't have an episode limit in info usually

    def close(self):
        if self.env:
            self.env.close()

    def create_env(self):
        return SwimmerWrapper(self.env_name)
