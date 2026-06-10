import numpy as np
import torch
import torch.nn.functional as F

import wandb
from agent.optim.utils import (
    batch_multi_agent,
    calculate_ppo_loss,
    compute_return,
    info_loss,
    log_prob_loss,
    rec_loss,
    state_divergence_loss,
)
from agent.utils.params import FreezeParameters
from networks.dreamer.rnns import rollout_policy, rollout_representation


def model_loss(config, model, obs, action, av_action, reward, cost, done, fake, last):
    time_steps = obs.shape[0]
    batch_size = obs.shape[1]
    n_agents = obs.shape[2]

    embed = model.observation_encoder(obs.reshape(-1, n_agents, obs.shape[-1]))
    embed = embed.reshape(time_steps, batch_size, n_agents, -1)

    prev_state = model.representation.initial_state(batch_size, n_agents, device=obs.device)
    prior, post, deters = rollout_representation(model.representation, time_steps, embed, action, prev_state, last)
    feat = torch.cat([post.stoch, deters], -1)
    feat_dec = post.get_features()

    reconstruction_loss, i_feat = rec_loss(
        model.observation_decoder,
        feat_dec.reshape(-1, n_agents, feat_dec.shape[-1]),
        obs[:-1].reshape(-1, n_agents, obs.shape[-1]),
        1.0 - fake[:-1].reshape(-1, n_agents, 1),
    )
    model_reward = model.reward_model(feat)
    reward_loss = F.smooth_l1_loss(model_reward, reward[1:])
    if model.cost_model is not None:
        model_cost = model.cost_model(feat)
        cost_loss = F.smooth_l1_loss(
            model_cost, cost[1:]
        )  #  TODO (razisamuely): May use other loss function that fits to cost term, for example, F.binary_cross_entropy_with_logits
    else:
        cost_loss = 0.0  # TODO (razisamuely): Better no cost handling, but for now we just ignore it

    pcont_loss = log_prob_loss(model.pcont, feat, (1.0 - done[1:]))
    av_action_loss = log_prob_loss(model.av_action, feat_dec, av_action[:-1]) if av_action is not None else 0.0
    i_feat = i_feat.reshape(time_steps - 1, batch_size, n_agents, -1)

    dis_loss = info_loss(i_feat[1:], model, action[1:-1], 1.0 - fake[1:-1].reshape(-1))
    div = state_divergence_loss(prior, post, config)

    model_loss = div + reward_loss + dis_loss + reconstruction_loss + pcont_loss + av_action_loss + cost_loss
    if np.random.randint(20) == 4:
        wandb.log(
            {
                "Model/reward_loss": reward_loss,
                "Model/cost_loss": cost_loss,
                "Model/div": div,
                "Model/av_action_loss": av_action_loss,
                "Model/reconstruction_loss": reconstruction_loss,
                "Model/info_loss": dis_loss,
                "Model/pcont_loss": pcont_loss,
                "Model/Predicted_average_cost": model_cost.mean() if model.cost_model is not None else 0.0,
                "Model/Actual_average_cost": cost[1:].mean(),
                "Model/Predicted_average_reward": model_reward.mean(),
                "Model/Actual_average_reward": reward[1:].mean(),
            }
        )

    return model_loss


