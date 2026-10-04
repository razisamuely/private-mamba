import argparse
import csv
import importlib.util
import os
import subprocess
from datetime import datetime

_spec = importlib.util.spec_from_file_location(
    "cluster_config", os.path.join(os.path.dirname(__file__), "cluster_config.py")
)
_cfg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cfg)
REMOTE_USER, REMOTE_HOST, MAIL_USER, REMOTE_HOME = (
    _cfg.REMOTE_USER,
    _cfg.REMOTE_HOST,
    _cfg.MAIL_USER,
    _cfg.REMOTE_HOME,
)


def create_sbatch_file(template_path, output_path, params):
    with open(template_path) as f:
        content = f.read()

    for key, value in params.items():
        content = content.replace(f"{{{{{key}}}}}", str(value))

    with open(output_path, "w") as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(description="Submit multiple seeds/envs to Slurm")
    parser.add_argument("--envs", type=str, nargs="+", default=["3m"], help="List of environment names (e.g. 3m 8m)")
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3], help="List of seeds")
    parser.add_argument("--cost_limits", type=float, nargs="+", default=[0.0], help="List of cost limits")
    parser.add_argument(
        "--env_type", type=str, default="starcraft", help="Environment type (starcraft, safety_gym, etc.)"
    )
    parser.add_argument("--cost_type", type=str, default="dead_allies_incremental", help="Cost function type")
    parser.add_argument("--laglr", type=float, default=0.00001, help="Lagrangian learning rate")
    parser.add_argument("--n_workers", type=int, default=4, help="Number of workers per job")
    parser.add_argument("--algo_name", type=str, default="safedreamer", help="Algorithm name (e.g. safedreamer)")
    parser.add_argument("--dry_run", action="store_true", help="Just generate files, don't submit")
    # Continuous action overrides (passed as EXTRA_ARGS to train.py)
    parser.add_argument("--actor_lr", type=float, default=None)
    parser.add_argument("--model_lr", type=float, default=None)
    parser.add_argument("--value_lr", type=float, default=None)
    parser.add_argument("--grad_clip", type=float, default=None)
    parser.add_argument("--grad_clip_policy", type=float, default=None)
    parser.add_argument("--ppo_epochs", type=int, default=None)
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--comm_mode", type=str, default=None, help="Communication mode (full/none)")
    parser.add_argument("--lag_mode", type=str, default=None, help="Lagrangian update rule (basic/pid)")
    parser.add_argument("--pid_kp", type=float, default=None, help="PID-Lagrangian proportional gain")
    parser.add_argument("--pid_ki", type=float, default=None, help="PID-Lagrangian integral gain")
    parser.add_argument("--pid_kd", type=float, default=None, help="PID-Lagrangian derivative gain")
    parser.add_argument("--lag_init", type=float, default=None, help="Initial multiplier; fixed with --laglr 0")
    parser.add_argument("--max_steps", type=int, default=None, help="Stop each run after this many env steps")
    parser.add_argument("--template", type=str, default=None, help="Custom sbatch template path")

    args = parser.parse_args()

    template_path = args.template if args.template else "sbatch_scripts/template.sbatch"
    log_dir = "sbatch_scripts/logs"
    history_file = os.path.join(log_dir, "experiments_history.csv")

    if not os.path.exists("sbatch_scripts/generated"):
        os.makedirs("sbatch_scripts/generated")

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # CSV Header if file doesn't exist
    if not os.path.exists(history_file):
        with open(history_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Algo", "Env", "Map", "CostLimit", "Seed", "JobID", "RunName", "Branch"])

    timestamp_str = datetime.now().strftime("date%m-%d-hr%H-%M-%S")

    # Get current branch
    try:
        current_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode().strip()
        current_branch = current_branch.replace("/", "-")
    except Exception:
        current_branch = "unknown"

    # Build extra CLI args for train.py
    extra_parts = []
    if args.actor_lr is not None:
        extra_parts.append(f"--actor_lr {args.actor_lr}")
    if args.model_lr is not None:
        extra_parts.append(f"--model_lr {args.model_lr}")
    if args.value_lr is not None:
        extra_parts.append(f"--value_lr {args.value_lr}")
    if args.grad_clip is not None:
        extra_parts.append(f"--grad_clip {args.grad_clip}")
    if args.grad_clip_policy is not None:
        extra_parts.append(f"--grad_clip_policy {args.grad_clip_policy}")
    if args.ppo_epochs is not None:
        extra_parts.append(f"--ppo_epochs {args.ppo_epochs}")
    if args.epochs is not None:
        extra_parts.append(f"--epochs {args.epochs}")
    if args.comm_mode is not None:
        extra_parts.append(f"--comm_mode {args.comm_mode}")
    if args.lag_mode is not None:
        extra_parts.append(f"--lag_mode {args.lag_mode}")
    if args.pid_kp is not None:
        extra_parts.append(f"--pid_kp {args.pid_kp}")
    if args.pid_ki is not None:
        extra_parts.append(f"--pid_ki {args.pid_ki}")
    if args.pid_kd is not None:
        extra_parts.append(f"--pid_kd {args.pid_kd}")
    if args.lag_init is not None:
        extra_parts.append(f"--lag_init {args.lag_init}")
    if args.max_steps is not None:
        extra_parts.append(f"--max_steps {args.max_steps}")
    extra_args = " \\\n    ".join(extra_parts) if extra_parts else ""

    for env_name in args.envs:
        for cost_limit in args.cost_limits:
            for seed in args.seeds:
                # Structured Run Name (Used for file and logging)
                # safedreamer_{costtype}_{env}_{costlim}_{map}_{seed}_{time}
                arm_suffix = (f"_{args.lag_mode}" if args.lag_mode else "") + (
                    f"_init{args.lag_init}" if args.lag_init is not None else ""
                )
                run_identifier = f"{args.algo_name}_{args.cost_type}_{args.env_type}_lag{args.laglr}_{cost_limit}_{env_name}_s{seed}{arm_suffix}_{timestamp_str}"
                sbatch_filename = f"sbatch_scripts/generated/{run_identifier}.sbatch"

                params = {
                    "MAIL_USER": MAIL_USER,
                    "REMOTE_HOME": REMOTE_HOME,
                    "JOB_NAME": run_identifier,
                    "ENV": args.env_type,
                    "ENV_NAME": env_name,
                    "COST_TYPE": args.cost_type,
                    "COST_LIMIT": cost_limit,
                    "SEED": seed,
                    "N_WORKERS": args.n_workers,
                    "ALGO": args.algo_name,
                    "LAGRANGIAN_LR": args.laglr,
                    "BRANCH_NAME": current_branch,
                    "EXTRA_ARGS": extra_args,
                }

                create_sbatch_file(template_path, sbatch_filename, params)

                if args.dry_run:
                    print(f"[DRY-RUN] Generated {sbatch_filename}")
                else:
                    remote_path = f"workspace/private-mamba/{sbatch_filename}"
                    print(f"Submitting {run_identifier} to cluster...")

                    # 1. Copy the generated sbatch to the remote
                    scp_cmd = ["scp", sbatch_filename, f"{REMOTE_USER}@{REMOTE_HOST}:{remote_path}"]
                    subprocess.run(scp_cmd, check=True)

                    # 2. Submit the sbatch on the remote and capture JobID
                    ssh_cmd = [
                        "ssh",
                        f"{REMOTE_USER}@{REMOTE_HOST}",
                        f"cd workspace/private-mamba && sbatch {sbatch_filename}",
                    ]
                    result = subprocess.run(ssh_cmd, check=True, capture_output=True, text=True)

                    # Output example: "Submitted batch job 1234567"
                    job_id = result.stdout.strip().split()[-1] if result.stdout else "unknown"
                    print(f"Job submitted! Slurm ID: {job_id}")

                    # 3. Log to local CSV
                    with open(history_file, "a", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow(
                            [
                                timestamp_str,
                                args.algo_name,
                                args.env_type,
                                env_name,
                                cost_limit,
                                seed,
                                job_id,
                                run_identifier,
                                current_branch,
                            ]
                        )


if __name__ == "__main__":
    main()
