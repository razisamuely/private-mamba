import argparse
import subprocess


def main():
    parser = argparse.ArgumentParser(description="List running experiments on the Slurm cluster")
    parser.add_argument("--user", type=str, default="razshmue", help="Slurm user name")
    args = parser.parse_args()

    remote_user = "razshmue"
    remote_host = "slurm.bgu.ac.il"

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
