# Cluster Submission Skill

## Steps

1. **Pull on cluster**
   ```bash
   ssh razshmue@slurm.bgu.ac.il "cd workspace/private-mamba && git checkout <branch> && git pull origin <branch>"
   ```

2. **Submit jobs**
   ```bash
   ./venv310/bin/python3 sbatch_scripts/submit_experiments.py \
       --envs <map> \
       --seeds 1 2 3 \
       --cost_limits <limits> \
       --env_type starcraft \
       --cost_type collision \
       --laglr 0.00001 \
       --cost_priority 0.15 \
       --algo_name safedreamer
   ```

3. **Update `runs.md`** with returned Slurm IDs

4. **Commit & push**
   ```bash
   git add -A && git commit -m "docs: add submitted runs" && git push origin <branch>
   ```

## Gotchas
- Wall time: check maintenance windows — set `--time` to fit before downtime
- GPU limit: max 7 GPUs per user (`QOSMaxGRESPerUser`) — excess jobs queue automatically
- SSH rate limiting: use `ControlMaster auto` + `ControlPersist 10m` in `~/.ssh/config`
- Always use `./venv310/bin/python3`, not system python
- Check queue: `ssh razshmue@slurm.bgu.ac.il "squeue -u razshmue"`
