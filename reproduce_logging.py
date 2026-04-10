import random
import time

import wandb


def reproduce():
    wandb.init(project="private-mamba", entity="raz-shmueli-corsound-ai", name="reproduce_logging_test")

    # Matching DreamerRunner metrics
    wandb.define_metric("steps")
    wandb.define_metric("main/winrate", step_metric="steps")
    wandb.define_metric("main/cost", step_metric="steps")
    wandb.define_metric("main/score", step_metric="steps")

    for i in range(10):
        steps = i * 1000
        # Simulated metrics
        reward = random.uniform(0, 1)
        cost = random.uniform(100, 500)  # Similar scale to Swimmer
        score = random.uniform(10, 20)

        print(f"Logging: Step {steps}, Reward {reward}, Cost {cost}, Score {score}")

        # Exact logging style of DreamerRunner
        wandb.log({"main/winrate": reward, "steps": steps})
        wandb.log({"main/cost": cost, "steps": steps})
        wandb.log({"main/score": score, "steps": steps})

        time.sleep(1)

    # Special test: Log a dict by mistake?
    # wandb.log({"main/cost": {"0": 1.0, "1": 1.5}, "steps": steps + 100})

    wandb.finish()


if __name__ == "__main__":
    reproduce()
