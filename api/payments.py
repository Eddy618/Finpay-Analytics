import hashlib
import hmac
import json
import os
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any

import requests
from fastapi import (
    APIRouter,
    Header,
    HTTPException,
    Request,
)
from pydantic import BaseModel, Field
from sqlalchemy import text

from api.database import engine


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


# ============================================================
# CONFIGURATION
# ============================================================

PAYSTACK_BASE_URL = os.getenv(
    "PAYSTACK_BASE_URL",
    "https://api.paystack.co",
)

PAYSTACK_SECRET_KEY = os.getenv(
    "PAYSTACK_SECRET_KEY",
)

PAYSTACK_CALLBACK_URL = os.getenv(
    "PAYSTACK_CALLBACK_URL",
    "http://localhost:8000/payments/callback",
)


# ============================================================
# REQUEST MODEL
# ============================================================

class PaymentInitializeRequest(BaseModel):
    email: str = Field(
        min_length=5,
        max_length=255,
    )

    amount_naira: Decimal = Field(
        gt=Decimal("0"),
    )

    currency: str = Field(
        default="NGN",
        min_length=3,
        max_length=3,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )


# ============================================================
# PAYSTACK HEADERS
# ============================================================

def paystack_headers() -> dict[str, str]:
    """Build Paystack API headers."""

    if not PAYSTACK_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail=(
                "PAYSTACK_SECRET_KEY is not configured."
            ),
        )

    return {
        "Authorization": (
            f"Bearer {PAYSTACK_SECRET_KEY}"
        ),
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (compatible; FinPay-Analytics/1.0; "
            "+https://finpay-analytics-3.onrender.com)"
        ),
    }


# ============================================================
# INITIALIZE PAYMENT
# ============================================================

@router.post("/initialize")
def initialize_payment(
    payment: PaymentInitializeRequest,
):

    try:
        amount_minor_decimal = (
            payment.amount_naira * Decimal("100")
        )

        amount_minor = int(
            amount_minor_decimal
        )

    except (InvalidOperation, ValueError):
        raise HTTPException(
            status_code=400,
            detail="Invalid payment amount.",
        )

    if amount_minor <= 0:
        raise HTTPException(
            status_code=400,
            detail="Payment amount must be greater than zero.",
        )

    currency = payment.currency.upper()

    reference = (
        f"FINPAY-{uuid.uuid4().hex[:20]}"
    )

    metadata = {
        "project": "FinPay Analytics",
        "description": payment.description,
        "customer_email": payment.email,
    }

    payload = {
        "email": payment.email,
        "amount": str(amount_minor),
        "currency": currency,
        "reference": reference,
        "callback_url": PAYSTACK_CALLBACK_URL,
        "metadata": json.dumps(metadata),
    }

    # --------------------------------------------------------
    # Call Paystack
    # --------------------------------------------------------

    try:
        response = requests.post(
            (
                f"{PAYSTACK_BASE_URL}"
                "/transaction/initialize"
            ),
            headers=paystack_headers(),
            json=payload,
            timeout=20,
        )

    except requests.RequestException as error:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Unable to reach Paystack: {error}"
            ),
        )

    if not response.ok:
        raise HTTPException(
            status_code=502,
            detail=(
                "Paystack initialization failed: "
                f"{response.text}"
            ),
        )

    result = response.json()

    if not result.get("status"):
        raise HTTPException(
            status_code=400,
            detail=result.get(
                "message",
                "Paystack rejected the payment.",
            ),
        )

    data = result.get("data", {})

    authorization_url = data.get(
        "authorization_url"
    )

    access_code = data.get(
        "access_code"
    )

    returned_reference = data.get(
        "reference",
        reference,
    )

    if not authorization_url:
        raise HTTPException(
            status_code=502,
            detail=(
                "Paystack did not return "
                "an authorization URL."
            ),
        )

    # --------------------------------------------------------
    # Save payment attempt
    # --------------------------------------------------------

    insert_query = text("""
        INSERT INTO public.payment_transactions (
            reference,
            customer_email,
            amount_minor,
            currency,
            status,
            authorization_url,
            access_code,
            metadata
        )
        VALUES (
            :reference,
            :customer_email,
            :amount_minor,
            :currency,
            :status,
            :authorization_url,
            :access_code,
            CAST(:metadata AS JSONB)
        )
        ON CONFLICT (reference)
        DO NOTHING;
    """)

    with engine.begin() as connection:
        connection.execute(
            insert_query,
            {
                "reference": returned_reference,
                "customer_email": payment.email,
                "amount_minor": amount_minor,
                "currency": currency,
                "status": "initialized",
                "authorization_url": authorization_url,
                "access_code": access_code,
                "metadata": json.dumps(metadata),
            },
        )

    return {
        "status": "success",
        "message": "Payment initialized.",
        "reference": returned_reference,
        "authorization_url": authorization_url,
        "access_code": access_code,
    }


