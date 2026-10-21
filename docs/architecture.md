# FinPay Analytics — System Architecture

## 1. Overview

FinPay Analytics is a payment transaction analytics project that uses Python, PostgreSQL, FastAPI, and Streamlit to process transaction data and present business insights.

## 2. System Components

### Data Source
Provides the transaction data used by the analytics pipeline. The project uses simulated data for demonstration.

### ETL Pipeline
The Python ETL process connects to PostgreSQL, checks the latest loaded transaction timestamp, extracts new records, and logs each pipeline run.

### PostgreSQL Database
Stores transaction records and supports SQL queries and views used for analytics, anomaly investigation, and reconciliation monitoring.

### Analytics Layer
SQL queries and database views calculate transaction metrics and identify records requiring further investigation.

### FastAPI Backend
Provides API endpoints for health checks, transaction information, KPIs, and other analytics.

### Streamlit Dashboard
Presents analytics in a dashboard for users who need to monitor payment performance.

## 3. Data Flow

1. Transaction data is obtained from the configured source.
2. The ETL pipeline extracts and loads available records.
3. PostgreSQL stores and serves transaction data.
4. SQL analytics produce KPI and monitoring results.
5. FastAPI exposes selected results through endpoints.
6. The dashboard displays analytics to business users.

## 4. Example Business Uses

- Monitor transaction success rates.
- Investigate failed transactions.
- Identify transactions flagged as anomalous.
- Review reconciliation exceptions.
- Track transaction volume and value.

## 5. Security Considerations

- Keep credentials and database connection strings in environment variables.
- Do not commit `.env` files or production credentials.
- Protect endpoints that expose sensitive data.
- Use synthetic data in public demonstrations.

## 6. Scope and Limitations

FinPay Analytics is a portfolio project using simulated financial data. Its anomaly rules and KPI definitions should be interpreted within the project's dataset and implementation; they are not proof of a production-grade fraud detection system.