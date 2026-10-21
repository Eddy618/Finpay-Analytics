# FinPay Analytics — Data Dictionary

## 1. Purpose

This document explains the main data entities and business metrics used in FinPay Analytics. The project uses simulated financial transaction data for educational and portfolio purposes.

## 2. Core Data Entities

| Entity | Purpose |
|---|---|
| Transactions | Records payment transactions and their statuses, amounts, and processing details. |
| Customers | Represents customers associated with transactions. |
| Merchants | Represents businesses receiving payments. |
| Channels | Identifies the channels through which payments are processed. |
| Partners | Represents payment partners involved in processing transactions. |
| Settlements | Contains settlement-related records used for reconciliation analysis. |

**Note:** Confirm the actual table names, columns, and relationships against the SQL files in the repository before treating this list as the definitive schema.

## 3. Key Business Metrics

### Total Transactions
The number of transaction records included in the reporting period.

### Total Transaction Value
The sum of transaction amounts included in the metric. Document whether this includes all transaction statuses or only selected statuses.

### Transaction Success Rate
The proportion of transactions considered successful.

Formula:

Success Rate = (Successful Transactions / Total Eligible Transactions) × 100

Define which statuses count as successful and which transactions are included in the denominator.

### Transaction Anomalies
The number of transactions flagged by the project's implemented anomaly-monitoring rules.

An anomaly flag indicates that a transaction meets a defined rule; it does not automatically prove fraud.

### Reconciliation Exceptions
Transactions that cannot be matched to the expected settlement records under the project's reconciliation logic.

An unmatched record may require investigation and should not automatically be described as a financial loss.

## 4. Data Quality

The project includes data-quality validation and monitoring. Document the actual checks implemented in the ETL pipeline, such as missing values, duplicate records, invalid amounts, or inconsistent statuses, only where those checks exist in the code.

## 5. Dataset Limitations

- The dataset is simulated.
- Results demonstrate analytical workflows rather than actual payment-industry performance.
- Anomaly counts depend on the implemented rules.
- Reconciliation results depend on the available settlement data and matching logic.
- KPI values should be interpreted according to their implemented definitions.

## 6. Schema Verification

Before finalising this document, verify:

- Actual table and view names.
- Column names and PostgreSQL data types.
- Primary and foreign keys.
- Relationships between transactions and related entities.
- Definitions and SQL formulas used by the API and dashboards.

Refer to the SQL files and database schema in the project repository for the authoritative definitions.

# FinPay Analytics — Data Dictionary

## 1. `vw_risk_features`

A SQL view that generates transaction features for fraud and anomaly detection from `public.transactions`.

| Column | Description |
|---|---|
| `transaction_id` | Unique transaction identifier |
| `customer_id` | Customer associated with the transaction |
| `merchant_id` | Merchant receiving the transaction |
| `channel_id` | Transaction channel |
| `partner_id` | Payment partner |
| `transaction_type` | Type of transaction |
| `currency` | Transaction currency |
| `transaction_timestamp` | Date and time of transaction |
| `amount` | Transaction amount |
| `log_amount` | Log-transformed transaction amount |
| `transaction_hour` | Hour of the transaction |
| `day_of_week` | ISO weekday number |
| `transaction_hour_sin/cos` | Cyclical hour features |
| `day_of_week_sin/cos` | Cyclical weekday features |
| `customer_tx_count_before` | Previous transactions by the customer |
| `customer_avg_amount_before` | Customer's previous average transaction amount |
| `customer_std_amount_before` | Standard deviation of previous customer transaction amounts |
| `customer_type_count_before` | Previous transactions of the same type by the customer |
| `customer_amount_ratio` | Current amount divided by previous customer average |
| `customer_amount_zscore` | Standardized difference from customer average |
| `merchant_tx_count_before` | Previous transactions associated with the merchant |
| `merchant_avg_amount_before` | Merchant's previous average transaction amount |
| `merchant_amount_ratio` | Current amount divided by merchant's previous average |
| `channel_tx_count_before` | Previous transactions through the channel |
| `partner_tx_count_before` | Previous transactions through the partner |
| `is_new_customer` | 1 if no previous customer transaction exists; otherwise 0 |
| `is_new_merchant` | 1 if no previous merchant transaction exists; otherwise 0 |

**Filtering:** Only transactions with a non-null timestamp and a positive, non-null amount are included.

## 2. `transaction_risk_scores`

Stores anomaly detection scores produced by the risk model.

| Column | Description |
|---|---|
| `risk_id` | Auto-generated primary key |
| `transaction_id` | Unique transaction ID linked to the source transaction |
| `risk_score_raw` | Raw model risk score |
| `risk_score` | Processed risk score |
| `is_anomaly` | Binary anomaly indicator: 0 or 1 |
| `risk_category` | Risk classification: Low, Moderate, High, or Critical |
| `model_name` | Name of the model; defaults to `IsolationForest` |
| `model_version` | Model version; defaults to `1.0` |
| `scored_at` | Date and time the risk score was recorded |

**Indexes:** Risk score, risk category, anomaly flag, and scoring timestamp.

## 3. `vw_transaction_risk`

Combines stored risk scores with transaction details for reporting and analysis.

It includes the risk record ID, transaction and customer identifiers, merchant, channel, partner, transaction type and status, amount, currency, transaction timestamp, risk scores, anomaly flag, risk category, model name, model version, and scoring timestamp.

## 4. Risk classification

The database permits these categories:

- **Low**
- **Moderate**
- **High**
- **Critical**

The table enforces `is_anomaly` as either 0 or 1. Exact score thresholds are not defined in these SQL files; they depend on the model-scoring logic.

## 5. Data lineage

`public.transactions` → `public.vw_risk_features` → risk model scoring → `public.transaction_risk_scores` → `public.vw_transaction_risk`.

The feature view calculates historical customer, merchant, channel, and partner activity. The scoring table stores model outputs, while the final view joins scores back to transaction records for analytics.
