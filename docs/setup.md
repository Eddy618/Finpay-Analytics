# FinPay Analytics — Setup Guide

## Prerequisites

- Python version compatible with the project dependencies.
- PostgreSQL.
- Git.
- Access to the project's required data source.

## 1. Clone the Repository

```bash
git clone https://github.com/Eddy618/Finpay-Analytics.git
cd Finpay-Analytics
```

## 2. Create a Virtual Environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use the appropriate Windows execution-policy guidance or activate the environment from your IDE.

## 3. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

## 4. Configure Environment Variables

Create a local `.env` file using the variable names expected by the project.

Add the required PostgreSQL connection settings and other configuration values. Do not commit this file to GitHub.

Refer to the project's configuration code for the exact required variable names.

## 5. Configure PostgreSQL

Create the database and user required by the project. Apply the SQL schema or initialization scripts provided in the repository.

Use the actual database name and schema configured in your environment.

## 6. Run the ETL Pipeline

```powershell
python src/etl.py
```

Check the terminal output for the database connection result, extracted record count, and ETL execution status.

## 7. Run the API

Use the FastAPI application module configured in the repository.

For example, if the application object is named `app` in `api/main.py`:

```powershell
python -m uvicorn api.main:app --reload
```

The module path above is an example. Confirm the actual application file before running the command.

## 8. Run Automated Tests

```powershell
python -m pytest -v
```

Record the actual test results and any warnings.

## 9. Troubleshooting

- **Database connection failure:** Check PostgreSQL status, credentials, host, and port.
- **Missing package:** Activate the correct virtual environment and reinstall dependencies.
- **Uvicorn import error:** Confirm the module path and FastAPI application variable.
- **Missing environment variable:** Check the project's configuration and `.env` file.
- **No new ETL records:** Check the source data and timestamp watermark before assuming the pipeline is broken.