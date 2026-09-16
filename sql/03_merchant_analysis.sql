-- ============================================
-- FINPAY ANALYTICS
-- MERCHANT PERFORMANCE ANALYSIS
-- ============================================

SELECT
    m.merchant_id,
    m.merchant_name,
    m.business_type,

    COUNT(t.transaction_id) AS total_transactions,

    COUNT(t.transaction_id) FILTER (
        WHERE t.transaction_status = 'Successful'
    ) AS successful_transactions,

    COUNT(t.transaction_id) FILTER (
        WHERE t.transaction_status = 'Failed'
    ) AS failed_transactions,

    ROUND(SUM(t.amount), 2) AS total_transaction_value,

    ROUND(AVG(t.amount), 2) AS average_transaction_value,

    ROUND(
        100.0 *
        COUNT(t.transaction_id) FILTER (
            WHERE t.transaction_status = 'Successful'
        )
        / NULLIF(COUNT(t.transaction_id), 0),
        2
    ) AS success_rate

FROM merchants m

JOIN transactions t
    ON m.merchant_id = t.merchant_id

GROUP BY
    m.merchant_id,
    m.merchant_name,
    m.business_type

ORDER BY
    total_transaction_value DESC;