# Experiment 4 Results: Success

## **Summary**
This experiment validated that the **Prioritized Sampling** and **Scale Alignment** correctly resolve the "clumping" problem in Safe Dreamer for SMAC.

## **Visual Results**
- **Original Cost**: ~30–45 (Total clumping)
- **Current Cost**: ~0.5–2.5 (Stable spacing)
- **Stability**: The Lagrangian multiplier reached a steady state without oscillating.

## **Key Changes Made**
1.  **Memory**: `DreamerMemory.py` now tracks `high_cost_indices` and samples them with 15% priority.
2.  **Configuration**: 
    - `cost_limit`: Reduced to **0.1 or 0.5** (matches 15-step horizon).
    - `laglr`: Reduced to **1e-4 or 1e-5** (prevents "over-correction" jitter).
3.  **Accuracy**: World Model now accurately predicts cost magnitudes (matched grey/blue lines).

## **Conclusion**
The agent is now safe and the World Model is no longer "blind" to cost violations.

---

**Next Experiment**: Verify if this safety formation has a hidden impact on Battle Performance (Winrate).
