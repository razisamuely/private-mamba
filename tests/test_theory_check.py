import json
import math

import pytest

from tools.theory_check import WINDOW, aggregate, main, summarize_run


def write_run(path, n_episodes=20, length=100, cost=2.0, imag=0.03, beta_end=0.4):
    """Synthetic log: per episode, three main/* rows with steps, then model/agent/diag rows."""
    lines = []
    steps = 0
    for e in range(n_episodes):
        steps += length
        lines.append({"main/winrate": 0.0, "steps": steps})
        lines.append({"main/cost": cost, "steps": steps})
        lines.append({"main/score": 10.0, "steps": steps})
        lines.append({"Model/cost_loss": 0.004, "Model/div": 0.05})
        lines.append({"Value/Cost": imag})
        lines.append({"Agent/Lagrangian": beta_end * (e + 1) / n_episodes})
        lines.append(
            {
                "Diag/bv_signed": -0.01,
                "Diag/bv_abs": 0.02,
                "Diag/v_post": 0.4,
                "Diag/tv_post_prior": 0.7,
                "Diag/tv_post_prior_max_agent": 0.8,
            }
        )
    path.write_text("\n".join(json.dumps(dict(_line=i, **row)) for i, row in enumerate(lines)) + "\n")
    return path


def test_summary_matches_hand_computation(tmp_path):
    s = summarize_run(write_run(tmp_path / "metrics.jsonl"), tail=0.5)
    assert s.max_steps == 2000
    assert s.tail_episodes == 11  # episodes ending at steps >= 1000
    assert s.real_window == pytest.approx(WINDOW * 2.0 / 100)
    assert s.imag_window == pytest.approx(WINDOW * 0.03)
    assert s.abs_gap == pytest.approx(WINDOW * 0.01)
    assert s.rel_gap == pytest.approx(0.5)
    assert s.kl_per_agent == pytest.approx(32 * 0.05)
    assert s.pinsker_bound == pytest.approx(math.sqrt(32 * 0.05 / 2))
    assert s.bv_rel == pytest.approx(0.05)
    assert s.beta_final == pytest.approx(0.4)


def test_window_constant():
    assert WINDOW == pytest.approx(13.994, abs=1e-3)


def test_truncated_last_line_is_skipped(tmp_path):
    path = write_run(tmp_path / "metrics.jsonl")
    path.write_text(path.read_text() + '{"main/cost": 1.0, "ste')
    s = summarize_run(path)
    assert s.tail_episodes > 0


def test_aggregate_and_cli(tmp_path, capsys):
    (tmp_path / "s1").mkdir()
    (tmp_path / "s2").mkdir()
    write_run(tmp_path / "s1" / "metrics.jsonl", cost=2.0)
    write_run(tmp_path / "s2" / "metrics.jsonl", cost=4.0)
    out = tmp_path / "summary.csv"
    assert main([str(tmp_path), "--out", str(out)]) == 0
    assert out.read_text().count("\n") == 3  # header + 2 runs
    agg = aggregate([summarize_run(tmp_path / "s1" / "metrics.jsonl"), summarize_run(tmp_path / "s2" / "metrics.jsonl")])
    mean, sd, n = agg["real_window"]
    assert n == 2 and mean == pytest.approx(WINDOW * 0.03)
    assert "2 run(s)" in capsys.readouterr().out
