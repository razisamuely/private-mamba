# Technical Draft: Fine-Tuning Constraints

## Config Changes
1.  **Scale Alignment**: Use `cost_limit=0.1` and `0.5` to match the per-step magnitude of 0.75.
2.  **Learning Rate Control**: Test `laglr=1e-4` and `1e-5` to manage the volatility witnessed at `1e-3`.

## Sampling
- Keep **Cost-Prioritized Sampling** at **15%**.
- High-cost indices tracking remains enabled to ensure the world model stays accurate as clumping decreases.
