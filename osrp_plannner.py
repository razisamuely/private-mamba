from collections import defaultdict


class OSRP_Planner:
    def __init__(self, config):
        self.config = config
        self.horizon = self.config.planner.horizon
        self.num_samples = self.config.planner.num_samples

    def plan(self, state, env, agent):
        action_cost = defaultdict(list)
        for _ in range(self.num_samples):
            cost = 0
            action = agent.get_action(state)
            initial_action = action

            for _ in range(self.horizon):
                next_state, _, done, info = env.step(action)
                cost += info.get("cost", 0)
                action = agent.get_action(next_state)

                if done:
                    break

            action_cost[initial_action].append(cost)

        best_action = min(action_cost, key=lambda a: sum(action_cost[a]) / len(action_cost[a]))
        return best_action, action_cost[best_action]
