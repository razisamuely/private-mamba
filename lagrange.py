from __future__ import annotations

from collections import deque

import numpy as np
import torch


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


class PIDLagrangian:  # noqa: B024
    """PID version of Lagrangian.

    Similar to the :class:`Lagrange` module, this module implements the PID version of the
    lagrangian method.

    .. note::
        The PID-Lagrange is more general than the Lagrange, and can be used in any policy gradient
        algorithm. As PID_Lagrange use the PID controller to control the lagrangian multiplier, it
        is more stable than the naive Lagrange.

    Args:
        pid_kp (float): The proportional gain of the PID controller.
        pid_ki (float): The integral gain of the PID controller.
        pid_kd (float): The derivative gain of the PID controller.
        pid_d_delay (int): The delay of the derivative term.
        pid_delta_p_ema_alpha (float): The exponential moving average alpha of the delta_p.
        pid_delta_d_ema_alpha (float): The exponential moving average alpha of the delta_d.
        sum_norm (bool): Whether to use the sum norm.
        diff_norm (bool): Whether to use the diff norm.
        penalty_max (int): The maximum penalty.
        lagrangian_multiplier_init (float): The initial value of the lagrangian multiplier.
        cost_limit (float): The cost limit.

    References:
        - Title: Responsive Safety in Reinforcement Learning by PID Lagrangian Methods
        - Authors: Joshua Achiam, David Held, Aviv Tamar, Pieter Abbeel.
        - URL: `PID Lagrange <https://arxiv.org/abs/2007.03964>`_
    """

    # pylint: disable-next=too-many-arguments
    def __init__(
        self,
        config,
    ) -> None:
        """Initialize an instance of :class:`PIDLagrangian`."""
        self._pid_kp: float = config.pid.kp
        self._pid_ki: float = config.pid.ki
        self._pid_kd: float = config.pid.kd
        self._pid_d_delay = config.pid.d_delay
        self._pid_delta_p_ema_alpha: float = config.pid.delta_p_ema_alpha
        self._pid_delta_d_ema_alpha: float = config.pid.delta_d_ema_alpha
        self._penalty_max: int = config.pid.penalty_max
        self._sum_norm: bool = config.pid.sum_norm
        self._diff_norm: bool = config.pid.diff_norm
        self._pid_i: float = config.pid.lagrangian_multiplier_init
        self._cost_ds: deque[float] = deque(maxlen=self._pid_d_delay)
        self._cost_ds.append(0.0)
        self._delta_p: float = 0.0
        self._cost_d: float = 0.0
        self._pid_d: float = 0.0
        self._cost_limit: float = config.cost_limit
        self._cost_penalty: float = config.pid.init_penalty
        self._use_cost_decay: bool = config.pid.use_cost_decay
        self._current_cost_limit: float = config.pid.init_cost_limit
        if self._use_cost_decay:
            self._steps = [config.pid.decay_time_step * (i + 1) for i in range(config.pid.decay_num)]
            self._limits = [
                max(config.pid.init_cost_limit - i * config.pid.decay_limit_step, config.cost_limit)
                for i in range(config.pid.decay_num)
            ]

    @property
    def lagrange_penalty(self) -> float:
        """The lagrangian multiplier."""
        return self._cost_penalty

    @property
    def delta_p(self) -> float:
        """The lagrangian multiplier p."""
        return self._delta_p

    @property
    def pid_i(self) -> float:
        """The lagrangian multiplier i."""
        return self._pid_i

    @property
    def pid_d(self) -> float:
        """The lagrangian multiplier d."""
        return self._pid_d

    def pid_update(self, epcost, step) -> None:
        r"""Update the PID controller.

        PID controller update the lagrangian multiplier following the next equation:

        .. math::

            \lambda_{t+1} = \lambda_t + (K_p e_p + K_i \int e_p dt + K_d \frac{d e_p}{d t}) \eta

        where :math:`e_p` is the error between the current episode cost and the cost limit,
        :math:`K_p`, :math:`K_i`, :math:`K_d` are the PID parameters, and :math:`\eta` is the
        learning rate.

        Args:
            ep_cost_avg (float): The average cost of the current episode.
        """
        ep_cost_avg = epcost
        if self._use_cost_decay:
            for i, threshold in enumerate(self._steps):
                if step < threshold:
                    self._current_cost_limit = self._limits[i]
                    break
            else:
                self._current_cost_limit = self._cost_limit
        else:
            self._current_cost_limit = self._cost_limit

        delta = float(ep_cost_avg - self._current_cost_limit)
        self._pid_i = max(0.0, self._pid_i + delta * self._pid_ki)
        if self._diff_norm:
            self._pid_i = max(0.0, min(1.0, self._pid_i))
        a_p = self._pid_delta_p_ema_alpha
        self._delta_p *= a_p
        self._delta_p += (1 - a_p) * delta
        a_d = self._pid_delta_d_ema_alpha
        self._cost_d *= a_d
        self._cost_d += (1 - a_d) * float(ep_cost_avg)
        self._pid_d = max(0.0, self._cost_d - self._cost_ds[0])
        pid_o = self._pid_kp * self._delta_p + self._pid_i + self._pid_kd * self._pid_d
        self._cost_penalty = max(0.0, pid_o)
        if self._diff_norm:
            self._cost_penalty = min(1.0, self._cost_penalty)
        if not (self._diff_norm or self._sum_norm):
            self._cost_penalty = min(self._cost_penalty, self._penalty_max)
        self._cost_ds.append(self._cost_d)
        self._cost_penalty = np.clip(self._cost_penalty, 0.0, self._penalty_max)
        return self._cost_penalty, self._pid_d, self._pid_i, self._delta_p
