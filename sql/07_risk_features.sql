-- ============================================================
-- FINPAY ANALYTICS
-- 07 - RISK FEATURE ENGINEERING
-- ============================================================

DROP VIEW IF EXISTS public.vw_risk_features;


CREATE VIEW public.vw_risk_features AS

WITH base AS (

    SELECT
        t.transaction_id,
        t.customer_id,
        t.merchant_id,
        t.channel_id,
        t.partner_id,
        t.transaction_type,
        t.amount,
        t.currency,
        t.transaction_timestamp,

        EXTRACT(
            HOUR FROM t.transaction_timestamp
        )::INTEGER AS transaction_hour,

        EXTRACT(
            ISODOW FROM t.transaction_timestamp
        )::INTEGER AS day_of_week

    FROM public.transactions AS t

    WHERE t.transaction_timestamp IS NOT NULL
      AND t.amount IS NOT NULL
      AND t.amount > 0
),


historical_features AS (

    SELECT
        b.*,

        -- ----------------------------------------------------
        -- Customer historical behavior
        -- ----------------------------------------------------

        COUNT(*) OVER (
            PARTITION BY b.customer_id
            ORDER BY b.transaction_timestamp
            ROWS BETWEEN UNBOUNDED PRECEDING
                 AND 1 PRECEDING
        ) AS customer_tx_count_before,

        AVG(b.amount) OVER (
            PARTITION BY b.customer_id
            ORDER BY b.transaction_timestamp
            ROWS BETWEEN UNBOUNDED PRECEDING
                 AND 1 PRECEDING
        ) AS customer_avg_amount_before,

        STDDEV_SAMP(b.amount) OVER (
            PARTITION BY b.customer_id
            ORDER BY b.transaction_timestamp
            ROWS BETWEEN UNBOUNDED PRECEDING
                 AND 1 PRECEDING
        ) AS customer_std_amount_before,

        COUNT(*) OVER (
            PARTITION BY
                b.customer_id,
                b.transaction_type
            ORDER BY b.transaction_timestamp
            ROWS BETWEEN UNBOUNDED PRECEDING
                 AND 1 PRECEDING
        ) AS customer_type_count_before,


        -- ----------------------------------------------------
        -- Merchant historical behavior
        -- ----------------------------------------------------

        COUNT(*) OVER (
            PARTITION BY b.merchant_id
            ORDER BY b.transaction_timestamp
            ROWS BETWEEN UNBOUNDED PRECEDING
                 AND 1 PRECEDING
        ) AS merchant_tx_count_before,

        AVG(b.amount) OVER (
            PARTITION BY b.merchant_id
            ORDER BY b.transaction_timestamp
            ROWS BETWEEN UNBOUNDED PRECEDING
                 AND 1 PRECEDING
        ) AS merchant_avg_amount_before,


        -- ----------------------------------------------------
        -- Channel historical activity
        -- ----------------------------------------------------

        COUNT(*) OVER (
            PARTITION BY b.channel_id
            ORDER BY b.transaction_timestamp
            ROWS BETWEEN UNBOUNDED PRECEDING
                 AND 1 PRECEDING
        ) AS channel_tx_count_before,


        -- ----------------------------------------------------
        -- Partner historical activity
        -- ----------------------------------------------------

        COUNT(*) OVER (
            PARTITION BY b.partner_id
            ORDER BY b.transaction_timestamp
            ROWS BETWEEN UNBOUNDED PRECEDING
                 AND 1 PRECEDING
        ) AS partner_tx_count_before

    FROM base AS b
)


SELECT

    -- ========================================================
    -- IDENTIFIERS / METADATA
    -- ========================================================

    transaction_id,
    customer_id,
    merchant_id,
    channel_id,
    partner_id,
    transaction_type,
    currency,
    transaction_timestamp,


    -- ========================================================
    -- RAW TRANSACTION FEATURES
    -- ========================================================

    amount,

    LN(
        1 + amount
    ) AS log_amount,


    -- ========================================================
    -- TIME FEATURES
    -- ========================================================

    transaction_hour,
    day_of_week,

    SIN(
        2 * PI() * transaction_hour / 24.0
    ) AS transaction_hour_sin,

    COS(
        2 * PI() * transaction_hour / 24.0
    ) AS transaction_hour_cos,

    SIN(
        2 * PI() * day_of_week / 7.0
    ) AS day_of_week_sin,

    COS(
        2 * PI() * day_of_week / 7.0
    ) AS day_of_week_cos,


    -- ========================================================
    -- CUSTOMER FEATURES
    -- ========================================================

    COALESCE(
        customer_tx_count_before,
        0
    ) AS customer_tx_count_before,

    COALESCE(
        customer_avg_amount_before,
        0
    ) AS customer_avg_amount_before,

    COALESCE(
        customer_std_amount_before,
        0
    ) AS customer_std_amount_before,

    COALESCE(
        customer_type_count_before,
        0
    ) AS customer_type_count_before,

    CASE
        WHEN customer_avg_amount_before IS NULL
             OR customer_avg_amount_before = 0
        THEN 1.0

        ELSE
            amount / customer_avg_amount_before
    END AS customer_amount_ratio,

    CASE
        WHEN customer_std_amount_before IS NULL
             OR customer_std_amount_before = 0
        THEN 0.0

        ELSE
            (
                amount - customer_avg_amount_before
            )
            / customer_std_amount_before
    END AS customer_amount_zscore,


    -- ========================================================
    -- MERCHANT FEATURES
    -- ========================================================

    COALESCE(
        merchant_tx_count_before,
        0
    ) AS merchant_tx_count_before,

    COALESCE(
        merchant_avg_amount_before,
        0
    ) AS merchant_avg_amount_before,

    CASE
        WHEN merchant_avg_amount_before IS NULL
             OR merchant_avg_amount_before = 0
        THEN 1.0

        ELSE
            amount / merchant_avg_amount_before
    END AS merchant_amount_ratio,


    -- ========================================================
    -- CHANNEL / PARTNER FEATURES
    -- ========================================================

    COALESCE(
        channel_tx_count_before,
        0
    ) AS channel_tx_count_before,

    COALESCE(
        partner_tx_count_before,
        0
    ) AS partner_tx_count_before,


    -- ========================================================
    -- NEW CUSTOMER / MERCHANT FLAGS
    -- ========================================================

    CASE
        WHEN customer_tx_count_before IS NULL
             OR customer_tx_count_before = 0
        THEN 1

        ELSE 0
    END AS is_new_customer,

    CASE
        WHEN merchant_tx_count_before IS NULL
             OR merchant_tx_count_before = 0
        THEN 1

        ELSE 0
    END AS is_new_merchant


FROM historical_features;