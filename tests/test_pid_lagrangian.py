import pytest
import torch

from lagrange import BasicLagrange, PIDLagrangian


def make_pid(cost_limit: float = 1.0, **kwargs) -> PIDLagrangian:
    defaults = dict(pid_kp=1.0, pid_ki=0.01, pid_kd=1.0, device="cpu")
    defaults.update(kwargs)
    return PIDLagrangian(cost_limit=cost_limit, **defaults)


def test_pid_update_sustained_violation_increases_beta():
    lag = make_pid(cost_limit=1.0)
    betas = []
    for _ in range(50):
        lag.update(torch.tensor(5.0))
        betas.append(lag.lambda_.item())
    assert betas[-1] > betas[0] > 0
    # I-term keeps accumulating under sustained violation
    assert betas[-1] > betas[len(betas) // 2]


def test_pid_update_cost_below_limit_relaxes_beta_nonnegative():
    lag = make_pid(cost_limit=1.0)
    for _ in range(20):
        lag.update(5.0)
    beta_high = lag.lambda_.item()
    for _ in range(100):
        lag.update(0.0)
    beta_low = lag.lambda_.item()
    assert beta_low < beta_high
    assert beta_low >= 0.0


def test_pid_beta_never_negative_when_cost_always_below_limit():
    lag = make_pid(cost_limit=10.0)
    for _ in range(100):
        lag.update(0.0)
        assert lag.lambda_.item() >= 0.0


def test_pid_i_only_matches_basic_lagrange():
    lr = 1e-3
    pid = make_pid(cost_limit=1.0, pid_kp=0.0, pid_ki=lr, pid_kd=0.0)
    basic = BasicLagrange(cost_limit=1.0, lagrangian_multiplier_init=0.0, lr=lr, device="cpu")
    for cost in [5.0, 3.0, 0.5, 2.0, 0.0]:
        pid.update(cost)
        basic.update(torch.tensor(cost))
        assert pid.lambda_.item() == pytest.approx(basic.lambda_.item(), abs=1e-6)


def test_pid_beta_clipped_at_penalty_max():
    lag = make_pid(cost_limit=0.0, pid_ki=10.0, penalty_max=2.0)
    for _ in range(100):
        lag.update(100.0)
    assert lag.lambda_.item() == pytest.approx(2.0)
