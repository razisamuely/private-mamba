import numpy as np
from env.starcraft.StarCraft import StarCraft

def main():
    # Create the environment
    env = StarCraft(env_name="8m")
    
    n_episodes = 10
    
    for e in range(n_episodes):
        # Reset environment
        obs_dict = env.reset()
        episode_reward = 0
        terminated = False
        
        # Track if episode is done
        episode_terminated = False
        
        while not episode_terminated:
            # Enable rendering
            env.render()
            
            # For each agent, select a random available action
            actions = []
            for agent_id in range(env.n_agents):
                avail_actions = env.get_avail_agent_actions(agent_id)
                avail_actions_ind = np.nonzero(avail_actions)[0]
                if len(avail_actions_ind) > 0:
                    action = np.random.choice(avail_actions_ind)
                    actions.append(action)
                else:
                    # No available actions - this shouldn't happen in SMAC
                    actions.append(0)
            
            # Convert to the format expected by your wrapper (a list, not a dict)
            next_obs_dict, reward_dict, done_dict, info = env.step(actions)
            
            # Update observations
            obs_dict = next_obs_dict
            
            # Track episode reward
            episode_reward += sum(reward_dict.values())
            
            # Check if episode is done
            episode_terminated = all(done_dict.values())
        
        print(f"Total reward in episode {e} = {episode_reward}")
    
    env.close()

if __name__ == "__main__":
    main()