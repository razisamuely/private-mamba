import argparse
import csv
import os
import subprocess
from datetime import datetime


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
    parser.add_argument("--n_workers", type=int, default=4, help="Number of workers per job")
    parser.add_argument("--algo_name", type=str, default="safedreamer", help="Algorithm name (e.g. safedreamer)")
    parser.add_argument("--dry_run", action="store_true", help="Just generate files, don't submit")

    args = parser.parse_args()

    template_path = "sbatch_scripts/template.sbatch"
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

    for env_name in args.envs:
        for cost_limit in args.cost_limits:
            for seed in args.seeds:
                # Structured Run Name (Used for file and logging)
                # safedreamer_{costtype}_{env}_{costlim}_{map}_{seed}_{time}
                run_identifier = (
                    f"{args.algo_name}_{args.cost_type}_{args.env_type}_{cost_limit}_{env_name}_s{seed}_{timestamp_str}"
                )
                sbatch_filename = f"sbatch_scripts/generated/{run_identifier}.sbatch"

                params = {
                    "JOB_NAME": run_identifier,
                    "ENV": args.env_type,
                    "ENV_NAME": env_name,
                    "COST_TYPE": args.cost_type,
                    "COST_LIMIT": cost_limit,
                    "SEED": seed,
                    "N_WORKERS": args.n_workers,
                    "ALGO": args.algo_name,
                    "BRANCH_NAME": current_branch,
                }

                create_sbatch_file(template_path, sbatch_filename, params)

                if args.dry_run:
                    print(f"[DRY-RUN] Generated {sbatch_filename}")
                else:
                    remote_path = f"workspace/private-mamba/{sbatch_filename}"
                    print(f"Submitting {run_identifier} to cluster...")

                    # 1. Copy the generated sbatch to the remote
                    scp_cmd = ["scp", sbatch_filename, f"razshmue@slurm.bgu.ac.il:{remote_path}"]
                    subprocess.run(scp_cmd, check=True)

                    # 2. Submit the sbatch on the remote and capture JobID
                    ssh_cmd = [
                        "ssh",
                        "razshmue@slurm.bgu.ac.il",
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
