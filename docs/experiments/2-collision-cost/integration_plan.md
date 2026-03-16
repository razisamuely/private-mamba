# Integration Plan: Collision Cost Experiment (StarCraft)

## 1. Environment Wrapper (`env/starcraft/StarCraft_safe.py`)

### New Method: `get_cost_collision(self, info)`
This method will:
1.  Iterate through all agents.
2.  Filter for alive agents (`health > 0`).
3.  Calculate pairwise Euclidean distance between all alive agents.
4.  Increment a counter if `distance < self.collision_threshold`.
5.  Return the total count.

### Update `get_cost(self, info, terminated=False)`
Add the following branch:
```python
elif self.cost_type == "collision":
    return self.get_cost_collision(info)
```

## 2. Parameter Initialization
Update `__init__` in `StarCraft_safe.py` to accept and store `collision_threshold`.

## 3. Automation Script (`sbatch_scripts/submit_experiments.py`)
No change needed to the script logic, but the `params` grid in `main()` should be updated to include `collision` as a `COST_TYPE`.

## 4. Remote Cluster Sync
Since this change involves the core environment wrapper, a full `git reset --hard origin/feat/issue-2-collision-cost` will be required on the BGU cluster after push.
