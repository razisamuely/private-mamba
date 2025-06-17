import os
import time

import imageio
import torch
from PIL import Image

from configs.dreamer.DreamerControllerConfig import DreamerControllerConfig
from env.starcraft.StarCraft import StarCraft
from environments import Env


def render_trained_policy(
    model_path=None, map_name="2s_vs_1sc", save_gif=True, gif_filename="starcraft_policy.gif", fps=10
):
    env_config = StarCraft(map_name)
    controller_config = DreamerControllerConfig()
    controller_config.ENV_TYPE = Env.STARCRAFT

    env = env_config.create_env()
    controller_config.IN_DIM = env.n_obs
    controller_config.ACTION_SIZE = env.n_actions

    controller = controller_config.create_controller()
    if model_path is not None:
        params = torch.load(model_path)
        controller.receive_params(params)

    controller.model.eval()
    controller.actor.eval()

    obs_dict = env.reset()
    state = {i: torch.tensor(obs).float() for i, obs in obs_dict.items()}
    done = {i: 0 for i in range(env.n_agents)}
    episode_reward = 0

    temp_dir = "temp_frames"
    if save_gif and not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    frames = []
    frame_count = 0
    agent_health = {i: env.get_health(i) for i in range(env.n_agents)}
    while not all(done.values()):
        frame = env.render(mode="rgb_array")

        if save_gif:
            frames.append(frame)
            Image.fromarray(frame).save(f"{temp_dir}/frame_{frame_count:04d}.png")
            frame_count += 1

        observations = []
        avail_actions = []

        for handle in range(env.n_agents):
            if env.get_health(handle) < agent_health[handle]:
                agent_health[handle] = env.get_health(handle)
                print(f"Agent {handle} health changed to {agent_health[handle]}")

            avail_actions.append(torch.tensor(env.get_avail_agent_actions(handle)))

            if handle in state and not done[handle]:
                observations.append(state[handle].unsqueeze(0))
            else:
                observations.append(torch.zeros(1, controller_config.IN_DIM))

        observations = torch.cat(observations).unsqueeze(0)
        av_action = torch.stack(avail_actions).unsqueeze(0)

        actions = controller.step(observations, av_action, None)
        action_list = [action.argmax().item() for action in actions]

        next_obs_dict, reward_dict, done_dict, info = env.step(action_list)
        print(f"Cost : {info['cost']}")

        state = {i: torch.tensor(obs).float() for i, obs in next_obs_dict.items()}
        done = done_dict
        episode_reward += sum(reward_dict.values())

        if not save_gif:
            time.sleep(0.1)

    print(f"Episode finished with reward: {episode_reward}")
    env.close()

    if save_gif and frames:
        gif_path = os.path.join("artifacts", gif_filename)
        if not os.path.exists("artifacts"):
            os.makedirs("artifacts")
        imageio.mimsave(gif_path, frames, fps=fps)
        print(f"GIF saved as {gif_path}")

    return episode_reward


if __name__ == "__main__":
    model_path = "wandb/wandb/run-20250516_144200-eltq1qts/files/model_episod_85.pt"
    model_path = None
    render_trained_policy(model_path=model_path, map_name="2s_vs_1sc")
