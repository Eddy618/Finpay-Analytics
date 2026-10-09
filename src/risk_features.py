"""
FinPay Analytics
Risk Feature Engineering

Reads the PostgreSQL risk feature view, prepares an ML-ready
dataset, and saves the resulting feature matrix locally.
"""

from pathlib import Path

import pandas as pd

from api.database import engine


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"

FEATURE_OUTPUT = DATA_DIR / "risk_features.csv"
SUMMARY_OUTPUT = DATA_DIR / "risk_feature_summary.csv"


# ============================================================
# REQUIRED COLUMNS
# ============================================================

REQUIRED_COLUMNS = {
    "transaction_id",
    "customer_id",
    "merchant_id",
    "channel_id",
    "partner_id",
    "transaction_type",
    "currency",
    "transaction_timestamp",
    "amount",
    "log_amount",
    "transaction_hour",
    "day_of_week",
    "transaction_hour_sin",
    "transaction_hour_cos",
    "day_of_week_sin",
    "day_of_week_cos",
    "customer_tx_count_before",
    "customer_avg_amount_before",
    "customer_std_amount_before",
    "customer_type_count_before",
    "customer_amount_ratio",
    "customer_amount_zscore",
    "merchant_tx_count_before",
    "merchant_avg_amount_before",
    "merchant_amount_ratio",
    "channel_tx_count_before",
    "partner_tx_count_before",
    "is_new_customer",
    "is_new_merchant",
}


# ============================================================
# LOAD FEATURES
# ============================================================

def load_risk_features() -> pd.DataFrame:
    """Load engineered risk features from PostgreSQL."""

    query = """
        SELECT *
        FROM public.vw_risk_features
        ORDER BY transaction_timestamp, transaction_id;
    """

    with engine.connect() as connection:
        dataframe = pd.read_sql(
            query,
            connection,
        )

    return dataframe


# ============================================================
# VALIDATE DATA
# ============================================================

def validate_features(
    dataframe: pd.DataFrame,
) -> None:
    """Validate required columns and basic data quality."""

    missing_columns = (
        REQUIRED_COLUMNS
        - set(dataframe.columns)
    )

    if missing_columns:
        raise ValueError(
            "Missing required feature columns: "
            + ", ".join(
                sorted(missing_columns)
            )
        )

    if dataframe.empty:
        raise ValueError(
            "Risk feature dataset is empty."
        )

    if dataframe["transaction_id"].isna().any():
        raise ValueError(
            "transaction_id contains NULL values."
        )

    if dataframe["amount"].isna().any():
        raise ValueError(
            "amount contains NULL values."
        )

    if (dataframe["amount"] <= 0).any():
        raise ValueError(
            "amount contains non-positive values."
        )


# ============================================================
# PREPARE ML DATASET
# ============================================================

def prepare_ml_features(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare numerical ML features and retain transaction
    metadata separately.

    Transaction type and currency are encoded before the
    remaining metadata columns are removed.
    """

    # --------------------------------------------------------
    # Metadata retained for tracing predictions back to the
    # original transaction.
    # --------------------------------------------------------

    metadata_columns = [
        "transaction_id",
        "customer_id",
        "merchant_id",
        "channel_id",
        "partner_id",
        "transaction_timestamp",
    ]

    metadata = dataframe[
        metadata_columns
    ].copy()

    # --------------------------------------------------------
    # Start with the full feature set, excluding only metadata.
    # --------------------------------------------------------

    model_dataframe = dataframe.drop(
        columns=metadata_columns
    ).copy()

    # --------------------------------------------------------
    # Encode categorical features.
    # --------------------------------------------------------

    categorical_columns = [
        column
        for column in [
            "transaction_type",
            "currency",
        ]
        if column in model_dataframe.columns
    ]

    if categorical_columns:
        model_dataframe = pd.get_dummies(
            model_dataframe,
            columns=categorical_columns,
            prefix=categorical_columns,
            dtype=int,
        )

    # --------------------------------------------------------
    # Replace infinite values.
    # --------------------------------------------------------

    model_dataframe = model_dataframe.replace(
        [float("inf"), float("-inf")],
        pd.NA,
    )

    # --------------------------------------------------------
    # Convert remaining columns to numeric.
    # --------------------------------------------------------

    for column in model_dataframe.columns:

        model_dataframe[column] = pd.to_numeric(
            model_dataframe[column],
            errors="coerce",
        )

    # --------------------------------------------------------
    # Fill missing numeric values.
    # --------------------------------------------------------

    model_dataframe = model_dataframe.fillna(0)

    return metadata, model_dataframe


# ============================================================
# FEATURE SUMMARY
# ============================================================

def build_feature_summary(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Create a summary describing the engineered features."""

    rows = []

    for column in dataframe.columns:

        series = dataframe[column]

        rows.append(
            {
                "feature": column,
                "dtype": str(series.dtype),
                "missing_values": int(
                    series.isna().sum()
                ),
                "unique_values": int(
                    series.nunique()
                ),
                "min": float(series.min()),
                "max": float(series.max()),
                "mean": float(series.mean()),
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    print("=" * 60)
    print("FinPay Analytics - Risk Feature Engineering")
    print("=" * 60)

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("\nLoading risk features from PostgreSQL...")

    dataframe = load_risk_features()

    print(
        f"Loaded {len(dataframe):,} transactions."
    )

    print("\nValidating feature dataset...")

    validate_features(dataframe)

    print("Validation passed.")

    print("\nPreparing ML feature matrix...")

    metadata, model_dataframe = (
        prepare_ml_features(dataframe)
    )

    output_dataframe = pd.concat(
        [
            metadata.reset_index(drop=True),
            model_dataframe.reset_index(drop=True),
        ],
        axis=1,
    )

    output_dataframe.to_csv(
        FEATURE_OUTPUT,
        index=False,
    )

    summary = build_feature_summary(
        model_dataframe
    )

    summary.to_csv(
        SUMMARY_OUTPUT,
        index=False,
    )

    print(
        f"\nFeature dataset saved to:\n"
        f"{FEATURE_OUTPUT}"
    )

    print(
        f"\nFeature summary saved to:\n"
        f"{SUMMARY_OUTPUT}"
    )

    print(
        "\nML feature matrix shape:"
        f" {model_dataframe.shape}"
    )

    print("\nFeatures:")
    for feature in model_dataframe.columns:
        print(f"  - {feature}")

    print(
        "\nRisk feature engineering completed."
    )


if __name__ == "__main__":
    main()