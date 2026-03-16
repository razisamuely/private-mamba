import unittest

import numpy as np


# instead of importing the whole class, we test the logic directly
def get_cost_collision_logic(n_agents, unit_positions, last_actions, healths, threshold=1.0):
    """Extracted logic from StarCraft_safe.py"""
    moving_agents = []

    # action indices check (2-5 are move commands in SMAC)
    action_indices = last_actions

    for i in range(n_agents):
        health = healths[i]
        pos = unit_positions[i]
        if health > 0:
            # Exclude stationary: check if action is a move command (indices 2-5)
            action = action_indices[i] if i < len(action_indices) else 0
            if 2 <= action <= 5:
                moving_agents.append(pos)

    cost = 0
    n = len(moving_agents)
    for i in range(n):
        for j in range(i + 1, n):
            x1, y1 = moving_agents[i]
            x2, y2 = moving_agents[j]
            dist = np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
            if dist < threshold:
                cost += 1
    return cost


class TestCollisionLogic(unittest.TestCase):
    def test_collision_moving_agents(self):
        # 0=noop, 1=stop, 2=north (move), 3=south (move)
        n_agents = 3
        unit_positions = {0: (0, 0), 1: (0, 0.5), 2: (0, 0.2)}
        last_actions = [2, 3, 1]  # Agent 0 moves, Agent 1 moves, Agent 2 stops
        healths = [10, 10, 10]

        cost = get_cost_collision_logic(n_agents, unit_positions, last_actions, healths)

        # Expectation: Only Agent 0 and 1 are moving.
        # Pair (0,1) distance is 0.5. Threshold is 1.0.
        # Cost should be 1.
        self.assertEqual(cost, 1)

    def test_clump_three_agents(self):
        # All three moving and clumped
        n_agents = 3
        unit_positions = {0: (0, 0), 1: (0.5, 0), 2: (0, 0.5)}
        last_actions = [2, 2, 2]
        healths = [10, 10, 10]

        cost = get_cost_collision_logic(n_agents, unit_positions, last_actions, healths)

        # Pair (0,1): dist 0.5 -> Cost 1
        # Pair (0,2): dist 0.5 -> Cost 1
        # Pair (1,2): dist ~0.707 -> Cost 1
        # Total = 3
        self.assertEqual(cost, 3)

    def test_dead_agent_exclusion(self):
        # All moving, but Agent 1 is dead
        n_agents = 3
        unit_positions = {0: (0, 0), 1: (0.2, 0), 2: (0.4, 0)}
        last_actions = [2, 2, 2]
        healths = [10, 0, 10]

        cost = get_cost_collision_logic(n_agents, unit_positions, last_actions, healths)

        # Only Pair (0,2) distance 0.4 should be counted.
        self.assertEqual(cost, 1)


if __name__ == "__main__":
    unittest.main()
