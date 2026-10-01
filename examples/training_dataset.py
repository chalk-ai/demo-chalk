"""
Create the "transaction_training" dataset for transaction model training.

Run with:
    uv run python examples/training_dataset.py

This runs an offline query that pulls transactions from Postgres (via the
postgres source) and saves the result as a named dataset "transaction_training".

Training code can reference it with data="transaction_training".
"""

from __future__ import annotations

import sys
from pathlib import Path

from chalk.client import ChalkClient

# Make the repo root importable so `src` resolves when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import Transaction  # noqa: E402

DATASETS_URL = (
    "https://chalk.ai/projects/demofytgpusgt/environments/demo46428d94/datasets"
)


def main():
    client = ChalkClient()

    print("=== Creating transaction_training dataset ===")
    print()
    output = [
        Transaction.id,
        Transaction.user_id,
        Transaction.amount,
        Transaction.category,
        Transaction.direction,
        Transaction.merchant,
        Transaction.status,
        Transaction.created_at,
        Transaction.is_small,
        Transaction.is_night,
        Transaction.processing_fee,
        Transaction.at,
    ]
    print("output features:")
    for f in output:
        print(f"  {f}")
    print()

    print("submitting offline query...")
    dataset = client.offline_query(
        output=output,
        dataset_name="transaction_training",
        max_samples=5000,
        recompute_features=True,
        store_offline=False,
        store_online=False,
        wait=True,
        run_asynchronously=False,
        show_progress=True,
    )

    print()
    print(f"dataset id:    {dataset.dataset_id}")
    print()

    try:
        df = dataset.get_data_as_polars().collect()
        print(f"rows:          {len(df)}")
        print()
        print(df.head(10))
    except Exception as e:
        print(f"could not fetch data preview: {e}")

    print()
    print(f"url:           {DATASETS_URL}/{dataset.dataset_id}")
    print()
    print("=== done ===")
    print('dataset_name="transaction_training" is ready for training')


if __name__ == "__main__":
    main()
