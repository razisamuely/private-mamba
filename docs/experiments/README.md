# Experiment History & Success Log

This log tracks the motivation, changes, and final outcomes of all Safe Dreamer experiments in StarCraft.

## 🏆 Current Best Configuration (Stable Collision Avoidance)
- **Map**: `8m`
- **Cost Type**: `collision`
- **Lagrangian Learning Rate**: `1e-4`
- **Cost Limit (per step slice)**: `0.1`
- **Sampling Strategy**: Cost-Prioritized (15% High-Cost samples)

---

## 📅 Experiment Registry

| Experiment ID | Title | Status | Outcome | Key Lesson |
| :--- | :--- | :--- | :--- | :--- |
| **04** | [Collision Fine-Tuning](./4-collision-cost-fine-tuning/) | **SUCCESS** | Cost 30 -> 1.5 | Scale Alignment & Low LagLR. |
| **03** | [Collision Fix Pilot](./3-collision-cost-fix/) | Partial | Improved Model | World Model needs Priority Sampling. |
| **02** | [Initial Collision Cost](./2-collision-cost/) | Failed | Blind World Model | Step-cost is too sparse for random buffers. |

---

## 📈 Technical Knowledge Base (Cheatsheet)
- **Cost Scale**: Environment team-cost is episodic (summed), but Dreamer thinks in 15-step slices. Use `0.1-0.5` limits for 15-step horizons.
- **World Model Accuracy**: Sparse costs require **Prioritized Sampling** (15% ratio) to prevent the "blind model" where prediction stays at 1.0.
- **Stability**: `laglr=1e-3` is too aggressive for accurate world models. Use `1e-4` for smooth convergence.
