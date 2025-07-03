from env.safetygym.SafetyGymWrapper import SafetyGymWrapper


def main():
    # Create the environment
    env = SafetyGymWrapper()

    n_episodes = 10

    for e in range(n_episodes):
        # Reset environment
        env.reset()
        episode_reward = 0

        # Track if episode is done
        episode_terminated = False

        while not episode_terminated:
            # Enable rendering
            env.render()

            # For each agent, select a random available action
            actions = []
            for agent_id in range(env.n_agents):
                # avail_actions = env.get_avail_agent_actions(agent_id)
                # avail_actions_ind = np.nonzero(avail_actions)[0]
                # action = np.random.choice(avail_actions_ind)
                action = env.get_random_action_discrete()[agent_id]  # Use discrete action
                actions.append(action)

            # Convert to the format expected by your wrapper (a list, not a dict)
            next_obs_dict, reward_dict, done_dict, info = env.step(actions)

            # Update observations

            # Track episode reward
            episode_reward += sum(reward_dict.values())

            # Check if episode is done
            episode_terminated = all(done_dict.values())

        print(f"Total reward in episode {e} = {episode_reward}")

    env.close()


if __name__ == "__main__":
    main()
