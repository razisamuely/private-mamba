from __future__ import annotations

from collections import deque
from enum import Enum

import numpy as np
import torch


class BasicLagrange:
    def __init__(self, cost_limit, lagrangian_multiplier_init, lr, device="cuda"):
        self.cost_limit = cost_limit
        self.lambda_ = torch.tensor(lagrangian_multiplier_init, requires_grad=False, device=device)
        self.lr = lr

    def update(self, cost):
        with torch.no_grad():
            if torch.is_tensor(cost):
                cost = cost.item()
            self.lambda_ += self.lr * (cost - self.cost_limit)
            self.lambda_ = self.lambda_.clamp(min=0)


class Lagrange:
    def __init__(
        self,
        cost_limit: float,
        lagrangian_multiplier_init: float = 0.001,
        penalty_multiplier_init: float = 5e-9,
        nu: float = 1e-5,
    ):
        self.cost_limit = cost_limit
        self.nu = nu

        # Lagrangian multiplier (λ)
        self._lagrangian_multiplier = torch.nn.Parameter(
            torch.tensor(max(lagrangian_multiplier_init, 0.0), dtype=torch.float32),
            requires_grad=False,  # Updated manually following paper
        )

        # Penalty multiplier (μ)
        self.penalty_multiplier = max(penalty_multiplier_init, 0.0)

    @property
    def lagrangian_multiplier(self) -> torch.Tensor:
        return torch.clamp(self._lagrangian_multiplier, min=0.0)

    def update_multipliers(self, cost_return_batch: torch.Tensor) -> torch.Tensor:
        """Update λ and μ following Augmented Lagrangian method from paper."""

        # Compute constraint violation (batch average)
        delta = (cost_return_batch.mean() - self.cost_limit).item()
        lambda_k = self.lagrangian_multiplier.item()
        mu_k = self.penalty_multiplier
        cond = lambda_k + mu_k * delta
        self._lagrangian_multiplier.data = torch.tensor(max(0.0, cond), dtype=torch.float32)
        if cond > 0.0:
            psi = lambda_k * delta + 0.5 * mu_k * delta * delta
        else:
            psi = -0.5 * lambda_k * lambda_k / mu_k

        self.penalty_multiplier = max(mu_k, mu_k * (1 + self.nu))
        self.penalty_multiplier = min(self.penalty_multiplier, 1.0)

        return psi


class LagMode(str, Enum):
    """Which multiplier-update rule to use."""

    BASIC = "basic"
    PID = "pid"


class PIDLagrangian:
    """PID controller on the Lagrangian multiplier (plain-PID variant).

    Same interface as :class:`BasicLagrange` (`.lambda_`, `.update(cost)`).
    The I-term alone with ``ki == lr`` reproduces :class:`BasicLagrange`.

    References:
        - Title: Responsive Safety in Reinforcement Learning by PID Lagrangian Methods
        - Authors: Adam Stooke, Joshua Achiam, Pieter Abbeel.
        - URL: `PID Lagrange <https://arxiv.org/abs/2007.03964>`_
    """

    def __init__(
        self,
        cost_limit: float,
        pid_kp: float = 1.0,
        pid_ki: float = 1e-5,
        pid_kd: float = 1.0,
        pid_d_delay: int = 10,
        delta_p_ema_alpha: float = 0.95,
        delta_d_ema_alpha: float = 0.9,
        penalty_max: float = 100.0,
        lagrangian_multiplier_init: float = 0.0,
        device: str = "cuda",
    ) -> None:
        self.cost_limit = cost_limit
        self._pid_kp = pid_kp
        self._pid_ki = pid_ki
        self._pid_kd = pid_kd
        self._penalty_max = penalty_max
        self._delta_p_ema_alpha = delta_p_ema_alpha
        self._delta_d_ema_alpha = delta_d_ema_alpha
        self._pid_i: float = max(lagrangian_multiplier_init, 0.0)
        self._cost_ds: deque[float] = deque(maxlen=pid_d_delay)
        self._cost_ds.append(0.0)
        self._delta_p: float = 0.0
        self._cost_d: float = 0.0
        self._pid_d: float = 0.0
        self._cost_penalty: float = max(lagrangian_multiplier_init, 0.0)
        self._device = device

    @property
    def lambda_(self) -> torch.Tensor:
        """Current multiplier, as a tensor (interface parity with BasicLagrange)."""
        return torch.tensor(self._cost_penalty, dtype=torch.float32, device=self._device)

    @property
    def delta_p(self) -> float:
        return self._delta_p

    @property
    def pid_i(self) -> float:
        return self._pid_i

    @property
    def pid_d(self) -> float:
        return self._pid_d

    def update(self, cost) -> None:
        """Update the multiplier from the latest episode cost (float or tensor)."""
        if torch.is_tensor(cost):
            cost = cost.item()
        delta = float(cost - self.cost_limit)
        # I: accumulate violation (== BasicLagrange when kp = kd = 0)
        self._pid_i = max(0.0, self._pid_i + delta * self._pid_ki)
        # P: EMA-smoothed current violation
        a_p = self._delta_p_ema_alpha
        self._delta_p = a_p * self._delta_p + (1 - a_p) * delta
        # D: increase of smoothed cost over the delay window (only if rising)
        a_d = self._delta_d_ema_alpha
        self._cost_d = a_d * self._cost_d + (1 - a_d) * float(cost)
        self._pid_d = max(0.0, self._cost_d - self._cost_ds[0])
        pid_o = self._pid_kp * self._delta_p + self._pid_i + self._pid_kd * self._pid_d
        self._cost_penalty = float(np.clip(pid_o, 0.0, self._penalty_max))
        self._cost_ds.append(self._cost_d)
