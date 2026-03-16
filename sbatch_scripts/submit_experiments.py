import argparse
import os
import subprocess


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
    parser.add_argument("--dry_run", action="store_true", help="Just generate files, don't submit")

    args = parser.parse_args()

    template_path = "sbatch_scripts/template.sbatch"

    if not os.path.exists("sbatch_scripts/generated"):
        os.makedirs("sbatch_scripts/generated")

    for env_name in args.envs:
        for cost_limit in args.cost_limits:
            for seed in args.seeds:
                job_name = f"{args.env_type}_{env_name}_lim{cost_limit}_seed{seed}"
                sbatch_filename = f"sbatch_scripts/generated/{job_name}.sbatch"

                params = {
                    "JOB_NAME": job_name,
                    "ENV": args.env_type,
                    "ENV_NAME": env_name,
                    "COST_TYPE": args.cost_type,
                    "COST_LIMIT": cost_limit,
                    "SEED": seed,
                    "N_WORKERS": args.n_workers,
                }

                create_sbatch_file(template_path, sbatch_filename, params)

                if args.dry_run:
                    print(f"[DRY-RUN] Generated {sbatch_filename}")
                else:
                    remote_path = f"workspace/private-mamba/{sbatch_filename}"
                    print(f"Submitting {job_name} to cluster...")

                    # 1. Copy the generated sbatch to the remote
                    scp_cmd = ["scp", sbatch_filename, f"razshmue@slurm.bgu.ac.il:{remote_path}"]
                    subprocess.run(scp_cmd, check=True)

                    # 2. Submit the sbatch on the remote
                    ssh_cmd = [
                        "ssh",
                        "razshmue@slurm.bgu.ac.il",
                        f"cd workspace/private-mamba && sbatch {sbatch_filename}",
                    ]
                    subprocess.run(ssh_cmd, check=True)


if __name__ == "__main__":
    main()
