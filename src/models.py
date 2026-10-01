from datetime import datetime

import chalk.functions as F
from chalk import DataFrame, FeatureTime, Windowed, _, feature, windowed
from chalk.features import features


@features
class Transaction:
    id: int
    # Transaction amount in USD (negative for outflows)
    amount: float
    # Spending category (e.g. "transfer", "retail")
    category: str
    # Creation timestamp for time-of-day expressions
    created_at: datetime
    # Debit or credit direction
    direction: str
    # Merchant name
    merchant: str
    # Transaction status (e.g. "COMPLETED", "RETURNED")
    status: str

    # Foreign key to User
    user_id: "User.id"
    # Parent user relationship
    user: "User"

    # Observation timestamp for temporal consistency
    at: FeatureTime

    # Computed expressions
    # Whether the transaction amount is under $5
    is_small: bool = _.amount < 5.0
    # Whether the transaction occurred between midnight and 6 AM
    is_night: bool = F.hour_of_day(_.created_at) < 6

    # NEW computed feature from Python resolver
    # Processing fee calculated from transaction amount
    processing_fee: float

    # Model inference (deployed by examples/deploy_model.py)
    # Probability (0 to 1) that the transaction is an anomaly
    # Inputs must match FEATURES order in examples/train.py. Bools are cast to
    # floats because the model server can't convert boolean columns.
    anomaly_score: float = F.catalog_call(
        "model.transaction-anomaly",
        _.amount,
        _.processing_fee,
        F.cast(_.is_small, float),
        F.cast(_.is_night, float),
    )


@features
class CreditReport:
    id: int
    # Count of tradelines on the report
    num_tradelines: int
    # Fraction of total amount that is past due
    percent_past_due: float
    # Bureau credit score
    score: int = feature(min=300, max=850, strict=True)
    # Sum of all tradeline balances
    total_balance: float

    # Foreign key to User
    user_id: "User.id"
    # Parent user relationship
    user: "User"


@features
class User:
    id: int
    # Account creation timestamp
    created_at: datetime
    # Whether email appears in a known-bad list
    denylisted: bool
    # Account email address
    email: str
    # Age of the email address in days
    email_age_days: int
    # Ground-truth fraud label or rules-based prediction
    is_fraud: bool
    # Full legal name
    name: str
    # Fuzzy match score between name and email username
    name_email_match_score: float
    # ML model output score for fraud likelihood
    risk_score: float

    # Relationships
    # Credit report for this user
    credit_report: CreditReport
    # All transactions for this user
    transactions: DataFrame[Transaction]

    # Aggregation expressions
    # Count of ACH-returned transactions
    ach_return_count: int = _.transactions[_.status == "RETURNED"].count()
    # Fraction of transactions that were returned
    ach_return_ratio: float = F.if_then_else(
        _.txn_count > 0, _.ach_return_count / _.txn_count, 0.0
    )
    # Mean transaction amount
    avg_txn_amount: float = _.transactions[_.amount].mean()
    # Count of transactions between midnight and 6 AM
    night_txn_count: int = _.transactions[F.hour_of_day(_.created_at) < 6].count()
    # Fraction of transactions occurring at night
    night_txn_ratio: float = F.if_then_else(
        _.txn_count > 0, _.night_txn_count / _.txn_count, 0.0
    )
    # Total number of transactions
    txn_count: int = _.transactions.count()

    # Windowed aggregation
    # Total spending in rolling windows
    recent_spending: Windowed[float] = windowed(
        "1d",
        "7d",
        "30d",
        expression=_.transactions[
            _.amount,
            _.created_at > _.chalk_window,
            _.created_at < _.chalk_now,
        ].sum(),
    )

    # NEW computed features from Python resolvers
    # Number of days since the account was created
    account_age_days: int
    # Domain portion of email address
    email_domain: str
    # Categorical risk level derived from risk_score
    risk_category: str
