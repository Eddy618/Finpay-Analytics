"""
FinPay Analytics
E3 - Load model risk scores into PostgreSQL.
"""

from pathlib import Path

import pandas as pd
from sqlalchemy import text

from api.database import engine


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULT_FILE = DATA_DIR / "risk_model_results.csv"


def load_results() -> pd.DataFrame:
    """Load the trained model results from CSV."""
    if not RESULT_FILE.exists():
        raise FileNotFoundError(
            f"Risk results file not found: {RESULT_FILE}"
        )

    dataframe = pd.read_csv(RESULT_FILE)

    if dataframe.empty:
        raise ValueError("Risk results file is empty.")

    return dataframe


def validate_results(dataframe: pd.DataFrame) -> None:
    """Validate the risk results before loading them."""
    required_columns = {
        "transaction_id",
        "risk_score_raw",
        "risk_score",
        "is_anomaly",
        "risk_category",
    }

    missing = required_columns - set(dataframe.columns)

    if missing:
        raise ValueError(
            "Missing risk result columns: "
            + ", ".join(sorted(missing))
        )

    allowed_categories = {
        "Low",
        "Moderate",
        "High",
        "Critical",
    }

    actual_categories = set(
        dataframe["risk_category"]
        .dropna()
        .astype(str)
        .unique()
    )

    invalid_categories = actual_categories - allowed_categories

    if invalid_categories:
        raise ValueError(
            "Invalid risk categories: "
            + ", ".join(sorted(invalid_categories))
        )


def load_to_database(dataframe: pd.DataFrame) -> None:
    """Insert or update risk scores in PostgreSQL."""

    insert_query = text(
        """
        INSERT INTO public.transaction_risk_scores (
            transaction_id,
            risk_score_raw,
            risk_score,
            is_anomaly,
            risk_category,
            model_name,
            model_version
        )
        VALUES (
            CAST(:transaction_id AS UUID),
            :risk_score_raw,
            :risk_score,
            :is_anomaly,
            :risk_category,
            :model_name,
            :model_version
        )
        ON CONFLICT (transaction_id)
        DO UPDATE SET
            risk_score_raw = EXCLUDED.risk_score_raw,
            risk_score = EXCLUDED.risk_score,
            is_anomaly = EXCLUDED.is_anomaly,
            risk_category = EXCLUDED.risk_category,
            model_name = EXCLUDED.model_name,
            model_version = EXCLUDED.model_version,
            scored_at = CURRENT_TIMESTAMP;
        """
    )

    records = []

    for row in dataframe.itertuples(index=False):
        records.append(
            {
                "transaction_id": str(row.transaction_id),
                "risk_score_raw": float(row.risk_score_raw),
                "risk_score": float(row.risk_score),
                "is_anomaly": int(row.is_anomaly),
                "risk_category": str(row.risk_category),
                "model_name": "IsolationForest",
                "model_version": "1.0",
            }
        )

    with engine.begin() as connection:
        connection.execute(insert_query, records)


def main() -> None:
    """Run the risk score loading process."""

    print("=" * 60)
    print("FinPay Analytics - Risk Score Loader")
    print("=" * 60)

    print("\nLoading model results...")

    dataframe = load_results()

    print(f"Loaded {len(dataframe):,} model results.")

    print("\nValidating results...")

    validate_results(dataframe)

    print("Validation passed.")

    print("\nLoading risk scores into PostgreSQL...")

    load_to_database(dataframe)

    print(
        f"Loaded {len(dataframe):,} risk scores successfully."
    )

    with engine.connect() as connection:
        count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM public.transaction_risk_scores;
                """
            )
        ).scalar_one()

    print(
        f"\nDatabase risk score records: {count:,}"
    )

    print("\nRisk score loading completed.")


if __name__ == "__main__":
    main()