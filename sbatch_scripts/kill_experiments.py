import argparse
import importlib.util
import os
import subprocess

_spec = importlib.util.spec_from_file_location(
    "cluster_config", os.path.join(os.path.dirname(__file__), "cluster_config.py")
)
_cfg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cfg)
REMOTE_USER, REMOTE_HOST = _cfg.REMOTE_USER, _cfg.REMOTE_HOST


def main():
    parser = argparse.ArgumentParser(description="Kill running experiments on the Slurm cluster")
    parser.add_argument("jobs", type=str, nargs="+", help="Specific job IDs to kill, or 'all' to kill all user jobs")
    parser.add_argument("--user", type=str, default=REMOTE_USER, help="Slurm user name")
    args = parser.parse_args()

    remote_user = REMOTE_USER
    remote_host = REMOTE_HOST

    if "all" in args.jobs:
        print(f"Canceling ALL jobs for user {args.user}...")
        scancel_cmd = f"scancel -u {args.user}"
    else:
        job_ids = " ".join(args.jobs)
        print(f"Canceling jobs: {job_ids}...")
        scancel_cmd = f"scancel {job_ids}"

    ssh_cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", f"{remote_user}@{remote_host}", scancel_cmd]

    try:
        subprocess.run(ssh_cmd, check=True)
        print("Success.")
    except subprocess.CalledProcessError as e:
        print(f"Error canceling jobs: {e.stderr}")


if __name__ == "__main__":
    main()
