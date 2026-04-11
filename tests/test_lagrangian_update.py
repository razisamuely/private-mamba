import torch

from lagrange import BasicLagrange


def make_lag(cost_limit=0.1, lr=1e-3):
    return BasicLagrange(cost_limit=cost_limit, lagrangian_multiplier_init=0.0, lr=lr, device="cpu")


def test_lambda_rises_when_cost_above_limit():
    lag = make_lag()
    lag.update(torch.tensor(0.5))
    assert lag.lambda_ > 0


def test_lambda_stays_zero_when_cost_below_limit():
    lag = make_lag()
    lag.update(torch.tensor(0.05))
    assert lag.lambda_ == 0


def test_lambda_scale_with_real_vs_imagined():
    """Real episode cost (~0.2) and imagined batch cost (~0.4) produce different λ values."""
    lag_real = make_lag(lr=1e-3)
    lag_imag = make_lag(lr=1e-3)
    lag_real.update(torch.tensor(0.2))
    lag_imag.update(torch.tensor(0.4))
    assert lag_real.lambda_ < lag_imag.lambda_
