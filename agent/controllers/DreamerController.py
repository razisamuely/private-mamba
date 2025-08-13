from collections import defaultdict
from copy import deepcopy

import numpy as np
import torch
from torch.distributions import OneHotCategorical

from agent.models.DreamerModel import DreamerModel
from networks.dreamer.action import Actor
from networks.dreamer.critic import AugmentedCritic


class DreamerController:

    def __init__(self, config):
        self.model = DreamerModel(config).eval()
        self.actor = Actor(config.FEAT, config.ACTION_SIZE, config.ACTION_HIDDEN, config.ACTION_LAYERS)
        self.critic = AugmentedCritic(config.FEAT, config.HIDDEN)
        self.expl_decay = config.EXPL_DECAY
        self.expl_noise = config.EXPL_NOISE
        self.expl_min = config.EXPL_MIN
        self.init_rnns()
        self.init_buffer()

    def receive_params(self, params):
        self.model.load_state_dict(params["model"])
        self.actor.load_state_dict(params["actor"])
        self.critic.load_state_dict(params["critic"])

    def init_buffer(self):
        self.buffer = defaultdict(list)

    def init_rnns(self):
        self.prev_rnn_state = None
        self.prev_actions = None

    def dispatch_buffer(self):
        total_buffer = {k: np.asarray(v, dtype=np.float32) for k, v in self.buffer.items()}
        last = np.zeros_like(total_buffer["done"])
        last[-1] = 1.0
        total_buffer["last"] = last
        self.init_rnns()
        self.init_buffer()
        return total_buffer

    def update_buffer(self, items):
        for k, v in items.items():
            if v is not None:
                self.buffer[k].append(v.squeeze(0).detach().clone().numpy())

    @torch.no_grad()
    def step(self, observations, avail_actions, nn_mask):
        """ "
        Compute policy's action distribution from inputs, and sample an
        action. Calls the model to produce mean, log_std, value estimate, and
        next recurrent state.  Moves inputs to device and returns outputs back
        to CPU, for the sampler.  Advances the recurrent state of the agent.
        (no grad)
        """
        state = self.model(observations, self.prev_actions, self.prev_rnn_state, nn_mask)
        feats = state.get_features()
        action, pi = self.actor(feats)
        if avail_actions is not None:
            pi[avail_actions == 0] = -1e10
            action_dist = OneHotCategorical(logits=pi)
            action = action_dist.sample()

        self.advance_rnns(state)
        self.prev_actions = action.clone()
        return action.squeeze(0).clone()

    def advance_rnns(self, state):
        self.prev_rnn_state = deepcopy(state)

    def exploration(self, action):
        """
        :param action: action to take, shape (1,)
        :return: action of the same shape passed in, augmented with some noise
        """
        for i in range(action.shape[0]):
            if np.random.uniform(0, 1) < self.expl_noise:
                index = torch.randint(0, action.shape[-1], (1,), device=action.device)
                transformed = torch.zeros(action.shape[-1])
                transformed[index] = 1.0
                action[i] = transformed
        self.expl_noise *= self.expl_decay
        self.expl_noise = max(self.expl_noise, self.expl_min)
        return action

    @torch.no_grad()
    def step_roll_out_simple_safedreamer(
        self,
        observations,
        avail_actions,
        nn_mask,
        rollout_steps=1,
        num_trajectories=50,
        num_iterations=3,
        cost_threshold=0.05,
        min_safe_trajectories=5,
    ):
        """
        SafeDreamer-style planning with safe trajectory filtering
        """
        best_action = None
        best_score = float("-inf")  # Changed from best_cost
        trajectories = []
        for iteration in range(num_iterations):

            # Store trajectory info

            for traj_idx in range(num_trajectories):
                initial_state = self.model(observations, self.prev_actions, self.prev_rnn_state, nn_mask)

                current_state = initial_state
                total_cost = 0.0
                total_reward = 0.0  # ADD: Track reward too

                for step in range(rollout_steps):
                    feats = current_state.get_features()

                    action, pi = self.actor(feats)

                    if avail_actions is not None:
                        pi[avail_actions == 0] = -1e10
                        action_dist = OneHotCategorical(logits=pi)
                        action = action_dist.sample()

                    if step == 0:
                        first_action = action.clone()

                    # # get cost with world model
                    # if hasattr(self.model, "cost_model") and self.model.cost_model is not None:
                    #     predicted_cost = self.model.cost_model(feats)
                    #     total_cost += predicted_cost.mean().item()
                    # else:
                    #     raise NotImplementedError("Cost model not implemented")

                    # cost using critic

                    critic_output = self.critic(feats)
                    predicted_cost = critic_output["cost"]
                    total_cost += predicted_cost.mean().item()

                    if hasattr(self.model, "reward_model") and self.model.reward_model is not None:
                        predicted_reward = self.model.reward_model(feats)
                        total_reward += predicted_reward.mean().item()

                    if step < rollout_steps - 1:
                        current_state = self.model.transition(action, current_state)

                trajectories.append({"action": first_action, "cost": total_cost, "reward": total_reward})

            # safe_trajectories = [t for t in trajectories if t["cost"] < cost_threshold]
            # get trajectory with minimal cost
        best_traj = min(trajectories, key=lambda t: t["cost"])
        worst_traj = max(trajectories, key=lambda t: t["cost"])

        # if len(safe_trajectories) >= min_safe_trajectories:
        #     best_traj = max(safe_trajectories, key=lambda t: t["reward"])
        #     current_score = best_traj["reward"]

        # else:
        #     best_traj = min(trajectories, key=lambda t: t["cost"])
        #     current_score = -best_traj["cost"]  # Negative cost as score (higher is better)

        # if current_score > best_score:
        #     best_score = current_score
        best_action = best_traj["action"]

        if best_action is None:
            initial_state = self.model(observations, self.prev_actions, self.prev_rnn_state, nn_mask)
            feats = initial_state.get_features()
            best_action, _ = self.actor(feats)

        initial_state = self.model(observations, self.prev_actions, self.prev_rnn_state, nn_mask)
        self.advance_rnns(initial_state)
        self.prev_actions = best_action.clone()

        return best_action.squeeze(0).clone()

    @torch.no_grad()
    def step_roll_out(self, observations, avail_actions, nn_mask, rollout_steps=15):
        """
        Perform a multi-step rollout starting from current observations.
        Returns the action for the first step, but internally simulates 'rollout_steps' steps.
        """
        # Get initial state from real observations
        initial_state = self.model(observations, self.prev_actions, self.prev_rnn_state, nn_mask)

        # Current state for rollout
        current_state = initial_state

        # Perform rollout for specified number of steps
        for step in range(rollout_steps):
            # Get features from current state
            feats = current_state.get_features()

            # Actor chooses action based on current state
            action, pi = self.actor(feats)

            # Apply available actions mask if provided
            if avail_actions is not None:
                pi[avail_actions == 0] = -1e10
                action_dist = OneHotCategorical(logits=pi)
                action = action_dist.sample()

            # Store the first action (the one we'll actually execute)
            if step == 0:
                first_action = action.clone()

            # Transition to next state (except on last step)
            if step < rollout_steps - 1:
                current_state = self.model.transition(action, current_state)

        # Update controller state
        self.advance_rnns(initial_state)
        self.prev_actions = first_action.clone()

        return first_action.squeeze(0).clone()
