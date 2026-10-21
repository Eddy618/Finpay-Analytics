# FinPay Analytics

**Payment Transaction Intelligence | Python · PostgreSQL · FastAPI · Streamlit**

FinPay Analytics is a financial transaction analytics project designed to transform payment data into actionable business insights. It combines data engineering, database management, transaction monitoring, reconciliation analysis, and API development.

## Business Problem

Payment businesses need to monitor transaction performance, identify unusual activity, track failed payments, and investigate transactions that have not been reconciled.

FinPay Analytics demonstrates how transaction data can be processed and presented to support these activities.

## Key Features

- **ETL pipeline:** Extracts transaction data and loads it into PostgreSQL.
- **Executive KPIs:** Summarises transaction volume, value, and success rates.
- **Anomaly monitoring:** Identifies transactions flagged by the project's anomaly rules.
- **Reconciliation analysis:** Highlights transactions requiring reconciliation investigation.
- **REST API:** Exposes transaction and analytics data through FastAPI.
- **Automated testing:** Tests application endpoints and core functionality.

## Technology Stack

- Python — data processing and backend logic
- PostgreSQL — relational data storage and SQL analytics
- FastAPI — REST API
- Streamlit — analytics dashboard
- pytest — automated testing
- Docker — containerisation, where configured

## Architecture

1. Transaction data enters the ETL pipeline.
2. Python processes the data and loads it into PostgreSQL.
3. SQL queries and views support transaction analysis and KPI calculations.
4. FastAPI exposes selected data through API endpoints.
5. The dashboard presents analytics for business users.

## Key Business Questions

- How many transactions were processed?
- What proportion of transactions succeeded?
- What is the total transaction value?
- Which transactions have been flagged as anomalous?
- Which transactions require reconciliation follow-up?

## Project Validation

Document the actual results of your latest ETL run, automated test suite, and live API checks here. Clearly distinguish local tests from live deployment checks.

## Getting Started

See [Setup Instructions](docs/setup.md) for environment configuration, database setup, installation, and execution commands.

## Project Documentation

- [Architecture](docs/architecture.md)
- [Setup Guide](docs/setup.md)
- [Data Dictionary](docs/data_dictionary.md)
- [Testing Guide](docs/testing.md)

## Data Disclaimer

This project uses simulated financial transaction data for demonstration and educational purposes. It is not a representation of actual customer transactions or a production financial monitoring system.

## Author

**Eddy618**

GitHub: [FinPay Analytics](https://github.com/Eddy618/Finpay-Analytics)
