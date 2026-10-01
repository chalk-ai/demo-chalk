from src.resolvers.resolvers import calculate_processing_fee, get_email_domain


def test_email_domain_extraction():
    """Test that domain is correctly extracted from email."""
    assert get_email_domain("alice@example.com") == "example.com"


def test_email_domain_gmail():
    """Test domain extraction for Gmail addresses."""
    assert get_email_domain("user@gmail.com") == "gmail.com"


def test_email_domain_empty():
    """Test domain extraction returns empty string for empty input."""
    assert get_email_domain("") == ""


def test_processing_fee_minimum():
    """Test that processing fee has a $0.50 minimum."""
    assert calculate_processing_fee(1.00) == 0.50


def test_processing_fee_percentage():
    """Test that processing fee is 2.9% for larger amounts."""
    fee = calculate_processing_fee(100.00)
    assert fee == 2.9


def test_processing_fee_negative_amount():
    """Test that processing fee uses absolute value of amount."""
    fee = calculate_processing_fee(-100.00)
    assert fee == 2.9
