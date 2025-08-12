from collections import defaultdict
from copy import deepcopy

import numpy as np
import torch
from torch.distributions import OneHotCategorical

from agent.models.DreamerModel import DreamerModel
from networks.dreamer.action import Actor


class DreamerController:

    def __init__(self, config):
        self.model = DreamerModel(config).eval()
        self.actor = Actor(config.FEAT, config.ACTION_SIZE, config.ACTION_HIDDEN, config.ACTION_LAYERS)
        self.expl_decay = config.EXPL_DECAY
        self.expl_noise = config.EXPL_NOISE
        self.expl_min = config.EXPL_MIN
        self.init_rnns()
        self.init_buffer()

    def receive_params(self, params):
        self.model.load_state_dict(params["model"])
        self.actor.load_state_dict(params["actor"])

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
    def step_roll_out_safedreamer_planning(
        self,
        observations,
        avail_actions,
        nn_mask,
        rollout_steps=15,
        num_trajectories=500,
        num_iterations=6,
        cost_threshold=2.0,
    ):
        """
        SafeDreamer OSRP (Online Safety-Reward Planning) implementation.
        Uses 500 trajectories, 15 steps depth, 6 iterations with safety constraints.
        """
        # Get initial state from real observations
        initial_state = self.model(observations, self.prev_actions, self.prev_rnn_state, nn_mask)
        batch_size, n_agents, action_size = observations.shape[0], observations.shape[1], self.config.ACTION_SIZE

        # Initialize action distribution parameters
        mu = torch.zeros(rollout_steps, n_agents, action_size, device=observations.device)
        sigma = torch.ones(rollout_steps, n_agents, action_size, device=observations.device)

        # CCEM iterations
        for iteration in range(num_iterations):
            trajectories = []
            trajectory_costs = []
            trajectory_rewards = []
            safe_trajectories = []  # Track safe trajectory indices

            # Sample trajectories
            for traj_idx in range(num_trajectories):
                # Generate action sequence for this trajectory
                action_sequence = []
                for step in range(rollout_steps):
                    if iteration == 0:
                        # First iteration: mix of actor policy and random sampling
                        if traj_idx < num_trajectories // 2:
                            # Use actor policy
                            feats = initial_state.get_features() if step == 0 else current_state.get_features()
                            _, pi = self.actor(feats)
                            if avail_actions is not None:
                                pi[avail_actions == 0] = -1e10
                            action_dist = OneHotCategorical(logits=pi)
                            action = action_dist.sample()
                        else:
                            # Random sampling
                            random_logits = torch.randn(n_agents, action_size, device=observations.device)
                            if avail_actions is not None:
                                random_logits[avail_actions == 0] = -1e10
                            action_dist = OneHotCategorical(logits=random_logits)
                            action = action_dist.sample()
                    else:
                        # Sample from updated distribution
                        action_logits = mu[step] + sigma[step] * torch.randn_like(mu[step])
                        if avail_actions is not None:
                            action_logits[avail_actions == 0] = -1e10
                        action_dist = OneHotCategorical(logits=action_logits)
                        action = action_dist.sample()

                    action_sequence.append(action)

                # Evaluate this action sequence
                current_state = initial_state
                trajectory_total_cost = 0.0
                trajectory_total_reward = 0.0

                for step, action in enumerate(action_sequence):
                    feats = current_state.get_features()

                    # Get predicted cost and reward
                    if hasattr(self.model, "cost_model") and self.model.cost_model is not None:
                        predicted_cost = self.model.cost_model(feats)
                        trajectory_total_cost += predicted_cost.mean().item()

                    if hasattr(self.model, "reward_model"):
                        predicted_reward = self.model.reward_model(feats)
                        trajectory_total_reward += predicted_reward.mean().item()

                    # Transition to next state
                    if step < rollout_steps - 1:
                        current_state = self.model.transition(action, current_state)

                trajectories.append(action_sequence)
                trajectory_costs.append(trajectory_total_cost)
                trajectory_rewards.append(trajectory_total_reward)

                # Check if trajectory satisfies safety constraint
                avg_cost_per_step = trajectory_total_cost / rollout_steps
                if avg_cost_per_step < cost_threshold:
                    safe_trajectories.append(traj_idx)

            # Select elite trajectories based on safety and performance
            elite_size = max(1, num_trajectories // 10)  # Top 10%

            if len(safe_trajectories) >= elite_size:
                # Enough safe trajectories: select highest reward among safe ones
                safe_rewards = [trajectory_rewards[i] for i in safe_trajectories]
                safe_reward_indices = torch.tensor(safe_rewards).argsort(descending=True)
                elite_indices = [safe_trajectories[i] for i in safe_reward_indices[:elite_size]]
            else:
                # Not enough safe trajectories: select lowest cost overall
                cost_indices = torch.tensor(trajectory_costs).argsort()
                elite_indices = cost_indices[:elite_size].tolist()

            # Update action distribution based on elite trajectories
            if iteration < num_iterations - 1:  # Don't update on last iteration
                for step in range(rollout_steps):
                    elite_actions = []
                    for idx in elite_indices:
                        elite_actions.append(trajectories[idx][step])

                    if elite_actions:
                        elite_actions_tensor = torch.stack(elite_actions)  # [elite_size, n_agents, action_size]

                        # Convert one-hot to logits and update distribution
                        elite_logits = torch.log(elite_actions_tensor + 1e-8)
                        mu[step] = elite_logits.mean(dim=0)
                        sigma[step] = torch.clamp(elite_logits.std(dim=0), min=0.1, max=2.0)

        # Select best trajectory for execution
        if safe_trajectories:
            # Choose safest trajectory with highest reward
            safe_rewards = [trajectory_rewards[i] for i in safe_trajectories]
            best_safe_idx = safe_trajectories[torch.tensor(safe_rewards).argmax().item()]
            best_trajectory = trajectories[best_safe_idx]
        else:
            # Choose trajectory with lowest cost
            best_idx = torch.tensor(trajectory_costs).argmin().item()
            best_trajectory = trajectories[best_idx]

        # Return first action from best trajectory
        first_action = best_trajectory[0]

        # Update controller state
        self.advance_rnns(initial_state)
        self.prev_actions = first_action.clone()

        return first_action.squeeze(0).clone()

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
