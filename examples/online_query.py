#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["chalkpy[all]"]
# ///
#
# Queries fraud detection features for a user.
#
# Usage:
#   uv run online_query.py 1

import sys

from chalk.client import ChalkClient

user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
client = ChalkClient()

result = client.query(
    input={"user.id": user_id},
    output=[
        "user.name",
        "user.email",
        "user.denylisted",
        "user.risk_score",
        "user.risk_category",
        "user.email_domain",
        "user.email_age_days",
        "user.name_email_match_score",
        "user.txn_count",
        "user.avg_txn_amount",
        "user.night_txn_ratio",
        "user.ach_return_ratio",
        "user.account_age_days",
        "user.credit_report.score",
        "user.credit_report.total_balance",
        "user.credit_report.percent_past_due",
    ],
)

print(f"Fraud signals for user {user_id}:")
for feat in result.data:
    print(f"  {feat.field}: {feat.value}")
