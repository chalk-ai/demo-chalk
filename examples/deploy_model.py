"""
Deploy the latest "transaction-anomaly" model version to a scaling group.

Looks up the newest version of the "transaction-anomaly" model in the model
registry and deploys it to the "transaction-anomaly" scaling group. Once
deployed, Transaction.anomaly_score (src/models.py) calls it with
F.catalog_call("model.transaction-anomaly", ...).

Run with:
    python examples/deploy_model.py

Then deploy the feature that calls the model:
    chalk apply
"""

from __future__ import annotations

from chalk.client import ChalkClient
from chalk.scalinggroup import AutoScalingSpec, ScalingGroupResourceRequest

MODEL_NAME = "transaction-anomaly"
SCALING_GROUP = "transaction-anomaly"


def main():
    client = ChalkClient()

    print(f"looking up latest {MODEL_NAME} version in the model registry...")
    model = client.get_model_version(MODEL_NAME)
    print(f"model version: {model.version}")

    print(f"deploying to scaling group {SCALING_GROUP}...")
    client.deploy_model_version_to_scaling_group(
        name=SCALING_GROUP,
        model_name=MODEL_NAME,
        model_version=model.version,
        scaling=AutoScalingSpec(min_replicas=1, max_replicas=1),
        resources=ScalingGroupResourceRequest(cpu="1", memory="2Gi"),
    )
    print("deployment submitted")
    print(f'call it with F.catalog_call("model.{SCALING_GROUP}", ...)')


if __name__ == "__main__":
    main()
