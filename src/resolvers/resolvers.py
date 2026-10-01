from chalk import Now, online
from chalk.features import Features

from src.models import Transaction, User


@online
def get_email_domain(email: User.email) -> User.email_domain:
    """Extract domain from email address."""
    return email.split("@")[-1].lower() if email else ""


@online
def get_risk_metrics(
    risk_score: User.risk_score,
    score: User.credit_report.score,
    created_at: User.created_at,
    now: Now,
) -> Features[User.risk_category, User.account_age_days]:
    """Derive categorical risk level and account age from risk score and credit data."""
    age_days = (now - created_at).days

    if risk_score >= 0.7 or score < 500:
        category = "high"
    elif risk_score >= 0.3:
        category = "medium"
    else:
        category = "low"

    return User(
        risk_category=category,
        account_age_days=age_days,
    )


@online
def calculate_processing_fee(amount: Transaction.amount) -> Transaction.processing_fee:
    """Calculate processing fee based on transaction amount."""
    return max(0.50, abs(amount) * 0.029)
