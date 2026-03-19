import unittest

import numpy as np

from agent.memory.DreamerMemory import DreamerMemory


class TestPrioritizedSampling(unittest.TestCase):
    def setUp(self):
        self.capacity = 100
        self.seq_len = 5
        self.n_agents = 2
        self.memory = DreamerMemory(
            capacity=self.capacity,
            sequence_length=self.seq_len,
            action_size=9,
            obs_size=30,
            n_agents=self.n_agents,
            device="cpu",
            env_type="starcraft",
            use_available_actions=False,
        )

    def test_high_cost_tracking(self):
        # Fill buffer with some normal and one high cost
        for i in range(10):
            obs = np.random.rand(1, self.n_agents, 30)
            action = np.random.rand(1, self.n_agents, 9)
            reward = np.zeros((1, self.n_agents, 1))
            cost = np.zeros((1, self.n_agents, 1))
            if i == 5:
                cost[0, 0, 0] = 1.0  # High cost at index 5
            self.memory.append(obs, action, reward, cost, [False], [False], [False], None)

        self.assertIn(5, self.memory.high_cost_indices)
        self.assertEqual(len(self.memory.high_cost_indices), 1)

    def test_prioritized_sampling_ratio(self):
        # Fill buffer until index 20
        # Put high cost only at index 15
        for i in range(20):
            cost = np.zeros((1, self.n_agents, 1))
            if i == 15:
                cost[0, 0, 0] = 10.0
            self.memory.append(
                np.zeros((1, self.n_agents, 30)),
                np.zeros((1, self.n_agents, 9)),
                np.zeros((1, self.n_agents, 1)),
                cost,
                [False],
                [False],
                [False],
                None,
            )

        # Sample with 100% priority to verify it always finds index 15
        batch_size = 10
        samples = self.memory.sample(batch_size, cost_priority_ratio=1.0)

        # Each sequence in the batch should contain the cost at index 15
        # The cost is at index 15. The sequence is length 5.
        # Sequence indices will be [j, j+1, j+2, j+3, j+4].
        # So 15 must be in that range.
        costs = samples["cost"].cpu().numpy()  # shape (seq_len-1, batch, agents, 1)
        # Wait, get_transitions returns [1:] for observations and [:-1] for costs.
        # sequence_length is 5, so cost has length 4.

        for b in range(batch_size):
            # Check if any agent at any step in the sequence has cost > 0
            found_cost = np.any(costs[:, b] > 0)
            self.assertTrue(found_cost, f"Batch {b} did not contain the high cost index")

    def test_empty_buffer_sampling_with_priority(self):
        # Sample with ratio 0.5 but no high costs present
        for i in range(10):
            self.memory.append(
                np.zeros((1, self.n_agents, 30)),
                np.zeros((1, self.n_agents, 9)),
                np.zeros((1, self.n_agents, 1)),
                np.zeros((1, self.n_agents, 1)),
                [False],
                [False],
                [True],
                None,
            )
        # Should fallback to regular sampling without error
        samples = self.memory.sample(4, cost_priority_ratio=0.5)
        self.assertEqual(samples["observation"].shape[1], 4)


if __name__ == "__main__":
    unittest.main()
