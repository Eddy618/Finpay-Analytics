-- ============================================
-- FINPAY ANALYTICS
-- DATA QUALITY CHECKS
-- ============================================

-- Customer count
SELECT COUNT(*) AS total_customers
FROM customers;


-- Merchant count
SELECT COUNT(*) AS total_merchants
FROM merchants;


-- Transaction count
SELECT COUNT(*) AS total_transactions
FROM transactions;


-- Successful transactions
SELECT COUNT(*) AS successful_transactions
FROM transactions
WHERE transaction_status = 'Successful';


-- Failed transactions
SELECT COUNT(*) AS failed_transactions
FROM transactions
WHERE transaction_status = 'Failed';


-- Pending transactions
SELECT COUNT(*) AS pending_transactions
FROM transactions
WHERE transaction_status = 'Pending';


-- Total transaction value
SELECT
    SUM(amount) AS total_transaction_value
FROM transactions;


-- Average transaction value
SELECT
    AVG(amount) AS average_transaction_value
FROM transactions;

-- ============================================
-- FINPAY CORE TRANSACTION KPIs
-- ============================================

SELECT
    COUNT(*) AS total_transactions,

    SUM(amount) AS total_transaction_value,

    ROUND(AVG(amount), 2) AS average_transaction_value,

    MIN(amount) AS minimum_transaction,

    MAX(amount) AS maximum_transaction
FROM transactions;


SELECT
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

    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE transaction_status = 'Successful'
        )
        / NULLIF(COUNT(*), 0),
        2
    ) AS success_rate,

    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE transaction_status = 'Failed'
        )
        / NULLIF(COUNT(*), 0),
        2
    ) AS failure_rate

FROM transactions;
