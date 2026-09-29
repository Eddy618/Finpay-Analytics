from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


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
# ANALYTICS ENDPOINT TESTS
# ============================================================

def test_kpis():
    response = client.get("/kpis")

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


def test_transactions():
    response = client.get(
        "/transactions?limit=10"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) <= 10


def test_transactions_status_filter():
    response = client.get(
        "/transactions?limit=10&status=Failed"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    for transaction in data:
        assert transaction["transaction_status"] == "Failed"


def test_anomalies():
    response = client.get(
        "/anomalies?limit=10"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


def test_reconciliation():
    response = client.get(
        "/reconciliation?limit=10"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


def test_channels():
    response = client.get("/channels")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    if data:
        assert "channel_name" in data[0]
        assert "total_transactions" in data[0]
        assert "success_rate" in data[0]


def test_partners():
    response = client.get("/partners")

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
    assert "/kpis" in data["paths"]
    assert "/payments/initialize" in data["paths"]