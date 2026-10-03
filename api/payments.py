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

from api.audit import write_audit_log
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
).rstrip("/")

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
            detail="PAYSTACK_SECRET_KEY is not configured.",
        )

    return {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": (
            "FinPay-Analytics/1.0"
        ),
    }


# ============================================================
# INITIALIZE PAYMENT
# ============================================================

@router.post("/initialize")
def initialize_payment(
    payment: PaymentInitializeRequest,
    request: Request,
):
    """
    Initialize a Paystack payment.

    The requested amount is supplied in NGN and converted
    to the currency's minor unit before sending to Paystack.
    """

    # --------------------------------------------------------
    # Validate and convert amount
    # --------------------------------------------------------

    try:
        amount_minor_decimal = (
            payment.amount_naira * Decimal("100")
        )

        # Prevent silent truncation such as:
        # 10.001 NGN -> 1000 kobo
        if (
            amount_minor_decimal
            != amount_minor_decimal.to_integral_value()
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Amount must have no more than two "
                    "decimal places for NGN."
                ),
            )

        amount_minor = int(
            amount_minor_decimal
        )

    except InvalidOperation:
        raise HTTPException(
            status_code=400,
            detail="Invalid payment amount.",
        )

    if amount_minor <= 0:
        raise HTTPException(
            status_code=400,
            detail="Payment amount must be greater than zero.",
        )

    # --------------------------------------------------------
    # Currency
    # --------------------------------------------------------

    currency = payment.currency.upper()

    # --------------------------------------------------------
    # Generate unique reference
    # --------------------------------------------------------

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
            detail=f"Unable to reach Paystack: {error}",
        )

    # --------------------------------------------------------
    # Paystack response validation
    # --------------------------------------------------------

    if not response.ok:
        raise HTTPException(
            status_code=502,
            detail=(
                "Paystack initialization failed: "
                f"{response.text}"
            ),
        )

    try:
        result = response.json()

    except ValueError:
        raise HTTPException(
            status_code=502,
            detail="Paystack returned an invalid JSON response.",
        )

    if not result.get("status"):
        raise HTTPException(
            status_code=400,
            detail=result.get(
                "message",
                "Paystack rejected the payment.",
            ),
        )

    data = result.get(
        "data",
        {},
    )

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

    try:
        with engine.begin() as connection:
            result = connection.execute(
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

            if result.rowcount == 0:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Payment reference already exists."
                    ),
                )

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Unable to save payment initialization: "
                f"{error}"
            ),
        )

    # --------------------------------------------------------
    # Audit AFTER database insert succeeds
    # --------------------------------------------------------

    client_ip = (
        request.client.host
        if request.client
        else None
    )

    write_audit_log(
        action="payment_initialized",
        resource_type="payment",
        resource_id=returned_reference,
        http_method="POST",
        endpoint="/payments/initialize",
        ip_address=client_ip,
        status_code=200,
        new_value={
            "reference": returned_reference,
            "currency": currency,
            "amount_minor": amount_minor,
            "status": "initialized",
        },
        details={
            "customer_email": payment.email,
            "description": payment.description,
            "gateway": "paystack",
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
# INTERNAL PAYMENT VERIFICATION
# ============================================================

def _verify_payment(
    reference: str,
    *,
    endpoint: str,
    ip_address: str | None = None,
):
    """
    Verify payment with Paystack and update the local record.
    """

    # --------------------------------------------------------
    # Call Paystack
    # --------------------------------------------------------

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
            detail=f"Unable to reach Paystack: {error}",
        )

    if not response.ok:
        raise HTTPException(
            status_code=502,
            detail=(
                "Paystack verification failed: "
                f"{response.text}"
            ),
        )

    try:
        result = response.json()

    except ValueError:
        raise HTTPException(
            status_code=502,
            detail="Paystack returned invalid JSON.",
        )

    if not result.get("status"):
        raise HTTPException(
            status_code=400,
            detail=result.get(
                "message",
                "Unable to verify payment.",
            ),
        )

    data = result.get(
        "data",
        {},
    )

    gateway_status = str(
        data.get(
            "status",
            "unknown",
        )
    ).lower()

    gateway_amount = int(
        data.get(
            "amount",
            0,
        )
    )

    gateway_currency = str(
        data.get(
            "currency",
            "NGN",
        )
    ).upper()

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
    # Get existing local payment
    # --------------------------------------------------------

    select_query = text("""
        SELECT
            amount_minor,
            currency,
            status
        FROM public.payment_transactions
        WHERE reference = :reference;
    """)

    try:
        with engine.connect() as connection:
            stored_payment = connection.execute(
                select_query,
                {
                    "reference": reference
                },
            ).mappings().first()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Unable to retrieve local payment: "
                f"{error}"
            ),
        )

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

    previous_status = str(
        stored_payment["status"]
    )

    # --------------------------------------------------------
    # Verify amount
    # --------------------------------------------------------

    if gateway_amount != expected_amount:
        write_audit_log(
            action="payment_verification_rejected",
            resource_type="payment",
            resource_id=reference,
            http_method="GET",
            endpoint=endpoint,
            ip_address=ip_address,
            status_code=400,
            old_value={
                "status": previous_status,
            },
            new_value={
                "status": gateway_status,
                "gateway_amount": gateway_amount,
                "expected_amount": expected_amount,
            },
            details={
                "reason": "amount_mismatch",
                "gateway": "paystack",
            },
        )

        raise HTTPException(
            status_code=400,
            detail="Payment amount mismatch.",
        )

    # --------------------------------------------------------
    # Verify currency
    # --------------------------------------------------------

    if gateway_currency != expected_currency:
        write_audit_log(
            action="payment_verification_rejected",
            resource_type="payment",
            resource_id=reference,
            http_method="GET",
            endpoint=endpoint,
            ip_address=ip_address,
            status_code=400,
            old_value={
                "status": previous_status,
            },
            new_value={
                "status": gateway_status,
                "gateway_currency": gateway_currency,
                "expected_currency": expected_currency,
            },
            details={
                "reason": "currency_mismatch",
                "gateway": "paystack",
            },
        )

        raise HTTPException(
            status_code=400,
            detail="Payment currency mismatch.",
        )

    # --------------------------------------------------------
    # Update local payment
    # --------------------------------------------------------

    update_query = text("""
        UPDATE public.payment_transactions
        SET
            status = :status,
            paystack_transaction_id =
                :paystack_transaction_id,
            gateway_response = :gateway_response,
            channel = :channel,
            paid_at = :paid_at,
            updated_at = CURRENT_TIMESTAMP
        WHERE reference = :reference;
    """)

    try:
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

            if result.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        "Payment record could not be updated."
                    ),
                )

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Unable to update payment: {error}"
            ),
        )

    # --------------------------------------------------------
    # Audit verification
    # --------------------------------------------------------

    write_audit_log(
        action="payment_verified",
        resource_type="payment",
        resource_id=reference,
        http_method="GET",
        endpoint=endpoint,
        ip_address=ip_address,
        status_code=200,
        old_value={
            "status": previous_status,
        },
        new_value={
            "status": gateway_status,
            "channel": channel,
            "amount_minor": gateway_amount,
            "currency": gateway_currency,
            "paystack_transaction_id": gateway_id,
            "paid_at": paid_at,
        },
        details={
            "gateway": "paystack",
            "gateway_response": gateway_response,
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
# VERIFY PAYMENT
# ============================================================

@router.get("/verify/{reference}")
def verify_payment(
    reference: str,
    request: Request,
):
    client_ip = (
        request.client.host
        if request.client
        else None
    )

    return _verify_payment(
        reference,
        endpoint=f"/payments/verify/{reference}",
        ip_address=client_ip,
    )


# ============================================================
# PAYMENT CALLBACK
# ============================================================

@router.get("/callback")
def payment_callback(
    reference: str | None = None,
    request: Request = None,
):
    client_ip = (
        request.client.host
        if request is not None
        and request.client
        else None
    )

    if not reference:
        return {
            "status": "received",
            "message": (
                "No payment reference was supplied."
            ),
        }

    return _verify_payment(
        reference,
        endpoint="/payments/callback",
        ip_address=client_ip,
    )


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
    """
    Process authenticated Paystack webhook events.
    """

    client_ip = (
        request.client.host
        if request.client
        else None
    )

    if not PAYSTACK_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail=(
                "PAYSTACK_SECRET_KEY is not configured."
            ),
        )

    # --------------------------------------------------------
    # Read raw body
    # --------------------------------------------------------

    raw_body = await request.body()

    if not x_paystack_signature:
        write_audit_log(
            action="payment_webhook_rejected",
            resource_type="payment",
            resource_id=None,
            http_method="POST",
            endpoint="/payments/webhook",
            ip_address=client_ip,
            status_code=401,
            details={
                "reason": "missing_signature",
            },
        )

        raise HTTPException(
            status_code=401,
            detail="Missing Paystack signature.",
        )

    # --------------------------------------------------------
    # HMAC SHA512 validation
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
        write_audit_log(
            action="payment_webhook_rejected",
            resource_type="payment",
            resource_id=None,
            http_method="POST",
            endpoint="/payments/webhook",
            ip_address=client_ip,
            status_code=401,
            details={
                "reason": "invalid_signature",
            },
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid Paystack signature.",
        )

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    try:
        event: dict[str, Any] = json.loads(
            raw_body.decode("utf-8")
        )

    except json.JSONDecodeError:
        write_audit_log(
            action="payment_webhook_rejected",
            resource_type="payment",
            resource_id=None,
            http_method="POST",
            endpoint="/payments/webhook",
            ip_address=client_ip,
            status_code=400,
            details={
                "reason": "invalid_json",
            },
        )

        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload.",
        )

    event_type = event.get(
        "event"
    )

    data = event.get(
        "data",
        {},
    )

    reference = data.get(
        "reference"
    )

    if not reference:
        write_audit_log(
            action="payment_webhook_ignored",
            resource_type="payment",
            resource_id=None,
            http_method="POST",
            endpoint="/payments/webhook",
            ip_address=client_ip,
            status_code=200,
            details={
                "reason": "missing_reference",
                "event": event_type,
            },
        )

        return {
            "status": "ignored",
            "message": (
                "Webhook contained no payment reference."
            ),
        }

    # --------------------------------------------------------
    # Extract gateway values
    # --------------------------------------------------------

    gateway_status = str(
        data.get(
            "status",
            "unknown",
        )
    ).lower()

    gateway_amount = int(
        data.get(
            "amount",
            0,
        )
    )

    gateway_currency = str(
        data.get(
            "currency",
            "NGN",
        )
    ).upper()

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
    # Lock and retrieve local payment
    # --------------------------------------------------------

    select_query = text("""
        SELECT
            amount_minor,
            currency,
            status
        FROM public.payment_transactions
        WHERE reference = :reference
        FOR UPDATE;
    """)

    update_query = text("""
        UPDATE public.payment_transactions
        SET
            status = :status,
            paystack_transaction_id =
                :paystack_transaction_id,
            gateway_response = :gateway_response,
            channel = :channel,
            paid_at = :paid_at,
            updated_at = CURRENT_TIMESTAMP
        WHERE reference = :reference;
    """)

    try:
        with engine.begin() as connection:

            stored_payment = connection.execute(
                select_query,
                {
                    "reference": reference,
                },
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

            previous_status = str(
                stored_payment["status"]
            )

            # ------------------------------------------------
            # Validate amount
            # ------------------------------------------------

            if gateway_amount != expected_amount:
                write_audit_log(
                    action="payment_webhook_rejected",
                    resource_type="payment",
                    resource_id=reference,
                    http_method="POST",
                    endpoint="/payments/webhook",
                    ip_address=client_ip,
                    status_code=400,
                    old_value={
                        "status": previous_status,
                    },
                    new_value={
                        "status": gateway_status,
                        "gateway_amount": gateway_amount,
                        "expected_amount": expected_amount,
                    },
                    details={
                        "reason": "amount_mismatch",
                        "event": event_type,
                        "gateway": "paystack",
                    },
                )

                raise HTTPException(
                    status_code=400,
                    detail="Payment amount mismatch.",
                )

            # ------------------------------------------------
            # Validate currency
            # ------------------------------------------------

            if gateway_currency != expected_currency:
                write_audit_log(
                    action="payment_webhook_rejected",
                    resource_type="payment",
                    resource_id=reference,
                    http_method="POST",
                    endpoint="/payments/webhook",
                    ip_address=client_ip,
                    status_code=400,
                    old_value={
                        "status": previous_status,
                    },
                    new_value={
                        "status": gateway_status,
                        "gateway_currency": gateway_currency,
                        "expected_currency": expected_currency,
                    },
                    details={
                        "reason": "currency_mismatch",
                        "event": event_type,
                        "gateway": "paystack",
                    },
                )

                raise HTTPException(
                    status_code=400,
                    detail="Payment currency mismatch.",
                )

            # ------------------------------------------------
            # Idempotency
            # ------------------------------------------------
            #
            # If Paystack retries the same successful event,
            # updating the row again is safe. We record the
            # webhook event as received without duplicating
            # payment rows.

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

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Webhook database update failed: "
                f"{error}"
            ),
        )

    # --------------------------------------------------------
    # Audit webhook
    # --------------------------------------------------------

    write_audit_log(
        action="payment_webhook_received",
        resource_type="payment",
        resource_id=reference,
        http_method="POST",
        endpoint="/payments/webhook",
        ip_address=client_ip,
        status_code=200,
        new_value={
            "status": gateway_status,
            "channel": channel,
            "amount_minor": gateway_amount,
            "currency": gateway_currency,
            "paystack_transaction_id": gateway_id,
            "paid_at": paid_at,
        },
        details={
            "event": event_type,
            "gateway": "paystack",
            "gateway_response": gateway_response,
        },
    )

    return {
        "status": "received",
        "event": event_type,
        "reference": reference,
        "payment_status": gateway_status,
        "updated": True,
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
            detail=(
                "Limit must be between 1 and 1000."
            ),
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
                {
                    "limit": limit,
                },
            )

            return [
                dict(row)
                for row in result.mappings()
            ]

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Payment history query failed: "
                f"{error}"
            ),
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

            result = connection.execute(
                query
            )

            row = result.mappings().first()

        if row is None:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Payment analytics not found."
                ),
            )

        return dict(row)

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Payment analytics query failed: "
                f"{error}"
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

            result = connection.execute(
                query
            )

            return [
                dict(row)
                for row in result.mappings()
            ]

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Daily payment analytics failed: "
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

            result = connection.execute(
                query
            )

            return [
                dict(row)
                for row in result.mappings()
            ]

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Payment channel analytics failed: "
                f"{error}"
            ),
        )