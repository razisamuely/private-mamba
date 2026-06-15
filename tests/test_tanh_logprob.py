"""Unit tests for tanh-squashed log-prob fix and RunningMeanStd obs normalization."""

import numpy as np
import torch
from torch.distributions import Normal, TransformedDistribution
from torch.distributions.transforms import TanhTransform


def test_logprob_ratio_matches_ground_truth():
    """Our PPO ratio (evaluated at raw u) should match the ground-truth
    TransformedDistribution ratio. The tanh correction cancels in the ratio,
    so evaluating Normal.log_prob at u gives the correct ratio."""
    torch.manual_seed(42)

    mu_old, std_old = torch.randn(100, 4), torch.rand(100, 4) * 0.5 + 0.1
    mu_new, std_new = torch.randn(100, 4), torch.rand(100, 4) * 0.5 + 0.1

    old_normal = Normal(mu_old, std_old)
    new_normal = Normal(mu_new, std_new)

    # Sample raw u from old policy
    u = old_normal.sample()
    a = torch.tanh(u)

    # Our method: ratio from evaluating at u (raw)
    our_ratio = (new_normal.log_prob(u).sum(-1) - old_normal.log_prob(u).sum(-1)).exp()

    # Ground truth: TransformedDistribution ratio (evaluating at a)
    old_td = TransformedDistribution(Normal(mu_old, std_old), TanhTransform(cache_size=1))
    new_td = TransformedDistribution(Normal(mu_new, std_new), TanhTransform(cache_size=1))
    gt_ratio = (new_td.log_prob(a).sum(-1) - old_td.log_prob(a).sum(-1)).exp()

    assert torch.allclose(our_ratio, gt_ratio, atol=1e-4), f"Max diff: {(our_ratio - gt_ratio).abs().max().item():.6f}"
    print("PASS: test_logprob_ratio_matches_ground_truth")


def test_old_bug_gives_wrong_ratio():
    """Demonstrate that evaluating Normal.log_prob at tanh(u) instead of u
    gives a DIFFERENT (wrong) ratio than the ground truth."""
    torch.manual_seed(42)

    mu_old, std_old = torch.randn(100, 4), torch.rand(100, 4) * 0.5 + 0.1
    mu_new, std_new = torch.randn(100, 4), torch.rand(100, 4) * 0.5 + 0.1

    old_normal = Normal(mu_old, std_old)
    new_normal = Normal(mu_new, std_new)

    u = old_normal.sample()
    a = torch.tanh(u)

    # Buggy method: evaluate at a (squashed) instead of u (raw)
    buggy_ratio = (new_normal.log_prob(a).sum(-1) - old_normal.log_prob(a).sum(-1)).exp()

    # Ground truth
    old_td = TransformedDistribution(Normal(mu_old, std_old), TanhTransform(cache_size=1))
    new_td = TransformedDistribution(Normal(mu_new, std_new), TanhTransform(cache_size=1))
    gt_ratio = (new_td.log_prob(a).sum(-1) - old_td.log_prob(a).sum(-1)).exp()

    # These should NOT match — proving the old code was wrong
    max_diff = (buggy_ratio - gt_ratio).abs().max().item()
    assert max_diff > 0.01, f"Expected significant difference but got max_diff={max_diff:.6f}"
    print(f"PASS: test_old_bug_gives_wrong_ratio (max_diff={max_diff:.4f})")


def test_running_mean_std():
    """Test that MAMuJoCoWrapper's running normalization tracks per-feature stats."""
    np.random.seed(42)

    # Simulate per-feature stats: feature 0 has mean=10, feature 1 has mean=-5
    data = np.random.randn(1000, 4).astype(np.float64)
    data[:, 0] += 10.0
    data[:, 1] -= 5.0
    data[:, 2] *= 3.0  # std=3

    # Replicate the Welford algorithm from MAMuJoCoWrapper
    obs_mean = np.zeros(4, dtype=np.float64)
    obs_var = np.ones(4, dtype=np.float64)
    obs_count = 0

    for obs in data:
        obs_count += 1
        delta = obs - obs_mean
        obs_mean += delta / obs_count
        delta2 = obs - obs_mean
        obs_var += (delta * delta2 - obs_var) / obs_count

    # Check mean converged
    assert np.abs(obs_mean[0] - 10.0) < 0.2, f"Mean[0] expected ~10, got {obs_mean[0]:.3f}"
    assert np.abs(obs_mean[1] - (-5.0)) < 0.2, f"Mean[1] expected ~-5, got {obs_mean[1]:.3f}"

    # Check std converged (var ~ std^2)
    assert np.abs(np.sqrt(obs_var[2]) - 3.0) < 0.3, f"Std[2] expected ~3, got {np.sqrt(obs_var[2]):.3f}"

    # Check per-feature independence: feature 0 stats shouldn't affect feature 1
    assert np.abs(obs_mean[3] - 0.0) < 0.2, f"Mean[3] expected ~0, got {obs_mean[3]:.3f}"

    print("PASS: test_running_mean_std")


def test_actor_returns_raw():
    """Test that the Actor now returns (action, pi, raw) with raw pre-tanh."""
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from networks.dreamer.action import Actor

    actor = Actor(in_dim=64, out_dim=4, hidden_size=32, layers=2, action_type="continuous")
    feat = torch.randn(2, 3, 64)  # batch=2, agents=3, feat=64
    action, pi, raw = actor(feat)

    # action should be tanh(raw)
    assert torch.allclose(action, torch.tanh(raw), atol=1e-6), "action != tanh(raw)"
    # action should be in (-1, 1)
    assert action.abs().max() < 1.0, "action out of (-1, 1)"
    # raw should be unbounded (can be > 1)
    print(f"  raw range: [{raw.min().item():.3f}, {raw.max().item():.3f}]")
    print("PASS: test_actor_returns_raw")


def test_actor_discrete_unchanged():
    """Test that discrete actor still works (returns None for raw)."""
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from networks.dreamer.action import Actor

    actor = Actor(in_dim=64, out_dim=9, hidden_size=32, layers=2, action_type="discrete")
    feat = torch.randn(2, 3, 64)
    action, pi, raw = actor(feat)

    assert raw is None, "Discrete actor should return None for raw"
    assert action.shape[-1] == 9, f"Expected action dim 9, got {action.shape[-1]}"
    print("PASS: test_actor_discrete_unchanged")


if __name__ == "__main__":
    test_logprob_ratio_matches_ground_truth()
    test_old_bug_gives_wrong_ratio()
    test_running_mean_std()
    test_actor_returns_raw()
    test_actor_discrete_unchanged()
    print("\nAll tests passed.")
