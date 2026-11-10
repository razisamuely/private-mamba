"""Seed the global random number generators from ``--seed``.

Until #36 ``--seed`` only *named* a run: the value reached
``Experiment.random_seed``, which nothing outside the retired Flatland path ever
read.  Runs still differed from one another -- the unseeded numpy, torch and
CUDA generators, and the order in which Ray workers finished, supply plenty of
randomness -- but no run could be repeated.

Every run recorded before this module exists is unseeded, and Appendix C of the
thesis says so.  Those runs are *not* rerun: seeding changes which sample a
given seed label draws, so seeded and unseeded runs of the same configuration
must not be pooled.
"""

import random

import numpy as np
import torch


def seed_everything(seed: int) -> None:
    """Seed Python, numpy and torch (CPU and every CUDA device) in this process.

    Call once per process, before anything builds a network or an environment.
    Each Ray worker is its own process with its own generators, so each has to
    call this itself -- and with a *different* seed, or every worker would draw
    the same action noise and collect near-identical episodes.
    """

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
