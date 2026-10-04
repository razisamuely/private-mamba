r"""Transition-error diagnostics for the paper's Theorem 1, Corollary 1, Proposition 1.

At replay step :math:`t`, agent :math:`i`'s world model predicts its stochastic state
with the prior :math:`p_i=p_\theta(z_t^i\mid h_t^i)`; the posterior
:math:`q_i=q_\theta(z_t^i\mid h_t^i,o_t^i)`, which also sees the real observation,
stands in for the real outcome.  Both share :math:`h_t^i` and are products of
:math:`K` categoricals with :math:`C` classes.

Value-weighted transition bias (estimate of :math:`B_V` in Theorem 1(i) and
Corollary 1, with the learned cost critic :math:`V_C` in place of the model's
cost-to-go):

.. math::

   b_V = \mathbb E\Bigl[V_C(h, z_q) - \tfrac1M \sum_{m=1}^{M} V_C(h, z_p^{(m)})\Bigr],
   \qquad z_q\sim q,\; z_p^{(m)}\sim p .

Per-agent total-variation upper bound (Proposition 1).  For each step,

.. math::

   \mathrm{TV}(q_i, p_i) = \mathbb E_{z\sim q_i}\bigl[(1 - p_i(z)/q_i(z))_+\bigr],

estimated with :math:`M` samples.  The real next-state law is the posterior averaged
over the next observation, so by convexity of total variation the replay average of
this quantity upper-bounds :math:`\epsilon_P^i`.  The inter-agent dependence term
:math:`\eta` of Proposition 1 needs several real next states from one state and is
not estimated here.

Sampling uses a dedicated ``torch.Generator`` (Gumbel-max), so computing the
diagnostics does not change the training random stream.
"""

from __future__ import annotations

from typing import Callable, Mapping

import torch
import torch.nn.functional as F

DIAG_SEED = 20261004
DIAG_SAMPLES = 8  # Monte Carlo samples per replay step
_U_MIN = 1e-12
_U_MAX = 1.0 - 1e-7


def make_generator(device: str | torch.device) -> torch.Generator:
    generator = torch.Generator(device=device)
    generator.manual_seed(DIAG_SEED)
    return generator


def sample_one_hot(logits: torch.Tensor, n_samples: int, generator: torch.Generator) -> torch.Tensor:
    """Gumbel-max samples from categoricals.

    logits: [..., K, C] -> one-hot samples [n_samples, ..., K, C].
    """
    assert n_samples >= 1
    u = torch.rand((n_samples, *logits.shape), generator=generator, device=logits.device, dtype=logits.dtype)
    gumbel = -torch.log(-torch.log(u.clamp(_U_MIN, _U_MAX)))  # [S, ..., K, C]
    index = (logits.unsqueeze(0) + gumbel).argmax(-1)  # [S, ..., K]
    return F.one_hot(index, logits.shape[-1]).to(logits.dtype)  # [S, ..., K, C]


def _log_prob(one_hot: torch.Tensor, logits: torch.Tensor) -> torch.Tensor:
    """Log-probability of one-hot samples [S, ..., K, C] under logits [..., K, C] -> [S, ...]."""
    return (one_hot * F.log_softmax(logits, -1).unsqueeze(0)).sum((-1, -2))


@torch.no_grad()
def tv_upper_bound_mc(
    q_logits: torch.Tensor, p_logits: torch.Tensor, n_samples: int, generator: torch.Generator
) -> torch.Tensor:
    """Monte Carlo TV(q, p) for products of categoricals; logits [..., K, C] -> [...] in [0, 1]."""
    assert q_logits.shape == p_logits.shape, (q_logits.shape, p_logits.shape)
    z = sample_one_hot(q_logits, n_samples, generator)  # [S, ..., K, C]
    log_ratio = _log_prob(z, p_logits) - _log_prob(z, q_logits)  # [S, ...]
    tv = (1.0 - torch.exp(torch.clamp(log_ratio, max=0.0))).mean(0)  # [...]
    assert torch.isfinite(tv).all()
    return tv


