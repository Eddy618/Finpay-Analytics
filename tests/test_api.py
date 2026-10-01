import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from api.main import app


# Load local environment variables from .env
load_dotenv()


client = TestClient(app)


# ============================================================
# AUTHENTICATION FIXTURE
# ============================================================

@pytest.fixture(scope="session")
def auth_headers():
    """
    Log in once for the test session and return
    the Bearer authorization header.
    """

    username = os.getenv("TEST_USERNAME")
    password = os.getenv("TEST_PASSWORD")

    assert username, (
        "TEST_USERNAME is missing from .env"
    )

    assert password, (
        "TEST_PASSWORD is missing from .env"
    )

    response = client.post(
        "/auth/login",
        json={
            "username": username,
            "password": password,
        },
    )

    assert response.status_code == 200, (
        f"Login failed: {response.text}"
    )

    data = response.json()

    assert "access_token" in data
    assert data["token_type"].lower() == "bearer"

    token = data["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


# ============================================================
# BASIC APPLICATION TESTS
# ============================================================

def test_root():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["application"] == "FinPay Analytics API"
    assert data["status"] == "running"


def test_health():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert data["database"] == "connected"


# ============================================================
# AUTHENTICATION TESTS
# ============================================================

def test_login():
    username = os.getenv("TEST_USERNAME")
    password = os.getenv("TEST_PASSWORD")

    assert username, (
        "TEST_USERNAME is missing from .env"
    )

    assert password, (
        "TEST_PASSWORD is missing from .env"
    )

    response = client.post(
        "/auth/login",
        json={
            "username": username,
            "password": password,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"].lower() == "bearer"
    assert "expires_in_minutes" in data
    assert data["username"] == username
    assert "role" in data


def test_kpis_requires_authentication():
    response = client.get("/kpis")

    assert response.status_code == 401


# ============================================================
# ANALYTICS ENDPOINT TESTS
# ============================================================

def test_kpis(auth_headers):
    response = client.get(
        "/kpis",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    required_fields = [
        "total_transactions",
        "successful_transactions",
        "failed_transactions",
        "pending_transactions",
        "refunded_transactions",
        "total_transaction_value",
        "successful_transaction_value",
        "average_transaction_value",
        "success_rate",
    ]

    for field in required_fields:
        assert field in data


def test_transactions(auth_headers):
    response = client.get(
        "/transactions?limit=10",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) <= 10


def test_transactions_status_filter(auth_headers):
    response = client.get(
        "/transactions?limit=10&status=Failed",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    for transaction in data:
        assert transaction["transaction_status"] == "Failed"


def test_anomalies(auth_headers):
    response = client.get(
        "/anomalies?limit=10",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


def test_reconciliation(auth_headers):
    response = client.get(
        "/reconciliation?limit=10",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


def test_channels(auth_headers):
    response = client.get(
        "/channels",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    if data:
        assert "channel_name" in data[0]
        assert "total_transactions" in data[0]
        assert "success_rate" in data[0]


def test_partners(auth_headers):
    response = client.get(
        "/partners",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    if data:
        assert "partner_name" in data[0]
        assert "total_transactions" in data[0]
        assert "success_rate" in data[0]


# ============================================================
# PAYMENT ENDPOINT TESTS
# ============================================================

def test_payment_history():
    response = client.get(
        "/payments/history?limit=10"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


def test_payment_analytics():
    response = client.get(
        "/payments/analytics"
    )

    assert response.status_code == 200

    data = response.json()

    required_fields = [
        "total_payment_attempts",
        "successful_payments",
        "failed_payments",
        "pending_payments",
        "abandoned_payments",
        "total_payment_value",
        "successful_payment_value",
        "average_payment_value",
        "payment_success_rate",
    ]

    for field in required_fields:
        assert field in data


def test_payment_daily_analytics():
    response = client.get(
        "/payments/analytics/daily"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


def test_payment_channel_analytics():
    response = client.get(
        "/payments/analytics/channels"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


# ============================================================
# API DOCUMENTATION TEST
# ============================================================

def test_openapi():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    data = response.json()

    assert "openapi" in data
    assert "paths" in data

    assert "/health" in data["paths"]
    assert "/auth/login" in data["paths"]
    assert "/kpis" in data["paths"]
    assert "/payments/initialize" in data["paths"]