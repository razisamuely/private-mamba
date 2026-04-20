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

## Monitoring & Debugging

```bash
# Job status
ssh razshmue@slurm.bgu.ac.il "squeue -u razshmue"

# Error log
ssh razshmue@slurm.bgu.ac.il "tail -30 workspace/private-mamba/<job_name>-id-<JOBID>.err"

# Output log
ssh razshmue@slurm.bgu.ac.il "tail -30 workspace/private-mamba/<job_name>-id-<JOBID>.out"

# Available GPUs by partition
ssh razshmue@slurm.bgu.ac.il "sinfo -o '%P %G %l' | grep gpu"

# Cancel all jobs
ssh razshmue@slurm.bgu.ac.il "scancel -u razshmue"
```

## GPU Keep-Alive (for CPU-heavy jobs)

**Problem**: SLURM cancels jobs after 4 hours of GPU idle. CPU-heavy training (e.g. MACPO with SC2 simulation) triggers false positives.

**Solution**: Background script that stresses GPU every 60 minutes for 10 seconds.

**Locations**:
- `/home/corsound/workspace/overleaf/scripts/gpu_keepalive.py`
- `/home/corsound/workspace/Safe-Policy-Optimization/sbatch_scripts/gpu_keepalive.py`

**Usage** (add to sbatch before training):
```bash
python scripts/gpu_keepalive.py > gpu_keepalive.log 2>&1 &
KEEPALIVE_PID=$!
trap "kill $KEEPALIVE_PID 2>/dev/null" EXIT
```

## Gotchas
- Wall time: check maintenance windows — set `--time` to fit before downtime
- GPU limit: max 7 GPUs per user (`QOSMaxGRESPerUser`) — excess jobs queue automatically
- SSH rate limiting: use `ControlMaster auto` + `ControlPersist 10m` in `~/.ssh/config`
- Always use `./venv310/bin/python3`, not system python
- Check queue: `ssh razshmue@slurm.bgu.ac.il "squeue -u razshmue"`
