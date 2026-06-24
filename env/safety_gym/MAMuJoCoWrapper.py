import numpy as np

try:
    from safety_gymnasium.tasks.safe_multi_agent.safe_mujoco_multi import SafeMAEnv
except ImportError:
    try:
        from safety_gymnasium.tasks.safe_multi_agent.tasks.velocity.safe_mujoco_multi import (
            SafeMAEnv,
        )
    except ImportError:
        from safety_gymnasium.tasks.safe_multi_agent.tasks.safe_mujoco_multi import (
            SafeMAEnv,
        )

# Map env_name -> (scenario, agent_conf)
ENV_REGISTRY = {
    "Safety2x1SwimmerVelocity-v0": ("Swimmer", "2x1"),
    "Safety2x3HalfCheetahVelocity-v0": ("HalfCheetah", "2x3"),
    "Safety2x4AntVelocity-v0": ("Ant", "2x4"),
    "Safety4x2AntVelocity-v0": ("Ant", "4x2"),
}


class MAMuJoCoWrapper:
    """
    Wrapper for MAMuJoCo (Safety-Gymnasium) environments.
    Supports both discrete (legacy) and continuous action modes.
    """

    def __init__(self, env_name="Safety2x1SwimmerVelocity-v0", action_type="discrete"):
        self.env_name = env_name
        self.action_type = action_type
        self.env = None

        if env_name in ENV_REGISTRY:
            self.scenario, self.agent_conf = ENV_REGISTRY[env_name]
        else:
            self.scenario = "Swimmer"
            self.agent_conf = "2x1"

        self.n_agents = 2
        self.n_obs = 10
        self.agents = [i for i in range(self.n_agents)]
        self._obs_mean = None
        self._obs_var = None
        self._obs_count = 0

        # Discrete legacy mapping (only used when action_type="discrete")
        self.n_actions_discrete = 9
        self.n_actions = self.n_actions_discrete
        self.action_map = self._create_action_mapping()

    def _initialize_env(self):
        if self.env is None:
            self.env = SafeMAEnv(scenario=self.scenario, agent_conf=self.agent_conf)
            self.n_agents = len(self.env.possible_agents)
            self.agents = list(range(self.n_agents))
            _ = self.env.reset()
            state = self.env.state()
            self.n_obs = state.shape[0] + self.n_agents

            if self.action_type == "continuous":
                agent0 = self.env.possible_agents[0]
                self.n_actions = self.env.action_space(agent0).shape[0]

    def _create_action_mapping(self):
        """Map 9 discrete indices to 2D continuous control (-1.0 to 1.0)"""
        return {
            0: (0.0, 0.0),
            1: (1.0, 0.0),
            2: (-1.0, 0.0),
            3: (0.0, 1.0),
            4: (0.0, -1.0),
            5: (1.0, 1.0),
            6: (-1.0, -1.0),
            7: (0.5, 0.5),
            8: (-0.5, -0.5),
        }

    def _update_obs_stats(self, obs):
        """Welford's online algorithm for per-feature running mean/var."""
        if self._obs_mean is None:
            self._obs_mean = np.zeros_like(obs, dtype=np.float64)
            self._obs_var = np.ones_like(obs, dtype=np.float64)
            self._obs_count = 0
        self._obs_count += 1
        delta = obs - self._obs_mean
        self._obs_mean += delta / self._obs_count
        delta2 = obs - self._obs_mean
        self._obs_var += (delta * delta2 - self._obs_var) / self._obs_count

    def _normalize_obs(self, obs):
        if self._obs_count < 2:
            return obs
        std = np.sqrt(np.maximum(self._obs_var, 1e-6))
        return ((obs - self._obs_mean) / std).astype(np.float32)

    def _get_obs_dict(self):
        state = self.env.state()
        obs_dict = {}
        for a in range(self.n_agents):
            agent_id_feats = np.zeros(self.n_agents, dtype=np.float32)
            agent_id_feats[a] = 1.0
            obs_i = np.concatenate([state, agent_id_feats])
            self._update_obs_stats(obs_i)
            obs_dict[a] = self._normalize_obs(obs_i)
        return obs_dict

    def reset(self):
        self._initialize_env()
        self.env.reset()
        return self._get_obs_dict()

    def step(self, action_vector):
        agents = list(self.env.possible_agents)
        dict_actions = {}

        if self.action_type == "continuous":
            for i, agent in enumerate(agents):
                act = np.asarray(action_vector[i], dtype=np.float32).flatten()
                lo = np.asarray(self.env.action_space(agent).low, dtype=np.float32)
                hi = np.asarray(self.env.action_space(agent).high, dtype=np.float32)
                dict_actions[agent] = np.clip(act, lo, hi)
        else:
            joint_idx = int(action_vector[0]) % self.n_actions_discrete
            val = self.action_map.get(joint_idx, (0.0, 0.0))
            for i, agent in enumerate(agents):
                t = float(val[i]) if i < len(val) else 0.0
                lo = np.asarray(self.env.action_space(agent).low, dtype=np.float32)
                hi = np.asarray(self.env.action_space(agent).high, dtype=np.float32)
                dict_actions[agent] = np.clip(np.array([t], dtype=np.float32), lo, hi)

        _, rewards, costs, terminations, truncations, infos = self.env.step(dict_actions)

        obs_dict = self._get_obs_dict()
        reward_dict = {i: rewards[agent] for i, agent in enumerate(self.env.possible_agents)}
        done_dict = {i: terminations[agent] or truncations[agent] for i, agent in enumerate(self.env.possible_agents)}
        cost_dict = {i: costs[agent] for i, agent in enumerate(self.env.possible_agents)}
        infos["cost"] = cost_dict

        return obs_dict, reward_dict, done_dict, infos

    def get_avail_agent_actions(self, agent_id):
        if self.action_type == "continuous":
            return np.ones(self.n_actions)
        return np.ones(self.n_actions_discrete)

    def get_health(self, agent_id):
        return 1.0

    def is_natural_termination(self, info, steps_done):
        return True

    def close(self):
        if self.env:
            self.env.close()

    def create_env(self):
        return MAMuJoCoWrapper(self.env_name, action_type=self.action_type)
