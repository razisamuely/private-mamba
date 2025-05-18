import os
import time

import imageio
import torch
from PIL import Image

from configs.dreamer.DreamerControllerConfig import DreamerControllerConfig
from env.mpe.vmas_simple_spread import VmasSpread
from environments import Env


def render_trained_policy(
    model_path=None, scenario_name="2s_vs_1sc", save_gif=True, gif_filename="starcraft_policy.gif", fps=10
):
    env_config = VmasSpread(scenario_name)
    controller_config = DreamerControllerConfig()
    controller_config.ENV_TYPE = Env.SIMPLE_SPREAD

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

    while not all(done.values()):
        print(f"Step: {frame_count}, Episode Reward: {episode_reward}")
        frame = env.render(mode="rgb_array")

        if save_gif:
            frames.append(frame)
            Image.fromarray(frame).save(f"{temp_dir}/frame_{frame_count:04d}.png")
            frame_count += 1

        observations = []
        avail_actions = []

        for handle in range(env.n_agents):
            avail_actions.append(torch.tensor(env.get_avail_agent_actions(handle)))

            if handle in state and not done[handle]:
                if len(state[handle].shape) == 1:
                    observations.append(state[handle].unsqueeze(0))
                else:
                    observations.append(state[handle])
            else:
                observations.append(torch.zeros(1, controller_config.IN_DIM))

        observations = torch.cat(observations).unsqueeze(0)
        av_action = torch.stack(avail_actions).unsqueeze(0)

        actions = controller.step(observations, av_action, None)
        action_list = [action.argmax().item() for action in actions]
        action_list_of_tensors = [torch.tensor([[action]]) for action in action_list]
        next_obs_dict, reward_dict, done_dict, info = env.step(action_list_of_tensors)

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

    # delet e temporary frames
    if save_gif:
        for frame in frames:
            os.remove(frame)
        os.rmdir(temp_dir)
        print(f"Temporary frames deleted from {temp_dir}")
    return episode_reward


if __name__ == "__main__":
    render_trained_policy(scenario_name="simple_spread")
