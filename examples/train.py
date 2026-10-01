"""
Train a small PyTorch model on the "transaction_training" dataset.

Labels the largest 5% of transactions (by absolute amount) as anomalies and
trains a two-layer classifier that outputs an anomaly probability from 0 to 1,
saving an ONNX checkpoint after each epoch. When the run finishes, the latest
checkpoint is registered as a new "transaction-anomaly" model version.

Run with:
    python examples/train.py
"""

from __future__ import annotations

from dataclasses import dataclass

from chalk.client import ChalkClient
from chalkcompute import Image

# Not `from chalkcompute import training`: inside the training container that
# name resolves to the chalkcompute.training package, not the decorator
from chalkcompute._training import training

MODEL_NAME = "transaction-anomaly"

FEATURES = [
    "transaction.amount",
    "transaction.processing_fee",
    "transaction.is_small",
    "transaction.is_night",
]


@dataclass
class Config:
    lr: float = 1e-3
    epochs: int = 5
    batch_size: int = 32
    hidden_dim: int = 64


@training(
    data="transaction_training",
    name="transaction-anomaly",
    image=Image.debian_slim("3.12").pip_install(
        [
            "chalkcompute==2.11.10",
            "chalkpy[runtime,training]==2.157.22",
            "torch",
            "onnx",
            "polars",
        ]
    ),
    cpu="4",
    memory="8Gi",
)
def train(df, config: Config):
    import io

    import onnx
    import torch
    import torch.nn as nn
    from chalk.client.serialization.model_serialization import MODEL_SERIALIZERS
    from chalk.ml.chalk_train import checkpoint, log_metrics
    from chalk.ml.utils import ModelType

    # chalkpy can't infer a schema for ONNX models, and checkpoint() fails
    # with "Invalid empty schema" without one, so declare it here
    MODEL_SERIALIZERS[ModelType.ONNX] = MODEL_SERIALIZERS[ModelType.ONNX]._replace(
        schema_fn=lambda _: ({f: float for f in FEATURES}, {"anomaly_score": float})
    )

    if hasattr(df, "collect"):
        df = df.collect()
    print(f"dataset: {len(df)} rows")

    X = torch.tensor(
        df.select(FEATURES).drop_nulls().cast(float).to_numpy(), dtype=torch.float32
    )
    # Anomaly = top 5% by size, counting large outflows (negative amounts) too
    sizes = X[:, 0].abs()
    y = (sizes > torch.quantile(sizes, 0.95)).float()
    print(f"training on {len(X)} rows, {int(y.sum())} anomalies")

    split = int(len(X) * 0.8)
    perm = torch.randperm(len(X), generator=torch.Generator().manual_seed(42))
    X_train, y_train = X[perm[:split]], y[perm[:split]]
    X_test, y_test = X[perm[split:]], y[perm[split:]]

    model = nn.Sequential(
        nn.Linear(len(FEATURES), config.hidden_dim),
        nn.ReLU(),
        nn.Linear(config.hidden_dim, 1),
        nn.Sigmoid(),  # probability the transaction is an anomaly, 0 to 1
        nn.Flatten(0),  # one score per transaction
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=config.lr)
    loss_fn = nn.BCELoss()

    def to_onnx(model):
        # Checkpoint as ONNX rather than the raw nn.Module: chalk saves PyTorch
        # modules as weights-only safetensors, which the inferred serving image
        # can't load. ONNX is served directly by onnxruntime.
        buf = io.BytesIO()
        torch.onnx.export(
            model,
            (X[:1],),
            buf,
            input_names=["features"],
            output_names=["anomaly_score"],
            dynamic_axes={"features": {0: "batch"}, "anomaly_score": {0: "batch"}},
            dynamo=False,
        )
        return onnx.load_from_string(buf.getvalue())

    for epoch in range(config.epochs):
        model.train()
        total_loss = 0.0
        for i in range(0, len(X_train), config.batch_size):
            xb = X_train[i : i + config.batch_size]
            yb = y_train[i : i + config.batch_size]
            optimizer.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(xb)
        avg_loss = total_loss / len(X_train)

        model.eval()
        with torch.no_grad():
            accuracy = ((model(X_test) > 0.5) == y_test).float().mean().item()

        print(
            f"epoch {epoch + 1}/{config.epochs}: loss={avg_loss:.4f}, accuracy={accuracy:.4f}"
        )
        log_metrics({"loss": avg_loss}, tags={"split": "train", "epoch": str(epoch)})
        log_metrics({"accuracy": accuracy}, tags={"split": "test", "epoch": str(epoch)})
        checkpoint(
            to_onnx(model),
            metadata={"epoch": epoch, "loss": avg_loss, "accuracy": accuracy},
        )

    return model


def main():
    config = Config()
    print(f"submitting training run with {config}")
    handle = train.run_training(config=config)
    print(f"run_id: {handle.run_id}")

    print("waiting for completion...")
    handle.wait(timeout=600)
    print("completed")

    ckpt = handle.latest_checkpoint()
    print(f"latest checkpoint: {ckpt.path if ckpt else 'none'}")

    client = ChalkClient()
    print(f"registering model namespace {MODEL_NAME}...")
    try:
        client.register_model_namespace(
            name=MODEL_NAME,
            description="Probability that a transaction is an anomaly",
        )
    except Exception as e:
        print(f"skipping, namespace may already exist: {e}")

    print("registering latest checkpoint in the model registry...")
    version = client.promote_model_artifact(
        name=MODEL_NAME,
        run_id=handle.run_id,
        aliases=["latest"],
        # Serve the ONNX checkpoint with onnxruntime; no torch needed at inference
        dependencies=["onnxruntime"],
    )
    print(f"registered {MODEL_NAME} version {version.model_version}")


if __name__ == "__main__":
    main()