def actor_rollout(obs, action, last, model, actor, critic, config):
    n_agents = obs.shape[2]
    with FreezeParameters([model]):
        embed = model.observation_encoder(obs.reshape(-1, n_agents, obs.shape[-1]))
        embed = embed.reshape(obs.shape[0], obs.shape[1], n_agents, -1)
        prev_state = model.representation.initial_state(obs.shape[1], obs.shape[2], device=obs.device)
        prior, post, _ = rollout_representation(model.representation, obs.shape[0], embed, action, prev_state, last)
        post = post.map(lambda x: x.reshape((obs.shape[0] - 1) * obs.shape[1], n_agents, -1))
        items = rollout_policy(model.transition, model.av_action, config.HORIZON, actor, post)
    imag_feat = items["imag_states"].get_features()
    imag_rew_feat = torch.cat([items["imag_states"].stoch[:-1], items["imag_states"].deter[1:]], -1)
    returns, cost_returns = critic_rollout(
        model,
        critic,
        imag_feat,
        imag_rew_feat,
        items["actions"],
        items["imag_states"].map(lambda x: x.reshape(-1, n_agents, x.shape[-1])),
        config,
    )

    trajectory_costs = cost_returns.sum(dim=0)

    output = [
        items["actions"][:-1].detach(),
        items["av_actions"][:-1].detach() if items["av_actions"] is not None else None,
        items["old_policy"][:-1].detach(),
        imag_feat[:-1].detach(),
        returns.detach(),
        cost_returns.detach(),
        trajectory_costs.detach(),
    ]
    return [batch_multi_agent(v, n_agents) for v in output]


def critic_rollout(model, critic, states, rew_states, actions, raw_states, config):
    with FreezeParameters([model, critic]):
        imag_reward = calculate_next_reward(model, actions, raw_states)
        imag_reward = imag_reward.reshape(actions.shape[:-1]).unsqueeze(-1).mean(-2, keepdim=True)[:-1]

        image_cost = calculate_next_cost(model, actions, raw_states)
        image_cost = image_cost.reshape(actions.shape[:-1]).unsqueeze(-1).mean(-2, keepdim=True)[:-1]

        value_dict = critic(states)
        value = value_dict["value"]
        cost_value = value_dict["cost"]
        discount_arr = model.pcont(rew_states).mean
        wandb.log(
            {
                "Value/Max reward": imag_reward.max(),
                "Value/Min reward": imag_reward.min(),
                "Value/Reward": imag_reward.mean(),
                "Value/Discounted returns": (imag_reward - 0.1 * image_cost).mean(),
                "Value/Discount": discount_arr.mean(),
                "Value/Max cost": image_cost.max(),
                "Value/Min cost": image_cost.min(),
                "Value/Cost": image_cost.mean(),
                "Value/Max Value": value.max(),
                "Value/Value": value.mean(),
                "Value/CostValue": cost_value.mean(),
                "Value/Max CostValue": cost_value.max(),
            }
        )

    returns = compute_return(
        imag_reward, value[:-1], discount_arr, bootstrap=value[-1], lmbda=config.DISCOUNT_LAMBDA, gamma=config.GAMMA
    )
    cost_returns = compute_return(
        image_cost,
        cost_value[:-1],
        discount_arr,
        bootstrap=cost_value[-1],
        lmbda=config.DISCOUNT_LAMBDA,
        gamma=config.GAMMA,
    )
    return returns, cost_returns


def calculate_reward(model, states, mask=None):
    imag_reward = model.reward_model(states)
    if mask is not None:
        imag_reward *= mask
    return imag_reward


def calculate_cost(model, states, mask=None):
    imag_cost = model.cost_model(states)
    if mask is not None:
        imag_cost *= mask
    return imag_cost


def calculate_next_reward(model, actions, states):
    actions = actions.reshape(-1, actions.shape[-2], actions.shape[-1])
    next_state = model.transition(actions, states)
    imag_rew_feat = torch.cat([states.stoch, next_state.deter], -1)
    return calculate_reward(model, imag_rew_feat)


def calculate_next_cost(model, actions, states):
    actions = actions.reshape(-1, actions.shape[-2], actions.shape[-1])
    next_state = model.transition(actions, states)
    imag_cost_feat = torch.cat([states.stoch, next_state.deter], -1)
    return calculate_cost(model, imag_cost_feat)


