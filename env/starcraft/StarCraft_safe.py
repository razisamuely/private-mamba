import random

import numpy as np
from smac.env import StarCraft2Env

from configs.Config import Config


class StarCraft(Config):
    """
    SafeRL wrapper for SMAC environments with tailored cost functions
    that don't naturally decrease as agents improve at the main task.
    """

    def __init__(self, env_name, cost_type="danger_zone", safe_distance=3.0, formation_threshold=5.0):
        self.env_name = env_name
        self.cost_type = cost_type
        self.safe_distance = safe_distance
        self.formation_threshold = formation_threshold

        self.env = StarCraft2Env(map_name=env_name, continuing_episode=True, difficulty="7")
        env_info = self.env.get_env_info()

        self.n_obs = env_info["obs_shape"]
        self.n_actions = env_info["n_actions"]
        self.n_agents = env_info["n_agents"]

        # Track statistics for cost computation
        self.prev_shots_fired = 0
        self.prev_hits_made = 0

    def to_dict(self, l):
        return {i: e for i, e in enumerate(l)}

    def step(self, action_dict, use_reward_shaping=False):
        reward, done, info = self.env.step(action_dict)
        cost = self.get_cost(info)
        info["cost"] = {i: cost for i in range(self.n_agents)}

        if cost > 0 and use_reward_shaping:
            reward
            info["reward_shaping"] = True
            reward = self.reward_shaping(reward, info, ratio=0.1)

        return (
            self.to_dict(self.env.get_obs()),
            {i: reward for i in range(self.n_agents)},
            {i: done for i in range(self.n_agents)},
            info,
        )

    def reset(self):
        self.env.reset()
        self.prev_shots_fired = 0
        self.prev_hits_made = 0
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
        return StarCraft(self.env_name, self.cost_type, self.safe_distance, self.formation_threshold)

    def get_random_action(self):
        actions = []
        for i in range(self.n_agents):
            available_actions = self.env.get_avail_agent_actions(i)
            # Get available action indices
            valid_actions = [j for j in range(self.n_actions) if available_actions[j] == 1]
            # Choose random valid action
            action = random.choice(valid_actions) if valid_actions else 0
            actions.append(action)
        return actions

    def get_health(self, agent_id):
        """Get health of specific agent"""
        unit = self.env.get_unit_by_id(agent_id)
        return unit.health if unit else 0

    def get_agent_position(self, agent_id):
        """Get position coordinates of agent"""
        unit = self.env.get_unit_by_id(agent_id)
        if unit:
            return (unit.pos.x, unit.pos.y)
        else:
            raise ValueError(f"Agent {agent_id} not found in the environment.")

    def get_enemy_distances(self, agent_id):
        """Calculate distances to all enemies for given agent"""
        agent_pos = self.get_agent_position(agent_id)

        distances = []
        enemies = self.env.enemies
        for enemy in enemies.values():
            if enemy.health > 0:  # Only alive enemies
                enemy_pos = (enemy.pos.x, enemy.pos.y)
                dist = np.sqrt((agent_pos[0] - enemy_pos[0]) ** 2 + (agent_pos[1] - enemy_pos[1]) ** 2)
                distances.append(dist)
        return distances

    def is_in_danger_zone(self, pos):
        """Check if position is in predefined danger zone"""
        if not pos:
            return False
        # Define danger zone as center area (customize based on map)
        center_x, center_y = 16, 16  # Adjust based on map size
        danger_radius = 8
        dist_to_center = np.sqrt((pos[0] - center_x) ** 2 + (pos[1] - center_y) ** 2)
        return dist_to_center < danger_radius

    def calculate_formation_spread(self, positions):
        """Calculate how spread out the formation is"""
        valid_positions = [pos for pos in positions if pos is not None]
        if len(valid_positions) < 2:
            return 0

        # Calculate average pairwise distance
        total_distance = 0
        pairs = 0
        for i in range(len(valid_positions)):
            for j in range(i + 1, len(valid_positions)):
                pos1, pos2 = valid_positions[i], valid_positions[j]
                dist = np.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)
                total_distance += dist
                pairs += 1

        return total_distance / pairs if pairs > 0 else 0

    # def get_cost_resource_waste(self, info):
    #     """Cost based on inefficient resource usage (wasted shots)"""
    #     # Get current battle statistics
    #     info.get("battle_won", False)
    #     current_shots = self.env.death_tracker_ally.get("shots_fired", 0)
    #     current_hits = self.env.death_tracker_ally.get("hits_made", 0)

    #     # Calculate shots fired this step
    #     shots_this_step = current_shots - self.prev_shots_fired
    #     hits_this_step = current_hits - self.prev_hits_made

    #     # Update tracking
    #     self.prev_shots_fired = current_shots
    #     self.prev_hits_made = current_hits

    #     # Cost = wasted shots (shots that didn't hit)
    #     wasted_shots = max(0, shots_this_step - hits_this_step)
    #     return wasted_shots

    def get_cost_resource_waste(self, info):

        # Get actual action indices from one-hot encoded actions
        if hasattr(self.env, "last_action") and self.env.last_action is not None:
            action_indices = [row.argmax() for row in self.env.last_action]
            # Count attack actions (actions >= n_actions_no_attack are attacks)
            attack_count = sum(1 for action in action_indices if action >= self.env.n_actions_no_attack)
        else:
            attack_count = 0

        # Track kills this step
        current_kills = info.get("dead_enemies", 0)
        kills_this_step = current_kills - getattr(self, "prev_kills", 0)
        self.prev_kills = current_kills

        # Cost = attacks that didn't result in kills (wasted shots)
        wasted_shots = max(0, attack_count - kills_this_step)
        return wasted_shots

    def reward_shaping(self, reward, info, ratio):
        """
        Apply reward shaping based on cost.
        The cost is subtracted from the reward to encourage efficiency.
        """
        cost = info.get("cost", {}).get(0, 0)
        if cost > 0:
            return reward - ratio * cost
        return reward

    def get_cost_aggressive_positioning(self, info):
        """Cost based on risky positioning (too close to enemies)"""
        total_risk = 0
        for agent_id in range(self.n_agents):
            if self.get_health(agent_id) > 0:  # Only alive agents
                enemy_distances = self.get_enemy_distances(agent_id)
                # Count how many enemies are within unsafe distance
                close_enemies = sum(1 for d in enemy_distances if d < self.safe_distance)
                total_risk += close_enemies
        return total_risk

    def get_cost_danger_zone_violation(self, info):
        """Cost based on entering dangerous areas"""
        violations = 0
        for agent_id in range(self.n_agents):
            if self.get_health(agent_id) > 0:  # Only alive agents
                pos = self.get_agent_position(agent_id)
                if self.is_in_danger_zone(pos):
                    violations += 1
        return violations

    def get_cost_formation_breaking(self, info):
        """Cost based on breaking formation (agents too spread out)"""
        positions = []
        for agent_id in range(self.n_agents):
            if self.get_health(agent_id) > 0:  # Only alive agents
                pos = self.get_agent_position(agent_id)
                if pos:
                    positions.append(pos)

        if len(positions) < 2:
            return 0

        formation_spread = self.calculate_formation_spread(positions)
        # Return cost if formation is too spread out
        return max(0, formation_spread - self.formation_threshold)

    def get_cost_combined(self, info):
        """Combined cost function using multiple factors"""
        resource_cost = self.get_cost_resource_waste(info) * 0.3
        position_cost = self.get_cost_aggressive_positioning(info) * 0.3
        danger_cost = self.get_cost_danger_zone_violation(info) * 0.2
        formation_cost = self.get_cost_formation_breaking(info) * 0.2

        return resource_cost + position_cost + danger_cost + formation_cost

    def get_cost(self, info):
        """Main cost function - selects based on cost_type"""
        if self.cost_type == "resource_waste":
            return self.get_cost_resource_waste(info)
        elif self.cost_type == "aggressive_positioning":
            return self.get_cost_aggressive_positioning(info)
        elif self.cost_type == "danger_zone":
            return self.get_cost_danger_zone_violation(info)
        elif self.cost_type == "formation_breaking":
            return self.get_cost_formation_breaking(info)
        elif self.cost_type == "combined":
            return self.get_cost_combined(info)
        elif self.cost_type == "dead_allies":
            # Original cost (for comparison)
            return info.get("dead_allies", 0)
        else:
            return 0


if __name__ == "__main__":
    # Test different cost functions
    cost_types = ["resource_waste", "aggressive_positioning", "danger_zone", "formation_breaking", "combined"]

    for cost_type in cost_types:
        print(f"\n=== Testing {cost_type} cost function ===")
        env = StarCraft("3m", cost_type=cost_type)
        obs = env.reset()

        print(f"Environment: {env.env_name}")
        print(f"Observations shape: {env.n_obs}")
        print(f"Actions: {env.n_actions}")
        print(f"Agents: {env.n_agents}")
        print(f"Cost type: {cost_type}")

        # Run a few steps to test cost calculation
        for step in range(3):
            actions = env.get_random_action()
            obs, reward, done, info = env.step(actions)
            cost = info.get("cost", {}).get(0, 0)
            print(f"Step {step}: Cost = {cost}")

        env.close()
