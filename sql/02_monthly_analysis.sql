-- ============================================
-- FINPAY ANALYTICS
-- MONTHLY TRANSACTION ANALYSIS
-- ============================================

SELECT
    DATE_TRUNC('month', transaction_timestamp)::date AS month,

    COUNT(*) AS total_transactions,

    COUNT(*) FILTER (
        WHERE transaction_status = 'Successful'
    ) AS successful_transactions,

    COUNT(*) FILTER (
        WHERE transaction_status = 'Failed'
    ) AS failed_transactions,

    COUNT(*) FILTER (
        WHERE transaction_status = 'Pending'
    ) AS pending_transactions,

    ROUND(SUM(amount), 2) AS total_transaction_value,

    ROUND(AVG(amount), 2) AS average_transaction_value,

    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE transaction_status = 'Successful'
        )
        / NULLIF(COUNT(*), 0),
        2
    ) AS success_rate

FROM transactions

GROUP BY
    DATE_TRUNC('month', transaction_timestamp)

ORDER BY
    month;