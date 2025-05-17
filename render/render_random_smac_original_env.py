import time

import numpy as np
from smac.env import StarCraft2Env


def main():
    # env = StarCraft2Env(map_name="8m")
    env = StarCraft2Env(map_name="2s_vs_1sc")
    env_info = env.get_env_info()

    env_info["n_actions"]
    n_agents = env_info["n_agents"]

    n_episodes = 10

    for e in range(n_episodes):
        env.reset()
        terminated = False
        episode_reward = 0

        while not terminated:
            env.get_obs()
            env.get_state()
            env.render(mode="human")  # Uncomment for rendering

            actions = []
            for agent_id in range(n_agents):
                avail_actions = env.get_avail_agent_actions(agent_id)
                avail_actions_ind = np.nonzero(avail_actions)[0]
                action = np.random.choice(avail_actions_ind)
                actions.append(action)

            reward, terminated, _ = env.step(actions)
            episode_reward += reward
            time.sleep(0.3)

        print(f"Total reward in episode {e} = {episode_reward}")

    env.close()


if __name__ == "__main__":
    main()
