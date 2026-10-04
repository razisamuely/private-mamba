import json
import math

import numpy as np
import torch

from local_log import tee_log_method, to_scalar


class FakeRun:
    def __init__(self):
        self.calls = []

    def log(self, data, step=None):
        self.calls.append((dict(data), step))
        return "ok"


def test_to_scalar_handles_numbers_tensors_arrays():
    assert to_scalar(3) == 3.0
    assert to_scalar(2.5) == 2.5
    assert to_scalar(torch.tensor(1.5)) == 1.5
    assert to_scalar(torch.tensor([4.0])) == 4.0
    assert to_scalar(np.float32(0.25)) == 0.25
    assert to_scalar(np.array([7.0])) == 7.0
    assert to_scalar(torch.zeros(3)) is None
    assert to_scalar("text") is None


def test_tee_forwards_and_writes_jsonl(tmp_path):
    path = tmp_path / "logs" / "metrics.jsonl"
    restore = tee_log_method(FakeRun, path)
    try:
        run = FakeRun()  # created after patching, like wandb.init
        assert run.log({"main/cost": torch.tensor(3.0), "steps": 120}) == "ok"
        run.log({"Agent/Lagrangian": 0.5, "hist": torch.zeros(4)}, step=7)
        run.log({"Model/div": float("nan")})
    finally:
        restore()
    assert run.calls[1] == ({"Agent/Lagrangian": 0.5, "hist": run.calls[1][0]["hist"]}, 7)
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert rows[0] == {"_line": 0, "main/cost": 3.0, "steps": 120.0}
    assert rows[1] == {"_line": 1, "Agent/Lagrangian": 0.5}
    assert rows[2]["_line"] == 2 and math.isnan(rows[2]["Model/div"])


def test_restore_removes_patch(tmp_path):
    original = FakeRun.log
    restore = tee_log_method(FakeRun, tmp_path / "m.jsonl")
    assert FakeRun.log is not original
    restore()
    assert FakeRun.log is original
