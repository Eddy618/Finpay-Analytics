from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import text

from api.database import engine
from api.payments import router as payments_router


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="FinPay Analytics API",
    description="FinPay transaction analytics, risk, reconciliation, and payments API",
    version="1.0.0",
)


# Register payment routes
app.include_router(payments_router)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "application": "FinPay Analytics API",
        "status": "running",
        "version": "1.0.0",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {error}",
        )


# ============================================================
# EXECUTIVE KPIs
# ============================================================

@app.get("/kpis")
def get_kpis():

    query = text("""
        SELECT
            total_transactions,
            successful_transactions,
            failed_transactions,
            pending_transactions,
            refunded_transactions,
            total_transaction_value,
            successful_transaction_value,
            average_transaction_value,
            success_rate
        FROM public.vw_executive_kpis;
    """)

    try:
        with engine.connect() as connection:
            result = connection.execute(query)
            row = result.mappings().first()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="KPI data not found.",
            )

        return dict(row)

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"KPI query failed: {error}",
        )


# ============================================================
# TRANSACTIONS
# ============================================================

@app.get("/transactions")
def get_transactions(
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
    ),
    status: str | None = None,
    transaction_type: str | None = None,
):

    conditions = []
    params = {
        "limit": limit,
    }

    if status:
        conditions.append(
            "transaction_status = :status"
        )
        params["status"] = status

    if transaction_type:
        conditions.append(
            "transaction_type = :transaction_type"
        )
        params["transaction_type"] = transaction_type

    where_clause = ""

    if conditions:
        where_clause = (
            "WHERE " + " AND ".join(conditions)
        )

    query = text(f"""
        SELECT
            transaction_id,
            customer_id,
            merchant_id,
            channel_id,
            partner_id,
            transaction_type,
            transaction_status,
            amount,
            currency,
            transaction_timestamp,
            completed_timestamp,
            failure_reason
        FROM public.transactions
        {where_clause}
        ORDER BY transaction_timestamp DESC
        LIMIT :limit;
    """)

    try:
        with engine.connect() as connection:
            result = connection.execute(
                query,
                params,
            )

            return [
                dict(row)
                for row in result.mappings()
            ]

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Transaction query failed: {error}",
        )


# ============================================================
# ANOMALIES
# ============================================================

@app.get("/anomalies")
def get_anomalies(
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
    ),
):

    query = text("""
        SELECT
            transaction_id,
            customer_id,
            merchant_id,
            transaction_type,
            transaction_status,
            amount,
            processing_time_minutes,
            transaction_anomaly,
            reconciliation_status,
            risk_category
        FROM public.vw_transaction_anomalies
        WHERE risk_category <> 'Normal'
        ORDER BY amount DESC
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
            detail=f"Anomaly query failed: {error}",
        )


# ============================================================
# RECONCILIATION
# ============================================================

@app.get("/reconciliation")
def get_reconciliation(
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
    ),
):

    query = text("""
        SELECT
            transaction_id,
            partner_id,
            transaction_status,
            transaction_amount,
            settlement_id,
            settlement_amount,
            settlement_status,
            reconciliation_status
        FROM public.vw_reconciliation
        WHERE reconciliation_status <> 'Matched'
        ORDER BY transaction_amount DESC
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
            detail=f"Reconciliation query failed: {error}",
        )


# ============================================================
# CHANNEL PERFORMANCE
# ============================================================

@app.get("/channels")
def get_channels():

    query = text("""
        SELECT
            channel_name,
            total_transactions,
            successful_transactions,
            failed_transactions,
            pending_transactions,
            total_transaction_value,
            average_transaction_value,
            success_rate
        FROM public.vw_channel_performance
        ORDER BY total_transaction_value DESC;
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
            detail=f"Channel query failed: {error}",
        )


# ============================================================
# PARTNER PERFORMANCE
# ============================================================

@app.get("/partners")
def get_partners():

    query = text("""
        SELECT
            partner_name,
            partner_type,
            total_transactions,
            successful_transactions,
            failed_transactions,
            pending_transactions,
            total_transaction_value,
            average_transaction_value,
            success_rate
        FROM public.vw_partner_performance
        ORDER BY total_transaction_value DESC;
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
            detail=f"Partner query failed: {error}",
        )