# ============================================================
# VERIFY PAYMENT
# ============================================================

@router.get("/verify/{reference}")
def verify_payment(reference: str):

    try:
        response = requests.get(
            (
                f"{PAYSTACK_BASE_URL}"
                f"/transaction/verify/{reference}"
            ),
            headers=paystack_headers(),
            timeout=20,
        )

    except requests.RequestException as error:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Unable to reach Paystack: {error}"
            ),
        )

    if not response.ok:
        raise HTTPException(
            status_code=502,
            detail=(
                "Paystack verification failed: "
                f"{response.text}"
            ),
        )

    result = response.json()

    if not result.get("status"):
        raise HTTPException(
            status_code=400,
            detail=result.get(
                "message",
                "Unable to verify payment.",
            ),
        )

    data = result.get("data", {})

    gateway_status = data.get(
        "status",
        "unknown",
    )

    gateway_amount = int(
        data.get("amount", 0)
    )

    gateway_currency = str(
        data.get("currency", "NGN")
    ).upper()

    gateway_id = data.get("id")

    gateway_response = data.get(
        "gateway_response"
    )

    channel = data.get(
        "channel"
    )

    paid_at = data.get(
        "paid_at"
    )

    # --------------------------------------------------------
    # Retrieve our stored payment
    # --------------------------------------------------------

    select_query = text("""
        SELECT
            amount_minor,
            currency
        FROM public.payment_transactions
        WHERE reference = :reference;
    """)

    with engine.connect() as connection:
        stored_payment = connection.execute(
            select_query,
            {"reference": reference},
        ).mappings().first()

    if stored_payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment reference not found.",
        )

    expected_amount = int(
        stored_payment["amount_minor"]
    )

    expected_currency = str(
        stored_payment["currency"]
    ).upper()

    # --------------------------------------------------------
    # Verify amount
    # --------------------------------------------------------

    if gateway_amount != expected_amount:
        raise HTTPException(
            status_code=400,
            detail="Payment amount mismatch.",
        )

    # --------------------------------------------------------
    # Verify currency
    # --------------------------------------------------------

    if gateway_currency != expected_currency:
        raise HTTPException(
            status_code=400,
            detail="Payment currency mismatch.",
        )

    # --------------------------------------------------------
    # Update local record
    # --------------------------------------------------------

    update_query = text("""
        UPDATE public.payment_transactions
        SET
            status = :status,
            paystack_transaction_id = :paystack_transaction_id,
            gateway_response = :gateway_response,
            channel = :channel,
            paid_at = :paid_at,
            updated_at = CURRENT_TIMESTAMP
        WHERE reference = :reference;
    """)

    with engine.begin() as connection:
        connection.execute(
            update_query,
            {
                "status": gateway_status,
                "paystack_transaction_id": gateway_id,
                "gateway_response": gateway_response,
                "channel": channel,
                "paid_at": paid_at,
                "reference": reference,
            },
        )

    return {
        "status": "success",
        "reference": reference,
        "payment_status": gateway_status,
        "amount_minor": gateway_amount,
        "currency": gateway_currency,
        "channel": channel,
        "paid_at": paid_at,
    }


# ============================================================
# PAYMENT CALLBACK
# ============================================================

@router.get("/callback")
def payment_callback(
    reference: str | None = None,
):

    if not reference:
        return {
            "status": "received",
            "message": (
                "No payment reference was supplied."
            ),
        }

    return verify_payment(reference)


# ============================================================
# PAYSTACK WEBHOOK
# ============================================================

