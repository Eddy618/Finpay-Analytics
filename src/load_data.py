import os
import pandas as pd

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# ============================================================
# FINPAY ANALYTICS - ETL PIPELINE
# ============================================================

print("================================")
print("       FINPAY ETL PIPELINE")
print("================================")


# ============================================================
# 1. LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


# Check environment variables
required_variables = {
    "DB_HOST": DB_HOST,
    "DB_PORT": DB_PORT,
    "DB_NAME": DB_NAME,
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
}

missing_variables = [
    name
    for name, value in required_variables.items()
    if not value
]

if missing_variables:
    raise ValueError(
        f"Missing database settings in .env: "
        f"{', '.join(missing_variables)}"
    )


# ============================================================
# 2. DATABASE CONNECTION
# ============================================================

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


# ============================================================
# 3. TEST DATABASE CONNECTION
# ============================================================

def test_connection():

    print("\nTesting PostgreSQL connection...")

    with engine.connect() as connection:

        result = connection.execute(
            text("SELECT 1")
        )

        result.fetchone()

    print("PostgreSQL connection successful!")


# ============================================================
# 4. LOAD CUSTOMERS
# ============================================================

def load_customers():

    print("\nLoading customers...")

    file_path = "data/raw/customers.csv"

    if not os.path.exists(file_path):

        raise FileNotFoundError(
            f"Customer file not found: {file_path}"
        )

    df = pd.read_csv(file_path)

    # --------------------------------------------------------
    # Check required columns
    # --------------------------------------------------------

    required_columns = [
        "customer_id",
        "first_name",
        "last_name",
        "email",
        "phone",
        "country",
        "city",
        "customer_type",
        "registration_date"
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            f"Customers CSV is missing columns: {missing}"
        )

    # --------------------------------------------------------
    # Remove duplicate emails inside the CSV
    # --------------------------------------------------------

    df = df.drop_duplicates(
        subset=["email"],
        keep="first"
    )

    # --------------------------------------------------------
    # Remove records that already exist
    # --------------------------------------------------------

    existing_ids = pd.read_sql(
        "SELECT customer_id FROM customers",
        engine
    )

    if not existing_ids.empty:

        df = df[
            ~df["customer_id"].isin(
                existing_ids["customer_id"]
            )
        ]

    # --------------------------------------------------------
    # Insert
    # --------------------------------------------------------

    if df.empty:

        print("Customers: nothing new to load.")
        return

    df.to_sql(
        "customers",
        engine,
        if_exists="append",
        index=False,
        chunksize=500
    )

    print(
        f"Customers loaded: {len(df)}"
    )


# ============================================================
# 5. LOAD MERCHANTS
# ============================================================

def load_merchants():

    print("\nLoading merchants...")

    file_path = "data/raw/merchants.csv"

    if not os.path.exists(file_path):

        raise FileNotFoundError(
            f"Merchant file not found: {file_path}"
        )

    df = pd.read_csv(file_path)

    required_columns = [
        "merchant_id",
        "merchant_name",
        "business_type",
        "country",
        "registration_date",
        "merchant_status"
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            f"Merchants CSV is missing columns: {missing}"
        )

    # --------------------------------------------------------
    # Remove duplicate merchant IDs
    # --------------------------------------------------------

    df = df.drop_duplicates(
        subset=["merchant_id"],
        keep="first"
    )

    # --------------------------------------------------------
    # Remove existing merchants
    # --------------------------------------------------------

    existing_ids = pd.read_sql(
        "SELECT merchant_id FROM merchants",
        engine
    )

    if not existing_ids.empty:

        df = df[
            ~df["merchant_id"].isin(
                existing_ids["merchant_id"]
            )
        ]

    if df.empty:

        print("Merchants: nothing new to load.")
        return

    df.to_sql(
        "merchants",
        engine,
        if_exists="append",
        index=False,
        chunksize=500
    )

    print(
        f"Merchants loaded: {len(df)}"
    )


# ============================================================
# 6. LOAD TRANSACTIONS
# ============================================================

