# Update: one more 8m variant (3 jobs) and new diagnostics

I pushed two more commits to `feat/aamas-8m-ablation`:

- `ef4fb37` adds `--lag_signal imagined`. It feeds the multiplier the mean imagined cost return, as
  the code did before `6c05450`, so we can compare the two multiplier inputs on the same code. The
  default stays `measured`.
- `22084a3` makes the learner log transition-error diagnostics every 50 model updates (`Diag/*` keys
  in WandB). They run under `no_grad`, restore the RNG state, and don't change training. The export
  script now pulls these keys too.

Jobs already running are unaffected. Any job that starts after the pull gets both changes.

1. Pull the branch on the cluster:
   ```bash
   cd ~/workspace/private-mamba && git pull
   ```
2. Launch the new variant from your machine, on the same branch:
   ```bash
   python sbatch_scripts/submit_experiments.py --envs 8m --cost_limits 4.0 --seeds 1 2 3 --laglr 1e-5 --lag_signal imagined --max_steps 105000
   ```
   Run names end in `_imag_..._feat-aamas`, so the `smac_8m_new` export picks them up unchanged.
3. About 10 minutes after the jobs start:
   - `Lag/mean_cost` in the imagined runs is small (on the order of the imagined per-step cost, well
     below 4), not an episode cost;
   - `Diag/tv_post_prior` and `Diag/bv_signed` appear in WandB, and the run hasn't crashed.
4. If any 8m jobs from the first batch are still queued (not yet running), they'll also log the
   diagnostics once they start. That's fine and expected.
