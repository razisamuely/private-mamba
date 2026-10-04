import itertools
from types import SimpleNamespace

import pytest
import torch
import torch.nn as nn

from agent.optim.diagnostics import make_generator, sample_one_hot, tv_upper_bound_mc, value_bias


def exact_tv_product(q_logits: torch.Tensor, p_logits: torch.Tensor) -> float:
    """Exact TV between two products of categoricals by enumeration; logits [K, C]."""
    q = torch.softmax(q_logits, -1)
    p = torch.softmax(p_logits, -1)
    k, c = q.shape
    total = 0.0
    for idx in itertools.product(range(c), repeat=k):
        qz = float(torch.prod(torch.stack([q[j, idx[j]] for j in range(k)])))
        pz = float(torch.prod(torch.stack([p[j, idx[j]] for j in range(k)])))
        total += abs(qz - pz)
    return 0.5 * total


def test_tv_is_zero_for_identical_distributions():
    logits = torch.randn(4, 2, 3, 5, generator=torch.Generator().manual_seed(0))
    tv = tv_upper_bound_mc(logits, logits.clone(), 64, make_generator("cpu"))
    assert torch.allclose(tv, torch.zeros_like(tv))


def test_tv_matches_exact_value_on_small_product():
    g = torch.Generator().manual_seed(1)
    q_logits = torch.randn(3, 4, generator=g)  # K=3 categoricals, C=4 classes
    p_logits = torch.randn(3, 4, generator=g)
    exact = exact_tv_product(q_logits, p_logits)
    estimate = float(tv_upper_bound_mc(q_logits, p_logits, 40000, make_generator("cpu")))
    assert estimate == pytest.approx(exact, abs=0.01)
    assert 0.0 <= estimate <= 1.0


def test_sample_one_hot_frequencies_match_softmax():
    logits = torch.tensor([[0.0, 1.0, -1.0]])  # [K=1, C=3]
    samples = sample_one_hot(logits, 60000, make_generator("cpu"))  # [S, 1, 3]
    assert torch.all(samples.sum(-1) == 1)
    freq = samples.mean(0)[0]
    assert torch.allclose(freq, torch.softmax(logits, -1)[0], atol=0.01)


def test_value_bias_matches_closed_form_for_linear_critic():
    k, c, d, n = 2, 3, 4, 2
    g = torch.Generator().manual_seed(2)
    w = torch.randn(k * c, generator=g)

    def critic(features: torch.Tensor):
        # V(z, h) = w . z, ignoring h; shape [..., N, 1]
        return {"cost": (features[..., : k * c] * w).sum(-1, keepdim=True)}

    p_logits = torch.randn(5, n, k, c, generator=g)  # [B, N, K, C]
    q_stoch = torch.nn.functional.one_hot(torch.randint(0, c, (5, n, k), generator=g), c).float().flatten(-2)
    deter = torch.randn(5, n, d, generator=g)
    bias, v_post = value_bias(critic, deter, q_stoch, p_logits, 40000, make_generator("cpu"))
    expected_prior = (torch.softmax(p_logits, -1).flatten(-2) * w).sum(-1)  # [B, N]
    expected = (q_stoch * w).sum(-1) - expected_prior
    assert bias.shape == (5, n)
    assert torch.allclose(v_post, (q_stoch * w).sum(-1))
    assert torch.allclose(bias, expected, atol=0.05)


def test_diagnostics_leave_global_rng_untouched():
    torch.manual_seed(123)
    expected = torch.rand(3)
    torch.manual_seed(123)
    logits = torch.zeros(2, 3, 4)
    tv_upper_bound_mc(logits, logits + 0.1, 16, make_generator("cpu"))
    assert torch.equal(torch.rand(3), expected)


def test_transition_diagnostics_end_to_end_with_rssm():
    rnns = pytest.importorskip("networks.dreamer.rnns", reason="needs the project's env packages")
    critic_module = pytest.importorskip("networks.dreamer.critic")
    from agent.optim.diagnostics import transition_diagnostics

    config = SimpleNamespace(
        N_CATEGORICALS=4, N_CLASSES=3, STOCHASTIC=12, DETERMINISTIC=16, ACTION_SIZE=5, EMBED=8, HIDDEN=16
    )
    n_agents, obs_dim, t, b = 3, 7, 6, 2
    transition = rnns.RSSMTransition(config, hidden_size=16)
    model = SimpleNamespace(
        observation_encoder=nn.Linear(obs_dim, config.EMBED),
        representation=rnns.RSSMRepresentation(config, transition),
    )
    critic = critic_module.AugmentedCritic(config.STOCHASTIC + config.DETERMINISTIC, config.HIDDEN)
    g = torch.Generator().manual_seed(3)
    actions = torch.nn.functional.one_hot(torch.randint(0, 5, (t, b, n_agents), generator=g), 5).float()
    fake = torch.zeros(t, b, n_agents, 1)
    fake[-2:, 1] = 1.0  # padded steps must be ignored
    samples = {
        "observation": torch.randn(t, b, n_agents, obs_dim, generator=g),
        "action": actions,
        "last": torch.zeros(t, b, n_agents, 1),
        "fake": fake,
    }
    critic.train()
    torch.manual_seed(5)
    expected_draw = torch.rand(2)
    torch.manual_seed(5)
    stats = transition_diagnostics(model, critic, samples, config, 8, make_generator("cpu"))
    assert torch.equal(torch.rand(2), expected_draw), "diagnostics changed the global RNG stream"
    assert critic.training, "critic mode must be restored"
    assert set(stats) == {
        "Diag/tv_post_prior",
        "Diag/tv_post_prior_max_agent",
        "Diag/bv_signed",
        "Diag/bv_abs",
        "Diag/v_post",
    }
    assert 0.0 <= stats["Diag/tv_post_prior"] <= stats["Diag/tv_post_prior_max_agent"] <= 1.0
    assert stats["Diag/bv_abs"] >= abs(stats["Diag/bv_signed"])