@torch.no_grad()
def value_bias(
    critic: Callable[[torch.Tensor], Mapping[str, torch.Tensor]],
    deter: torch.Tensor,
    q_stoch: torch.Tensor,
    p_logits: torch.Tensor,
    n_samples: int,
    generator: torch.Generator,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Cost-critic value at the posterior sample minus its mean over prior samples.

    deter [..., N, D], q_stoch [..., N, K*C] (one-hot sample), p_logits [..., N, K, C].
    Returns (bias [..., N], v_post [..., N]).  Features follow RSSMState.get_features:
    cat(stoch, deter).
    """
    v_post = critic(torch.cat([q_stoch, deter], -1))["cost"].squeeze(-1)  # [..., N]
    z = sample_one_hot(p_logits, n_samples, generator).flatten(-2)  # [S, ..., N, K*C]
    deter_s = deter.unsqueeze(0).expand(n_samples, *deter.shape)  # [S, ..., N, D]
    v_prior = critic(torch.cat([z, deter_s], -1))["cost"].squeeze(-1).mean(0)  # [..., N]
    bias = v_post - v_prior  # [..., N]
    assert torch.isfinite(bias).all()
    return bias, v_post


def _masked_mean(x: torch.Tensor, weight: torch.Tensor) -> float:
    total = weight.sum()
    assert total > 0, "no valid replay steps for diagnostics"
    return float((x * weight).sum() / total)


@torch.no_grad()
def transition_diagnostics(
    model, critic, samples: Mapping[str, torch.Tensor], config, n_samples: int, generator: torch.Generator
) -> dict[str, float]:
    """Diagnostics on one replay batch, with the same rollout as the world-model loss.

    The rollout samples latents from the global RNG and the critic has dropout, so the
    global RNG state is restored and the critic runs in eval mode: training is unaffected.
    """
    cpu_state = torch.random.get_rng_state()
    cuda_states = torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None
    critic_was_training = critic.training
    critic.eval()
    try:
        return _transition_diagnostics(model, critic, samples, config, n_samples, generator)
    finally:
        critic.train(critic_was_training)
        torch.random.set_rng_state(cpu_state)
        if cuda_states is not None:
            torch.cuda.set_rng_state_all(cuda_states)


def _transition_diagnostics(
    model, critic, samples: Mapping[str, torch.Tensor], config, n_samples: int, generator: torch.Generator
) -> dict[str, float]:
    # Imported here so the estimators above stay importable without the env packages
    # that networks.dreamer.rnns pulls in through configs.
    from networks.dreamer.rnns import rollout_representation

    obs, action, last, fake = samples["observation"], samples["action"], samples["last"], samples["fake"]
    time_steps, batch_size, n_agents = obs.shape[0], obs.shape[1], obs.shape[2]
    embed = model.observation_encoder(obs.reshape(-1, n_agents, obs.shape[-1]))
    embed = embed.reshape(time_steps, batch_size, n_agents, -1)  # [T, B, N, E]
    prev_state = model.representation.initial_state(batch_size, n_agents, device=obs.device)
    prior, post, _ = rollout_representation(model.representation, time_steps, embed, action, prev_state, last)
    k, c = config.N_CATEGORICALS, config.N_CLASSES
    q_logits = post.logits.reshape(*post.logits.shape[:-1], k, c)  # [T-1, B, N, K, C]
    p_logits = prior.logits.reshape(*prior.logits.shape[:-1], k, c)  # [T-1, B, N, K, C]
    weight = (1.0 - fake[:-1]).reshape(time_steps - 1, batch_size, n_agents)  # [T-1, B, N]

    tv = tv_upper_bound_mc(q_logits, p_logits, n_samples, generator)  # [T-1, B, N]
    bias, v_post = value_bias(critic, post.deter, post.stoch, p_logits, n_samples, generator)  # [T-1, B, N]
    per_agent_tv = (tv * weight).sum((0, 1)) / weight.sum((0, 1)).clamp_min(1.0)  # [N]
    stats = {
        "Diag/tv_post_prior": _masked_mean(tv, weight),
        "Diag/tv_post_prior_max_agent": float(per_agent_tv.max()),
        "Diag/bv_signed": _masked_mean(bias, weight),
        "Diag/bv_abs": _masked_mean(bias.abs(), weight),
        "Diag/v_post": _masked_mean(v_post, weight),
    }
    for key, value in stats.items():
        assert torch.isfinite(torch.tensor(value)), (key, value)
    return stats
