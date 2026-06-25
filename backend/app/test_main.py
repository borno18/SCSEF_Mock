import pytest
from fastapi.testclient import TestClient
from backend.app.main import app, derive_department
from backend.app.rules import check_phishing_signals, clean_agent_summary

client = TestClient(app)

def test_health_endpoint():
    """Verify GET /health answers immediately with 200 + {'status': 'ok'}."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_check_phishing_signals():
    """Verify that phishing words and formats trigger check_phishing_signals."""
    # Matches OTP
    assert check_phishing_signals("Please tell me your OTP number immediately") is True
    # Matches PIN
    assert check_phishing_signals("আপনার PIN নাম্বার দিন") is True
    # Matches password
    assert check_phishing_signals("Give me your password") is True
    # Matches is this bkash
    assert check_phishing_signals("bKash ki? target scammer") is True
    # Non-matching support message
    assert check_phishing_signals("Hello, I need help changing my registered email address.") is False

def test_clean_agent_summary():
    """Verify that denylist words or 13-19 digit runs trigger summary cleaning."""
    safe_summary = "Customer has a question regarding failed transaction limits."
    assert clean_agent_summary(safe_summary, "other") == safe_summary

    # Leak containing OTP
    unsafe_summary_otp = "Customer leaked their OTP 12345."
    assert "Customer reports a wrong_transfer issue" in clean_agent_summary(unsafe_summary_otp, "wrong_transfer")

    # Leak containing CVV
    unsafe_summary_cvv = "The CVV is 999."
    assert "Customer reports a refund_request issue" in clean_agent_summary(unsafe_summary_cvv, "refund_request")

    # Leak containing card digits (16 digits)
    unsafe_summary_card = "Customer account card number 4111 2222 3333 4444."
    assert "Customer reports a payment_failed issue" in clean_agent_summary(unsafe_summary_card, "payment_failed")

def test_derive_department():
    """Verify that departments are correctly derived from case type and message context."""
    assert derive_department("wrong_transfer", "I sent BDT 3000 to wrong recipient") == "dispute_resolution"
    assert derive_department("payment_failed", "Balance deducted but payment failed") == "payments_ops"
    assert derive_department("phishing_or_social_engineering", "OTP request") == "fraud_risk"
    
    # Contested refund request
    assert derive_department("refund_request", "I contest this charge, I want a dispute refund!") == "dispute_resolution"
    
    # Non-contested refund request
    assert derive_department("refund_request", "Please refund my transaction, I changed my mind.") == "customer_support"
    
    # Other case
    assert derive_department("other", "App is crashing") == "customer_support"
