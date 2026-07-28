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
    parser = argparse.ArgumentParser(description="List running experiments on the Slurm cluster")
    parser.add_argument("--user", type=str, default=REMOTE_USER, help="Slurm user name")
    args = parser.parse_args()

    remote_user = REMOTE_USER
    remote_host = REMOTE_HOST

    print(f"Fetching running experiments for user {args.user}...")

    ssh_cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=5",
        f"{remote_user}@{remote_host}",
        f"squeue -u {args.user} -o '%.10i %.10P %.30j %.10u %.2t %.10M %.10D %R'",
    ]

    try:
        result = subprocess.run(ssh_cmd, check=True, capture_output=True, text=True)
        print("\n" + result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching experiments: {e.stderr}")


if __name__ == "__main__":
    main()
