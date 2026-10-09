-- ============================================================
-- FINPAY ANALYTICS
-- 08 - RISK SCORE STORAGE
-- ============================================================

CREATE TABLE IF NOT EXISTS public.transaction_risk_scores (
    risk_id BIGSERIAL PRIMARY KEY,

    transaction_id UUID NOT NULL UNIQUE,

    risk_score_raw DOUBLE PRECISION NOT NULL,
    risk_score DOUBLE PRECISION NOT NULL,

    is_anomaly INTEGER NOT NULL
        CHECK (is_anomaly IN (0, 1)),

    risk_category VARCHAR(20) NOT NULL
        CHECK (
            risk_category IN (
                'Low',
                'Moderate',
                'High',
                'Critical'
            )
        ),

    model_name VARCHAR(100) NOT NULL
        DEFAULT 'IsolationForest',

    model_version VARCHAR(50) NOT NULL
        DEFAULT '1.0',

    scored_at TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_transaction_risk_score
ON public.transaction_risk_scores (
    risk_score DESC
);

CREATE INDEX IF NOT EXISTS idx_transaction_risk_category
ON public.transaction_risk_scores (
    risk_category
);

CREATE INDEX IF NOT EXISTS idx_transaction_risk_anomaly
ON public.transaction_risk_scores (
    is_anomaly
);

CREATE INDEX IF NOT EXISTS idx_transaction_risk_scored_at
ON public.transaction_risk_scores (
    scored_at DESC
);


-- ============================================================
-- ANALYTICS VIEW
-- ============================================================

CREATE OR REPLACE VIEW public.vw_transaction_risk AS
SELECT
    r.risk_id,
    r.transaction_id,

    t.customer_id,
    t.merchant_id,
    t.channel_id,
    t.partner_id,
    t.transaction_type,
    t.transaction_status,
    t.amount,
    t.currency,
    t.transaction_timestamp,

    r.risk_score_raw,
    r.risk_score,
    r.is_anomaly,
    r.risk_category,
    r.model_name,
    r.model_version,
    r.scored_at

FROM public.transaction_risk_scores AS r

JOIN public.transactions AS t
    ON t.transaction_id = r.transaction_id;