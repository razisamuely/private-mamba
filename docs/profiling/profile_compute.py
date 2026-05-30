#!/usr/bin/env python3
"""
Profile compute time of each training phase in Safe Dreamers.

Measures:
  - World model update (Phase 1): model_loss + backward + optimizer step
  - Imagination rollout (Phase 2): actor_rollout (world model forward only, no grad)
  - Actor + critic update (Phase 2): actor_loss + value_loss + backward + optimizer steps

Usage:
  cd /home/corsound/workspace/private-mamba
  python docs/profiling/profile_compute.py
"""
import sys
import time

import torch

import wandb

wandb.init(mode="disabled")

sys.path.insert(0, "/home/corsound/workspace/private-mamba")


from agent.learners.DreamerLearner import initialize_weights
from agent.models.DreamerModel import DreamerModel
from agent.optim.loss import actor_loss, actor_rollout, model_loss, value_loss
from configs.dreamer.DreamerLearnerConfig import DreamerLearnerConfig
from networks.dreamer.action import Actor
from networks.dreamer.critic import AugmentedCritic

# ── Config ────────────────────────────────────────────────────────────────────
config = DreamerLearnerConfig()
config.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {config.DEVICE}")

# ── Models ────────────────────────────────────────────────────────────────────
model = DreamerModel(config).to(config.DEVICE).eval()
actor = Actor(config.FEAT, config.ACTION_SIZE, config.ACTION_HIDDEN, config.ACTION_LAYERS).to(config.DEVICE)
critic = AugmentedCritic(config.FEAT, config.HIDDEN).to(config.DEVICE)
initialize_weights(model, mode="xavier")
initialize_weights(actor)
initialize_weights(critic, mode="xavier")

model_opt = torch.optim.Adam(model.parameters(), lr=config.MODEL_LR)
actor_opt = torch.optim.Adam(actor.parameters(), lr=config.ACTOR_LR)
critic_opt = torch.optim.Adam(critic.parameters(), lr=config.VALUE_LR)

# ── Fake batch ────────────────────────────────────────────────────────────────
T = config.SEQ_LENGTH
B = config.MODEL_BATCH_SIZE
N = 2  # n_agents (starcraft default)
D = config.IN_DIM


def fake_samples(batch_size):
    return {
        "observation": torch.randn(T, batch_size, N, D, device=config.DEVICE),
        "action": torch.zeros(T, batch_size, N, config.ACTION_SIZE, device=config.DEVICE),
        "av_action": None,
        "reward": torch.randn(T, batch_size, N, 1, device=config.DEVICE),
        "cost": torch.randn(T, batch_size, N, 1, device=config.DEVICE),
        "done": torch.zeros(T, batch_size, N, 1, device=config.DEVICE),
        "fake": torch.zeros(T, batch_size, N, 1, device=config.DEVICE),
        "last": torch.zeros(T, batch_size, N, 1, device=config.DEVICE),
    }


# ── Timing helper ─────────────────────────────────────────────────────────────
def timeit(fn, n=20, warmup=5):
    for _ in range(warmup):
        fn()
    if config.DEVICE == "cuda":
        torch.cuda.synchronize()
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        if config.DEVICE == "cuda":
            torch.cuda.synchronize()
        times.append((time.perf_counter() - t0) * 1000)
    return sum(times) / len(times), min(times), max(times)


# ── Phase 1: World model update ───────────────────────────────────────────────
def phase1():
    s = fake_samples(config.MODEL_BATCH_SIZE)
    model.train()
    loss = model_loss(
        config,
        model,
        s["observation"],
        s["action"],
        s["av_action"],
        s["reward"],
        s["cost"],
        s["done"],
        s["fake"],
        s["last"],
    )
    model_opt.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), config.GRAD_CLIP)
    model_opt.step()
    model.eval()


# ── Phase 2a: Imagination rollout (world model forward only) ──────────────────
def phase2_rollout():
    s = fake_samples(config.BATCH_SIZE)
    actor_rollout(s["observation"], s["action"], s["last"], model, actor, critic, config)


# ── Phase 2b: Actor + critic update ──────────────────────────────────────────
def phase2_update():
    s = fake_samples(config.BATCH_SIZE)
    actions, av_actions, old_policy, imag_feat, returns, cost_returns, _ = actor_rollout(
        s["observation"], s["action"], s["last"], model, actor, critic, config
    )

    value_pred = critic(imag_feat)["value"]
    adv = returns.detach() - value_pred.detach()
    cost_value_pred = critic(imag_feat)["cost"]
    cost_adv = cost_returns.detach() - cost_value_pred.detach()
    lagrangian_adv = adv - 0.1 * cost_adv

    inds = torch.randperm(actions.shape[0])
    idx = inds[:2000]
    a_loss = actor_loss(
        imag_feat[idx],
        actions[idx],
        av_actions[idx] if av_actions is not None else None,
        old_policy[idx],
        lagrangian_adv[idx],
        actor,
        config.ENTROPY,
    )
    actor_opt.zero_grad()
    a_loss.backward()
    torch.nn.utils.clip_grad_norm_(actor.parameters(), config.GRAD_CLIP_POLICY)
    actor_opt.step()

    v_loss = value_loss(critic, imag_feat[idx], returns[idx], cost_returns[idx])
    critic_opt.zero_grad()
    v_loss.backward()
    torch.nn.utils.clip_grad_norm_(critic.parameters(), config.GRAD_CLIP_POLICY)
    critic_opt.step()


# ── Run ───────────────────────────────────────────────────────────────────────
print("\nProfiling... (20 runs each, 5 warmup)\n")

m_avg, m_min, m_max = timeit(phase1)
r_avg, r_min, r_max = timeit(phase2_rollout)
u_avg, u_min, u_max = timeit(phase2_update)

total = m_avg + r_avg + u_avg
print(f"{'Phase':<40} {'Avg (ms)':>10} {'Min':>8} {'Max':>8} {'% total':>8}")
print("-" * 76)
print(f"{'Phase 1: World model update':<40} {m_avg:>10.1f} {m_min:>8.1f} {m_max:>8.1f} {100*m_avg/total:>7.1f}%")
print(f"{'Phase 2a: Imagination rollout':<40} {r_avg:>10.1f} {r_min:>8.1f} {r_max:>8.1f} {100*r_avg/total:>7.1f}%")
print(f"{'Phase 2b: Actor+critic update':<40} {u_avg:>10.1f} {u_min:>8.1f} {u_max:>8.1f} {100*u_avg/total:>7.1f}%")
print("-" * 76)
print(f"{'Total per training iteration':<40} {total:>10.1f}")
print(
    f"\nWorld model (Phase 1) vs policy (Phase 2a+2b): {m_avg:.1f}ms vs {r_avg+u_avg:.1f}ms "
    f"({m_avg/(r_avg+u_avg):.1f}x)"
)