def _continuous_actor_loss(imag_states, actions, old_policy, advantage, actor, ent_weight):
    """PPO loss for continuous (Gaussian) actions with tanh squash."""
    from torch.distributions import Normal

    _, new_pi = actor(imag_states)
    new_mean, new_log_std = new_pi.chunk(2, dim=-1)
    new_mean = torch.nan_to_num(new_mean, nan=0.0)
    new_log_std = torch.nan_to_num(new_log_std, nan=0.0)
    new_log_std = torch.clamp(new_log_std, -5.0, 2.0)
    new_mean = torch.clamp(new_mean, -10.0, 10.0)
    new_std = F.softplus(new_log_std) + 1e-5
    old_mean, old_log_std = old_policy.chunk(2, dim=-1)
    old_mean = torch.nan_to_num(old_mean, nan=0.0)
    old_log_std = torch.nan_to_num(old_log_std, nan=0.0)
    old_log_std = torch.clamp(old_log_std, -5.0, 2.0)
    old_mean = torch.clamp(old_mean, -10.0, 10.0)
    old_std = F.softplus(old_log_std) + 1e-5

    new_dist = Normal(new_mean, new_std)
    old_dist = Normal(old_mean, old_std)

    new_lp = new_dist.log_prob(actions).sum(-1, keepdim=True)
    old_lp = old_dist.log_prob(actions).sum(-1, keepdim=True)
    rho = (new_lp - old_lp).exp()

    from agent.optim.utils import ppo_loss

    polLoss = ppo_loss(advantage, rho)
    ent_loss = -new_dist.entropy().sum(-1)

    if np.random.randint(10) == 9:
        wandb.log(
            {
                "Policy/Entropy": ent_loss.mean(),
                "Policy/ppo_loss": polLoss.mean(),
                "Policy/Mean action": actions.float().mean(),
            }
        )

    return (polLoss + ent_loss.unsqueeze(-1) * ent_weight).mean()


def actor_loss(imag_states, actions, av_actions, old_policy, advantage, actor, ent_weight):
    if getattr(actor, "action_type", "discrete") == "continuous":
        return _continuous_actor_loss(imag_states, actions, old_policy, advantage, actor, ent_weight)

    _, new_policy = actor(imag_states)
    if av_actions is not None:
        new_policy[av_actions == 0] = -1e10
    actions = actions.argmax(-1, keepdim=True)
    rho = (
        F.log_softmax(new_policy, dim=-1).gather(2, actions) - F.log_softmax(old_policy, dim=-1).gather(2, actions)
    ).exp()
    ppo_loss, ent_loss = calculate_ppo_loss(new_policy, rho, advantage)

    if np.random.randint(10) == 9:
        wandb.log(
            {
                "Policy/Entropy": ent_loss.mean(),
                "Policy/ppo_loss": ppo_loss.mean(),
                "Policy/Entropy + PPO loss": (ppo_loss + ent_loss.unsqueeze(-1) * ent_weight).mean(),
                "Policy/Mean action": actions.float().mean(),
                # "Policy/Cost returns": cost_returns.mean(),
                "Policy/Entropy + PPO + 001 * Cost returns loss": (
                    ppo_loss + ent_loss.unsqueeze(-1) * ent_weight
                ).mean(),
            }
        )

    return (ppo_loss + ent_loss.unsqueeze(-1) * ent_weight).mean()


def value_loss(critic, imag_feat, reward_targets, cost_targets=None, lambda_cost=1.0):
    values = critic(imag_feat)
    value_pred = values["value"]
    value_loss = ((reward_targets - value_pred) ** 2) / 2.0

    if cost_targets is not None:
        cost_pred = values["cost"]
        cost_loss = ((cost_targets - cost_pred) ** 2) / 2.0

        if np.random.randint(20) == 9:
            wandb.log(
                {
                    "Agent/critic_reward_value_loss": value_loss.mean(),
                    "Agent/critic_cost_value_loss": cost_loss.mean(),
                }
            )

        return torch.mean(value_loss) + lambda_cost * torch.mean(cost_loss)

    return torch.mean(value_loss)
