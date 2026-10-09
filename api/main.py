"""
FinPay Analytics
Main FastAPI application.
"""

from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import text

from api.auth import CurrentUser, get_current_user, router as auth_router
from api.database import engine
from api.payments import router as payments_router


app = FastAPI(
    title="FinPay Analytics API",
    description="Fintech transaction intelligence and payment analytics API.",
    version="1.0.0",
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(auth_router)
app.include_router(payments_router)


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "finpay-api",
    }


# ============================================================
# KPI
# ============================================================

@app.get("/kpis")
def get_kpis(
    current_user: CurrentUser = Depends(get_current_user),
):
    with engine.connect() as connection:
        result = connection.execute(
            text(
                """
                SELECT *
                FROM public.vw_executive_kpis;
                """
            )
        )

        row = result.mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="KPI data not found.",
        )

    return dict(row)


# ============================================================
# TRANSACTIONS
# ============================================================

@app.get("/transactions")
def get_transactions(
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: CurrentUser = Depends(get_current_user),
):
    with engine.connect() as connection:
        result = connection.execute(
            text(
                """
                SELECT *
                FROM public.transactions
                ORDER BY transaction_timestamp DESC
                LIMIT :limit;
                """
            ),
            {"limit": limit},
        )

        return [dict(row) for row in result.mappings().all()]


# ============================================================
# ANOMALIES
# ============================================================

@app.get("/anomalies")
def get_anomalies(
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: CurrentUser = Depends(get_current_user),
):
    with engine.connect() as connection:
        result = connection.execute(
            text(
                """
                SELECT *
                FROM public.vw_transaction_anomalies
                ORDER BY transaction_timestamp DESC
                LIMIT :limit;
                """
            ),
            {"limit": limit},
        )

        return [dict(row) for row in result.mappings().all()]


# ============================================================
# RECONCILIATION
# ============================================================

@app.get("/reconciliation")
def get_reconciliation(
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: CurrentUser = Depends(get_current_user),
):
    with engine.connect() as connection:
        result = connection.execute(
            text(
                """
                SELECT *
                FROM public.vw_reconciliation
                LIMIT :limit;
                """
            ),
            {"limit": limit},
        )

        return [dict(row) for row in result.mappings().all()]


# ============================================================
# CHANNELS
# ============================================================

@app.get("/channels")
def get_channels(
    current_user: CurrentUser = Depends(get_current_user),
):
    with engine.connect() as connection:
        result = connection.execute(
            text(
                """
                SELECT *
                FROM public.vw_channel_performance;
                """
            )
        )

        return [dict(row) for row in result.mappings().all()]


# ============================================================
# PARTNERS
# ============================================================

@app.get("/partners")
def get_partners(
    current_user: CurrentUser = Depends(get_current_user),
):
    with engine.connect() as connection:
        result = connection.execute(
            text(
                """
                SELECT *
                FROM public.vw_partner_performance;
                """
            )
        )

        return [dict(row) for row in result.mappings().all()]


# ============================================================
# ML RISK
# ============================================================

@app.get("/risk")
def get_risk(
    limit: int = Query(default=100, ge=1, le=1000),
    category: Optional[str] = Query(default=None),
    anomalies_only: bool = Query(default=False),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Return ML-derived transaction risk records.

    This is an unsupervised anomaly score, not a fraud probability.
    """

    query = """
        SELECT *
        FROM public.vw_transaction_risk
        WHERE 1 = 1
    """

    params = {
        "limit": limit,
    }

    if category:
        query += """
            AND risk_category = :category
        """
        params["category"] = category

    if anomalies_only:
        query += """
            AND is_anomaly = 1
        """

    query += """
        ORDER BY risk_score DESC
        LIMIT :limit;
    """

    with engine.connect() as connection:
        result = connection.execute(
            text(query),
            params,
        )

        return [dict(row) for row in result.mappings().all()]


# ============================================================
# ML RISK SUMMARY
# ============================================================

@app.get("/risk/summary")
def get_risk_summary(
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Return summary statistics for the ML risk model.
    """

    with engine.connect() as connection:
        result = connection.execute(
            text(
                """
                SELECT
                    COUNT(*) AS total_scored,
                    SUM(is_anomaly) AS total_anomalies,
                    ROUND(
                        AVG(risk_score)::numeric,
                        2
                    ) AS average_risk_score,
                    ROUND(
                        MIN(risk_score)::numeric,
                        2
                    ) AS minimum_risk_score,
                    ROUND(
                        MAX(risk_score)::numeric,
                        2
                    ) AS maximum_risk_score
                FROM public.transaction_risk_scores;
                """
            )
        )

        row = result.mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Risk summary not found.",
        )

    return dict(row)


# ============================================================
# TOP ML RISKS
# ============================================================

@app.get("/risk/top")
def get_top_risks(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Return the highest-risk transactions.
    """

    with engine.connect() as connection:
        result = connection.execute(
            text(
                """
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
                    risk_score,
                    is_anomaly,
                    risk_category,
                    model_name,
                    model_version,
                    scored_at
                FROM public.vw_transaction_risk
                ORDER BY risk_score DESC
                LIMIT :limit;
                """
            ),
            {"limit": limit},
        )

        return [dict(row) for row in result.mappings().all()]