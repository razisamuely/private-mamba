import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Normal, OneHotCategorical

from networks.dreamer.utils import build_model
from networks.transformer.layers import AttentionEncoder


def _sample_continuous(x):
    mean, log_std = x.chunk(2, dim=-1)
    # Replace any NaN with zero to prevent crash
    if torch.isnan(mean).any():
        mean = torch.nan_to_num(mean, nan=0.0)
    if torch.isnan(log_std).any():
        log_std = torch.nan_to_num(log_std, nan=0.0)
    log_std = torch.clamp(log_std, -5.0, 2.0)
    std = F.softplus(log_std) + 1e-5
    mean = torch.clamp(mean, -10.0, 10.0)
    dist = Normal(mean, std)
    raw = dist.rsample()
    action = torch.tanh(raw)
    return action, x, raw


def _sample_discrete(x):
    action_dist = OneHotCategorical(logits=x)
    action = action_dist.sample()
    return action, x


class Actor(nn.Module):
    def __init__(self, in_dim, out_dim, hidden_size, layers, activation=nn.ReLU, action_type="discrete"):
        super().__init__()
        self.action_type = action_type
        net_out_dim = out_dim * 2 if action_type == "continuous" else out_dim
        self.feedforward_model = build_model(in_dim, net_out_dim, layers, hidden_size, activation)

    def forward(self, state_features):
        x = self.feedforward_model(state_features)
        if self.action_type == "continuous":
            action, pi, raw = _sample_continuous(x)
            return action, pi, raw
        action, pi = _sample_discrete(x)
        return action, pi, None


class AttentionActor(nn.Module):
    def __init__(self, in_dim, out_dim, hidden_size, layers, activation=nn.ReLU, action_type="discrete"):
        super().__init__()
        self.action_type = action_type
        net_out_dim = out_dim * 2 if action_type == "continuous" else out_dim
        self.feedforward_model = build_model(hidden_size, net_out_dim, 1, hidden_size, activation)
        self._attention_stack = AttentionEncoder(1, hidden_size, hidden_size)
        self.embed = nn.Linear(in_dim, hidden_size)

    def forward(self, state_features):
        n_agents = state_features.shape[-2]
        batch_size = state_features.shape[:-2]
        embeds = F.relu(self.embed(state_features))
        embeds = embeds.view(-1, n_agents, embeds.shape[-1])
        attn_embeds = F.relu(self._attention_stack(embeds).view(*batch_size, n_agents, embeds.shape[-1]))
        x = self.feedforward_model(attn_embeds)
        if self.action_type == "continuous":
            action, pi, raw = _sample_continuous(x)
            return action, pi, raw
        action, pi = _sample_discrete(x)
        return action, pi, None
