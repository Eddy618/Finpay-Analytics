import os
from pathlib import Path
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()


def get_database_engine():
    """Create a connection to the PostgreSQL database."""

    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    database = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    if not all([database, user, password]):
        raise ValueError(
            "Database settings are missing. "
            "Check your .env file."
        )

    connection_url = (
        f"postgresql+psycopg2://"
        f"{user}:{password}@{host}:{port}/{database}"
    )

    return create_engine(connection_url)


# ============================================================
# INCREMENTAL EXTRACTION
# ============================================================

def get_last_loaded_timestamp(engine):
    """
    Get the latest transaction timestamp already
    loaded into the analytics table.
    """

    query = text("""
        SELECT MAX(transaction_timestamp)
        FROM public.transactions_analytics;
    """)

    with engine.connect() as connection:
        result = connection.execute(query)
        return result.scalar()


def extract_transactions(engine, last_loaded_timestamp=None):
    """
    Extract transactions from PostgreSQL.

    If a previous load exists, only transactions newer
    than the latest loaded timestamp are extracted.
    """

    base_query = """
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
            completed_timestamp,
            failure_reason,
            created_at
        FROM public.transactions
    """

    # First/full load
    if last_loaded_timestamp is None:
        query = base_query + """
            ORDER BY transaction_timestamp;
        """

        return pd.read_sql(query, engine)

    # Incremental load
    query = text(
        base_query
        + """
            WHERE transaction_timestamp > :last_loaded_timestamp
            ORDER BY transaction_timestamp;
        """
    )

    return pd.read_sql(
        query,
        engine,
        params={
            "last_loaded_timestamp": last_loaded_timestamp
        }
    )


# ============================================================
# DATA VALIDATION
# ============================================================

def validate_data(df):
    """
    Run critical data-quality checks.

    The pipeline stops if any critical check fails.
    """

    print("\nDATA QUALITY CHECKS")
    print("-" * 45)

    checks = {
        "Rows": len(df),

        "Duplicate transaction IDs":
            df["transaction_id"].duplicated().sum(),

        "Missing amounts":
            df["amount"].isna().sum(),

        "Invalid amounts":
            (df["amount"] <= 0).sum(),

        "Missing customer IDs":
            df["customer_id"].isna().sum(),

        "Missing merchant IDs":
            df["merchant_id"].isna().sum(),

        "Missing channel IDs":
            df["channel_id"].isna().sum(),

        "Missing partner IDs":
            df["partner_id"].isna().sum(),

        "Missing transaction timestamps":
            df["transaction_timestamp"].isna().sum(),
    }

    for check_name, result in checks.items():
        print(f"{check_name}: {result:,}")

    critical_checks = {
        name: value
        for name, value in checks.items()
        if name != "Rows"
    }

    failures = {
        name: value
        for name, value in critical_checks.items()
        if value > 0
    }

    if failures:
        print("\nDATA QUALITY FAILED")
        print("-" * 45)

        for name, value in failures.items():
            print(f"ERROR: {name} = {value:,}")

        raise ValueError(
            "ETL pipeline stopped because critical "
            "data-quality checks failed."
        )

    print("\nDATA QUALITY PASSED")


# ============================================================
# TRANSFORMATION
# ============================================================

def transform_data(df):
    """
    Clean and enrich transaction data.
    """

    df = df.copy()

    # Convert timestamps
    df["transaction_timestamp"] = pd.to_datetime(
        df["transaction_timestamp"],
        errors="coerce"
    )

    df["completed_timestamp"] = pd.to_datetime(
        df["completed_timestamp"],
        errors="coerce"
    )

    # Calculate processing time
    df["processing_time_minutes"] = (
        (
            df["completed_timestamp"]
            - df["transaction_timestamp"]
        ).dt.total_seconds() / 60
    ).round(2)

    # Status indicators
    df["is_successful"] = (
        df["transaction_status"] == "Successful"
    )

    df["is_failed"] = (
        df["transaction_status"] == "Failed"
    )

    df["is_pending"] = (
        df["transaction_status"] == "Pending"
    )

    df["is_refunded"] = (
        df["transaction_status"] == "Refunded"
    )

    return df


# ============================================================
# LOAD
# ============================================================

def load_processed_data(df, engine):
    """
    Save processed data to CSV and append new rows
    into PostgreSQL.
    """

    output_dir = Path("data/processed")
    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        output_dir / "transactions_processed.csv"
    )

    # Always save a local CSV copy
    df.to_csv(
        output_file,
        index=False
    )

    print(
        f"\nCSV saved to: {output_file}"
    )

    # Nothing to load
    if df.empty:
        print(
            "No new transactions to load into PostgreSQL."
        )
        return 0

    # Append instead of replacing
    df.to_sql(
        "transactions_analytics",
        engine,
        schema="public",
        if_exists="append",
        index=False,
        method="multi"
    )

    print(
        f"Loaded {len(df):,} new transactions "
        "into public.transactions_analytics"
    )

    return len(df)