@router.post("/webhook")
async def paystack_webhook(
    request: Request,
    x_paystack_signature: str | None = Header(
        default=None
    ),
):

    if not PAYSTACK_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail=(
                "PAYSTACK_SECRET_KEY is not configured."
            ),
        )

    # --------------------------------------------------------
    # Read raw request body
    # --------------------------------------------------------

    raw_body = await request.body()

    if not x_paystack_signature:
        raise HTTPException(
            status_code=401,
            detail="Missing Paystack signature.",
        )

    # --------------------------------------------------------
    # Validate HMAC SHA512 signature
    # --------------------------------------------------------

    expected_signature = hmac.new(
        PAYSTACK_SECRET_KEY.encode("utf-8"),
        raw_body,
        hashlib.sha512,
    ).hexdigest()

    if not hmac.compare_digest(
        expected_signature,
        x_paystack_signature,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid Paystack signature.",
        )

    # --------------------------------------------------------
    # Parse event
    # --------------------------------------------------------

    try:
        event: dict[str, Any] = json.loads(
            raw_body.decode("utf-8")
        )

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload.",
        )

    event_type = event.get("event")

    data = event.get(
        "data",
        {},
    )

    reference = data.get(
        "reference"
    )

    if not reference:
        return {
            "status": "ignored",
            "message": (
                "Webhook contained no payment reference."
            ),
        }

    gateway_status = data.get(
        "status",
        "unknown",
    )

    gateway_id = data.get(
        "id"
    )

    gateway_response = data.get(
        "gateway_response"
    )

    channel = data.get(
        "channel"
    )

    paid_at = data.get(
        "paid_at"
    )

    # --------------------------------------------------------
    # Update payment record
    # --------------------------------------------------------

    update_query = text("""
        UPDATE public.payment_transactions
        SET
            status = :status,
            paystack_transaction_id = :paystack_transaction_id,
            gateway_response = :gateway_response,
            channel = :channel,
            paid_at = :paid_at,
            updated_at = CURRENT_TIMESTAMP
        WHERE reference = :reference;
    """)

    with engine.begin() as connection:
        result = connection.execute(
            update_query,
            {
                "status": gateway_status,
                "paystack_transaction_id": gateway_id,
                "gateway_response": gateway_response,
                "channel": channel,
                "paid_at": paid_at,
                "reference": reference,
            },
        )

    return {
        "status": "received",
        "event": event_type,
        "reference": reference,
        "payment_status": gateway_status,
        "updated": result.rowcount > 0,
    }

# ============================================================
# PAYMENT HISTORY
# ============================================================

@router.get("/history")
def get_payment_history(
    limit: int = 100,
):

    if limit < 1 or limit > 1000:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 1000.",
        )

    query = text("""
        SELECT
            reference,
            customer_email,
            amount_minor,
            currency,
            status,
            channel,
            paystack_transaction_id,
            gateway_response,
            paid_at,
            created_at,
            updated_at
        FROM public.payment_transactions
        ORDER BY created_at DESC
        LIMIT :limit;
    """)

    try:
        with engine.connect() as connection:
            result = connection.execute(
                query,
                {"limit": limit},
            )

            return [
                dict(row)
                for row in result.mappings()
            ]

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Payment history query failed: {error}",
        )

# ============================================================
# PAYMENT ANALYTICS
# ============================================================

@router.get("/analytics")
def get_payment_analytics():

    query = text("""
        SELECT
            total_payment_attempts,
            successful_payments,
            failed_payments,
            pending_payments,
            abandoned_payments,
            total_payment_value,
            successful_payment_value,
            average_payment_value,
            payment_success_rate
        FROM public.vw_payment_gateway_kpis;
    """)

    try:
        with engine.connect() as connection:

            result = connection.execute(query)

            row = result.mappings().first()

        if row is None:

            raise HTTPException(
                status_code=404,
                detail="Payment analytics not found.",
            )

        return dict(row)

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Payment analytics query failed: {error}"
            ),
        )


# ============================================================
# DAILY PAYMENT ANALYTICS
# ============================================================

@router.get("/analytics/daily")
def get_payment_daily_analytics():

    query = text("""
        SELECT
            payment_date,
            total_payment_attempts,
            successful_payments,
            failed_payments,
            pending_payments,
            abandoned_payments,
            total_payment_value,
            successful_payment_value,
            payment_success_rate
        FROM public.vw_payment_gateway_daily
        ORDER BY payment_date;
    """)

    try:

        with engine.connect() as connection:

            result = connection.execute(query)

            return [
                dict(row)
                for row in result.mappings()
            ]

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Daily payment analytics failed: "
                f"{error}"
            ),
        )


# ============================================================
# PAYMENT CHANNEL ANALYTICS
# ============================================================

@router.get("/analytics/channels")
def get_payment_channel_analytics():

    query = text("""
        SELECT
            payment_channel,
            total_payment_attempts,
            successful_payments,
            failed_payments,
            pending_payments,
            abandoned_payments,
            total_payment_value,
            successful_payment_value,
            payment_success_rate
        FROM public.vw_payment_gateway_channel
        ORDER BY total_payment_value DESC;
    """)

    try:

        with engine.connect() as connection:

            result = connection.execute(query)

            return [
                dict(row)
                for row in result.mappings()
            ]

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Payment channel analytics failed: "
                f"{error}"
            ),
        )