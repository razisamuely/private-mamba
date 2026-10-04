"""Mirror WandB logging to a local JSON-lines file, so runs can be analyzed without WandB.

Every call to ``Run.log`` is forwarded unchanged and also appended to ``path`` as one JSON
object with a running ``_line`` index.  Scalars (Python numbers, single-element numpy
arrays or torch tensors) are written as floats, non-finite values as ``NaN``/``Infinity``;
anything else (histograms, media) is skipped.

The class method must be patched *before* the first ``wandb.init``: init binds
``wandb.log`` to the run's method at that moment, and the learner calls ``wandb.init``
a second time, which rebinds it from the (patched) class.
"""

from __future__ import annotations

import json
import numbers
from pathlib import Path
from typing import Any, Callable, Optional


def to_scalar(value: Any) -> Optional[float]:
    """Float for a scalar-like value, ``None`` for anything else."""
    if isinstance(value, numbers.Number):
        return float(value)
    size = getattr(value, "size", None)
    numel = getattr(value, "numel", None)
    try:
        n = numel() if callable(numel) else (size if isinstance(size, int) else None)
    except TypeError:
        n = None
    if n == 1 and hasattr(value, "item"):
        return float(value.item())
    return None


def tee_log_method(cls: type, path: str | Path) -> Callable[[], None]:
    """Patch ``cls.log`` to also write each call to ``path``; returns a restore function."""
    original = cls.log
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    handle = target.open("a", encoding="utf-8", buffering=1)  # line-buffered: survives a crash
    state = {"line": 0}

    def log(self, data, *args, **kwargs):
        result = original(self, data, *args, **kwargs)
        row: dict[str, float] = {"_line": state["line"]}
        for key, value in dict(data).items():
            scalar = to_scalar(value)
            if scalar is not None:
                row[key] = scalar
        state["line"] += 1
        handle.write(json.dumps(row) + "\n")
        return result

    cls.log = log

    def restore() -> None:
        cls.log = original
        handle.close()

    return restore
