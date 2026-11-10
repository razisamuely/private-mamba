"""`--seed` reaches the generators and the environment (#36).

Before #36 the flag only named the run, so these are the two properties that
were missing: the same seed draws the same numbers, and the seed reaches the
environment through the curriculum config the workers are handed.
"""

import os
import random
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from configs.EnvConfigs import EnvCurriculumConfig  # noqa: E402
from env.mpe.vmas_simple_spread import VmasSpread  # noqa: E402
from environments import Env  # noqa: E402
from seeding import seed_everything  # noqa: E402


def _draws():
    return (random.random(), float(np.random.rand()), float(torch.rand(1)))


def test_same_seed_draws_the_same_numbers():
    seed_everything(7)
    first = _draws()
    seed_everything(7)
    assert _draws() == first


def test_different_seeds_draw_different_numbers():
    seed_everything(7)
    first = _draws()
    seed_everything(8)
    assert _draws() != first


def test_curriculum_config_forwards_the_seed_to_the_environment():
    """The workers are handed an EnvCurriculumConfig, never the env config."""

    class Recorder(VmasSpread):
        def __init__(self):
            self.seen = None

        def set_seed(self, seed):
            self.seen = seed

    recorder = Recorder()
    EnvCurriculumConfig((recorder,), (100,), Env.SIMPLE_SPREAD).set_seed(11)
    assert recorder.seen == 11


def test_environments_without_seeding_support_ignore_the_seed():
    """The base no-op keeps the retired Flatland and VMAS paths working."""

    VmasSpread("simple_spread").set_seed(11)
