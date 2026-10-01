import pytest
from chalk.client import ChalkClient

from src.models import CreditReport, Transaction, User


@pytest.fixture
def chalk_client():
    return ChalkClient()


def test_user_query(chalk_client: ChalkClient):
    """Test querying basic user features."""
    chalk_client.check(
        input={User.id: 1},
        assertions={
            User.email: "alice@example.com",
            User.name: "Alice Johnson",
        },
    )


def test_user_email_domain(chalk_client: ChalkClient):
    """Test computed email domain feature."""
    chalk_client.check(
        input={User.id: 1},
        assertions={
            User.email_domain: "example.com",
        },
    )


def test_user_risk_category(chalk_client: ChalkClient):
    """Test computed risk category from risk score."""
    chalk_client.check(
        input={User.id: 1},
        assertions={
            User.risk_category: "low",
        },
    )


def test_user_transaction_aggregates(chalk_client: ChalkClient):
    """Test transaction aggregate features on user."""
    chalk_client.check(
        input={User.id: 1},
        assertions={
            User.txn_count: 10,
            User.avg_txn_amount: 150.0,
        },
    )


def test_transaction_query(chalk_client: ChalkClient):
    """Test querying transaction features."""
    chalk_client.check(
        input={Transaction.id: 1},
        assertions={
            Transaction.amount: 100.0,
            Transaction.status: "COMPLETED",
        },
    )


def test_transaction_processing_fee(chalk_client: ChalkClient):
    """Test computed processing fee on transaction."""
    chalk_client.check(
        input={Transaction.id: 1},
        assertions={
            Transaction.processing_fee: 2.9,
        },
    )


def test_credit_report_query(chalk_client: ChalkClient):
    """Test querying credit report features."""
    chalk_client.check(
        input={CreditReport.id: 1},
        assertions={
            CreditReport.score: 720,
            CreditReport.num_tradelines: 5,
        },
    )


def test_user_credit_report_relationship(chalk_client: ChalkClient):
    """Test has-one relationship from user to credit report."""
    chalk_client.check(
        input={User.id: 1},
        assertions={
            User.credit_report.score: 720,
        },
    )