# ============================================================
# ETL AUDIT LOG
# ============================================================

def log_etl_run(
    engine,
    started_at,
    completed_at,
    rows_extracted,
    rows_loaded,
    quality_status,
    pipeline_status,
    error_message=None,
):
    """
    Write the ETL run result into the audit table.
    """

    query = text("""
        INSERT INTO public.etl_run_log (
            run_started_at,
            run_completed_at,
            rows_extracted,
            rows_loaded,
            data_quality_status,
            pipeline_status,
            error_message
        )
        VALUES (
            :started_at,
            :completed_at,
            :rows_extracted,
            :rows_loaded,
            :quality_status,
            :pipeline_status,
            :error_message
        );
    """)

    with engine.begin() as connection:
        connection.execute(
            query,
            {
                "started_at": started_at,
                "completed_at": completed_at,
                "rows_extracted": rows_extracted,
                "rows_loaded": rows_loaded,
                "quality_status": quality_status,
                "pipeline_status": pipeline_status,
                "error_message": error_message,
            }
        )


# ============================================================
# MAIN ETL PIPELINE
# ============================================================

def main():

    started_at = datetime.now()

    rows_extracted = 0
    rows_loaded = 0

    quality_status = "NOT_RUN"
    pipeline_status = "FAILED"
    error_message = None

    print("=" * 60)
    print("FINPAY ETL PIPELINE")
    print("=" * 60)

    try:

        # ----------------------------------------------------
        # CONNECT
        # ----------------------------------------------------

        print("\nConnecting to PostgreSQL...")

        engine = get_database_engine()

        print("Database connection successful.")

        # ----------------------------------------------------
        # CHECK LAST LOAD
        # ----------------------------------------------------

        print(
            "\n1. Checking latest loaded transaction..."
        )

        last_loaded_timestamp = (
            get_last_loaded_timestamp(engine)
        )

        if last_loaded_timestamp:

            print(
                "Latest loaded timestamp:",
                last_loaded_timestamp
            )

        else:

            print(
                "No previous analytics load found."
            )

        # ----------------------------------------------------
        # EXTRACT
        # ----------------------------------------------------

        print(
            "\n2. Extracting new transactions..."
        )

        transactions = extract_transactions(
            engine,
            last_loaded_timestamp
        )

        rows_extracted = len(transactions)

        print(
            f"New transactions extracted: "
            f"{rows_extracted:,}"
        )

        # ----------------------------------------------------
        # NO NEW DATA
        # ----------------------------------------------------

        if rows_extracted == 0:

            print(
                "\nNo new transactions found."
            )

            quality_status = "NOT_REQUIRED"
            pipeline_status = "SUCCESS"

            return

        # ----------------------------------------------------
        # VALIDATE
        # ----------------------------------------------------

        print(
            "\n3. Validating data..."
        )

        validate_data(transactions)

        quality_status = "PASSED"

        # ----------------------------------------------------
        # TRANSFORM
        # ----------------------------------------------------

        print(
            "\n4. Transforming data..."
        )

        transactions = transform_data(
            transactions
        )

        print(
            "Transformation complete."
        )

        # ----------------------------------------------------
        # LOAD
        # ----------------------------------------------------

        print(
            "\n5. Loading processed data..."
        )

        rows_loaded = load_processed_data(
            transactions,
            engine
        )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        pipeline_status = "SUCCESS"

        print("\n" + "=" * 60)
        print("ETL PIPELINE SUCCESSFUL")
        print("=" * 60)

        print(
            f"Rows extracted: {rows_extracted:,}"
        )

        print(
            f"Rows loaded:    {rows_loaded:,}"
        )

    except Exception as error:

        error_message = str(error)

        print("\n" + "=" * 60)
        print("ETL PIPELINE FAILED")
        print("=" * 60)

        print(
            f"Error: {error_message}"
        )

        raise

    finally:

        completed_at = datetime.now()

        # Only log if database connection exists
        try:

            if "engine" in locals():

                log_etl_run(
                    engine=engine,
                    started_at=started_at,
                    completed_at=completed_at,
                    rows_extracted=rows_extracted,
                    rows_loaded=rows_loaded,
                    quality_status=quality_status,
                    pipeline_status=pipeline_status,
                    error_message=error_message,
                )

                print(
                    "\nETL run logged successfully."
                )

        except Exception as log_error:

            print(
                "\nWARNING: Could not write "
                f"ETL audit log: {log_error}"
            )


# ============================================================
# RUN PIPELINE
# ============================================================

if __name__ == "__main__":
    main()