def load_transactions():

    print("\nLoading transactions...")

    file_path = "data/raw/transactions.csv"

    if not os.path.exists(file_path):

        raise FileNotFoundError(
            f"Transaction file not found: {file_path}"
        )

    df = pd.read_csv(file_path)

    print(
        f"Transaction CSV records found: {len(df)}"
    )

    # --------------------------------------------------------
    # Required source columns
    # --------------------------------------------------------

    required_columns = [
        "transaction_id",
        "customer_id",
        "merchant_id",
        "channel",
        "partner",
        "transaction_type",
        "transaction_status",
        "amount",
        "currency",
        "transaction_timestamp",
        "completed_timestamp",
        "failure_reason"
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            f"Transactions CSV is missing columns: {missing}"
        )

    # --------------------------------------------------------
    # Remove duplicate transaction IDs
    # --------------------------------------------------------

    df = df.drop_duplicates(
        subset=["transaction_id"],
        keep="first"
    )

    # --------------------------------------------------------
    # Load payment channel lookup
    # --------------------------------------------------------

    channels = pd.read_sql(
        """
        SELECT
            channel_id,
            channel_name
        FROM payment_channels
        """,
        engine
    )

    if channels.empty:

        raise ValueError(
            "payment_channels table is empty."
        )

    # --------------------------------------------------------
    # Load partner lookup
    # --------------------------------------------------------

    partners = pd.read_sql(
        """
        SELECT
            partner_id,
            partner_name
        FROM partners
        """,
        engine
    )

    if partners.empty:

        raise ValueError(
            "partners table is empty."
        )

    # --------------------------------------------------------
    # Map channel name → channel ID
    # --------------------------------------------------------

    df = df.merge(
        channels,
        left_on="channel",
        right_on="channel_name",
        how="left"
    )

    # --------------------------------------------------------
    # Map partner name → partner ID
    # --------------------------------------------------------

    df = df.merge(
        partners,
        left_on="partner",
        right_on="partner_name",
        how="left"
    )

    # --------------------------------------------------------
    # Validate mappings
    # --------------------------------------------------------

    unmapped_channels = df[
        df["channel_id"].isna()
    ]["channel"].unique()

    if len(unmapped_channels) > 0:

        raise ValueError(
            "Unmapped payment channels: "
            f"{list(unmapped_channels)}"
        )

    unmapped_partners = df[
        df["partner_id"].isna()
    ]["partner"].unique()

    if len(unmapped_partners) > 0:

        raise ValueError(
            "Unmapped partners: "
            f"{list(unmapped_partners)}"
        )

    # --------------------------------------------------------
    # Check customer IDs
    # --------------------------------------------------------

    customers = pd.read_sql(
        """
        SELECT customer_id
        FROM customers
        """,
        engine
    )

    df = df[
        df["customer_id"].isin(
            customers["customer_id"]
        )
    ]

    # --------------------------------------------------------
    # Check merchant IDs
    # --------------------------------------------------------

    merchants = pd.read_sql(
        """
        SELECT merchant_id
        FROM merchants
        """,
        engine
    )

    df = df[
        df["merchant_id"].isin(
            merchants["merchant_id"]
        )
    ]

    # --------------------------------------------------------
    # Remove transactions already in database
    # --------------------------------------------------------

    existing_transactions = pd.read_sql(
        """
        SELECT transaction_id
        FROM transactions
        """,
        engine
    )

    if not existing_transactions.empty:

        df = df[
            ~df["transaction_id"].isin(
                existing_transactions["transaction_id"]
            )
        ]

    # --------------------------------------------------------
    # Select database columns
    # --------------------------------------------------------

    df = df[
        [
            "transaction_id",
            "customer_id",
            "merchant_id",
            "channel_id",
            "partner_id",
            "transaction_type",
            "transaction_status",
            "amount",
            "currency",
            "transaction_timestamp",
            "completed_timestamp",
            "failure_reason"
        ]
    ]

    # --------------------------------------------------------
    # Convert timestamps
    # --------------------------------------------------------

    df["transaction_timestamp"] = pd.to_datetime(
        df["transaction_timestamp"],
        errors="coerce"
    )

    df["completed_timestamp"] = pd.to_datetime(
        df["completed_timestamp"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Remove invalid dates
    # --------------------------------------------------------

    invalid_dates = df[
        df["transaction_timestamp"].isna()
    ]

    if not invalid_dates.empty:

        print(
            f"Warning: removing "
            f"{len(invalid_dates)} transactions "
            f"with invalid timestamps."
        )

        df = df[
            df["transaction_timestamp"].notna()
        ]

    # --------------------------------------------------------
    # Load transactions
    # --------------------------------------------------------

    if df.empty:

        print(
            "Transactions: nothing new to load."
        )

        return

    print(
        f"Preparing {len(df)} transactions..."
    )

    df.to_sql(
        "transactions",
        engine,
        if_exists="append",
        index=False,
        chunksize=500
    )

    print(
        f"Transactions loaded: {len(df)}"
    )


# ============================================================
# 7. VERIFY DATA
# ============================================================

def verify_data():

    print("\n================================")
    print("       DATA VERIFICATION")
    print("================================")

    queries = {
        "Customers": "SELECT COUNT(*) FROM customers",
        "Merchants": "SELECT COUNT(*) FROM merchants",
        "Transactions": "SELECT COUNT(*) FROM transactions",
        "Payment Channels": "SELECT COUNT(*) FROM payment_channels",
        "Partners": "SELECT COUNT(*) FROM partners"
    }

    with engine.connect() as connection:

        for name, query in queries.items():

            result = connection.execute(
                text(query)
            )

            count = result.scalar()

            print(
                f"{name}: {count}"
            )


# ============================================================
# 8. MAIN ETL PROCESS
# ============================================================

def main():

    try:

        test_connection()

        load_customers()

        load_merchants()

        load_transactions()

        verify_data()

        print("\n================================")
        print("     ETL COMPLETED SUCCESSFULLY")
        print("================================")

    except Exception as error:

        print("\n================================")
        print("          ETL FAILED")
        print("================================")

        print(
            f"\nError: {error}"
        )

        raise


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":

    main()