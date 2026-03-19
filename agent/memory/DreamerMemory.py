import numpy as np
import torch


class DreamerMemory:
    def __init__(
        self, capacity, sequence_length, action_size, obs_size, n_agents, device, env_type, use_available_actions
    ):
        self.capacity = capacity
        self.sequence_length = sequence_length
        self.action_size = action_size
        self.obs_size = obs_size
        self.device = device
        self.env_type = env_type
        self.use_available_actions = use_available_actions
        self.init_buffer(n_agents, env_type)

    def init_buffer(self, n_agents, env_type):
        self.observations = np.empty((self.capacity, n_agents, self.obs_size), dtype=np.float32)
        self.actions = np.empty((self.capacity, n_agents, self.action_size), dtype=np.float32)
        self.av_actions = (
            np.empty((self.capacity, n_agents, self.action_size), dtype=np.float32)
            if self.use_available_actions
            else None
        )
        self.rewards = np.empty((self.capacity, n_agents, 1), dtype=np.float32)
        self.costs = np.empty((self.capacity, n_agents, 1), dtype=np.float32)
        self.dones = np.empty((self.capacity, n_agents, 1), dtype=np.float32)
        self.fake = np.empty((self.capacity, n_agents, 1), dtype=np.float32)
        self.last = np.empty((self.capacity, n_agents, 1), dtype=np.float32)
        self.next_idx = 0
        self.n_agents = n_agents
        self.full = False
        self.high_cost_indices = set()

    def append(self, obs, action, reward, cost, done, fake, last, av_action):
        if self.actions.shape[-2] != action.shape[-2]:
            self.init_buffer(action.shape[-2], self.env_type)
        for i in range(len(obs)):
            self.observations[self.next_idx] = obs[i]
            self.actions[self.next_idx] = action[i]
            if av_action is not None:
                self.av_actions[self.next_idx] = av_action[i]
            self.rewards[self.next_idx] = reward[i]
            self.costs[self.next_idx] = cost[i]
            if np.any(cost[i] > 0):
                self.high_cost_indices.add(self.next_idx)
            else:
                self.high_cost_indices.discard(self.next_idx)

            self.dones[self.next_idx] = done[i]
            self.fake[self.next_idx] = fake[i]
            self.last[self.next_idx] = last[i]
            self.next_idx = (self.next_idx + 1) % self.capacity
            self.full = self.full or self.next_idx == 0

    def tenzorify(self, nparray):
        return torch.from_numpy(nparray).float()

    def sample(self, batch_size, cost_priority_ratio=0.0):
        if cost_priority_ratio > 0 and len(self.high_cost_indices) > 0:
            return self.get_transitions(self.sample_positions_prioritized(batch_size, cost_priority_ratio))
        return self.get_transitions(self.sample_positions(batch_size))

    def process_batch(self, val, idxs, batch_size):
        return torch.as_tensor(val[idxs].reshape(self.sequence_length, batch_size, self.n_agents, -1)).to(self.device)

    def get_transitions(self, idxs):
        batch_size = len(idxs)
        vec_idxs = idxs.transpose().reshape(-1)
        observation = self.process_batch(self.observations, vec_idxs, batch_size)[1:]
        reward = self.process_batch(self.rewards, vec_idxs, batch_size)[:-1]
        cost = self.process_batch(self.costs, vec_idxs, batch_size)[:-1]
        action = self.process_batch(self.actions, vec_idxs, batch_size)[:-1]
        av_action = (
            self.process_batch(self.av_actions, vec_idxs, batch_size)[1:] if self.use_available_actions else None
        )
        done = self.process_batch(self.dones, vec_idxs, batch_size)[:-1]
        fake = self.process_batch(self.fake, vec_idxs, batch_size)[1:]
        last = self.process_batch(self.last, vec_idxs, batch_size)[1:]

        return {
            "observation": observation,
            "reward": reward,
            "cost": cost,
            "action": action,
            "done": done,
            "fake": fake,
            "last": last,
            "av_action": av_action,
        }

    def sample_position(self):
        valid_idx = False
        while not valid_idx:
            idx = np.random.randint(0, self.capacity if self.full else self.next_idx - self.sequence_length)
            idxs = np.arange(idx, idx + self.sequence_length) % self.capacity
            valid_idx = self.next_idx not in idxs[1:]  # Make sure data does not cross the memory index
        return idxs

    def sample_positions(self, batch_size):
        return np.asarray([self.sample_position() for _ in range(batch_size)])

    def sample_positions_prioritized(self, batch_size, ratio):
        n_high_cost = int(batch_size * ratio)
        n_regular = batch_size - n_high_cost

        positions = []
        # Sample regular ones
        for _ in range(n_regular):
            positions.append(self.sample_position())

        # Sample high-cost ones
        high_cost_list = list(self.high_cost_indices)
        for _ in range(n_high_cost):
            valid_idx = False
            while not valid_idx:
                # Pick a random costly timestep
                costly_idx = np.random.choice(high_cost_list)
                # Pick a random offset so the costly timestep is somewhere in the training slice ([:-1])
                offset = np.random.randint(0, self.sequence_length - 1)
                idx = (costly_idx - offset) % self.capacity

                idxs = np.arange(idx, idx + self.sequence_length) % self.capacity
                # Check validity: 1. Start index is within range. 2. Buffer wrap around.
                if self.full:
                    valid_idx = self.next_idx not in idxs[1:]
                else:
                    valid_idx = idx < self.next_idx - self.sequence_length and self.next_idx not in idxs[1:]
            positions.append(idxs)

        return np.asarray(positions)

    def __len__(self):
        return self.capacity if self.full else self.next_idx

    def clean(self):
        self.memory = list()
        self.position = 0
