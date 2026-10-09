"""
FinPay Analytics
E2 - Train and evaluate an Isolation Forest risk model.
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"

FEATURE_FILE = DATA_DIR / "risk_features.csv"
MODEL_FILE = DATA_DIR / "risk_model.joblib"
SCALER_FILE = DATA_DIR / "risk_scaler.joblib"
RESULT_FILE = DATA_DIR / "risk_model_results.csv"


# ============================================================
# MODEL FEATURES
# ============================================================

METADATA_COLUMNS = [
    "transaction_id",
    "customer_id",
    "merchant_id",
    "channel_id",
    "partner_id",
    "transaction_timestamp",
]


# ============================================================
# LOAD DATA
# ============================================================

def load_feature_data() -> pd.DataFrame:
    """Load the engineered risk dataset."""

    if not FEATURE_FILE.exists():
        raise FileNotFoundError(
            f"Feature file not found: {FEATURE_FILE}"
        )

    dataframe = pd.read_csv(
        FEATURE_FILE
    )

    if dataframe.empty:
        raise ValueError(
            "Risk feature dataset is empty."
        )

    return dataframe


# ============================================================
# PREPARE FEATURES
# ============================================================

def prepare_features(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:

    metadata_columns = [
        column
        for column in METADATA_COLUMNS
        if column in dataframe.columns
    ]

    metadata = dataframe[
        metadata_columns
    ].copy()

    feature_dataframe = dataframe.drop(
        columns=metadata_columns
    ).copy()

    # Ensure every model feature is numeric.
    for column in feature_dataframe.columns:
        feature_dataframe[column] = pd.to_numeric(
            feature_dataframe[column],
            errors="coerce",
        )

    feature_dataframe = feature_dataframe.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    feature_dataframe = feature_dataframe.fillna(0)

    return metadata, feature_dataframe


# ============================================================
# TRAIN MODEL
# ============================================================

def train_model(
    feature_dataframe: pd.DataFrame,
) -> tuple[IsolationForest, StandardScaler, np.ndarray]:

    scaler = StandardScaler()

    scaled_features = scaler.fit_transform(
        feature_dataframe
    )

    model = IsolationForest(
        n_estimators=300,
        contamination=0.05,
        max_samples="auto",
        random_state=42,
        n_jobs=-1,
    )

    model.fit(
        scaled_features
    )

    predictions = model.predict(
        scaled_features
    )

    scores = model.decision_function(
        scaled_features
    )

    return (
        model,
        scaler,
        predictions,
        scores,
    )


# ============================================================
# BUILD RESULTS
# ============================================================

def build_results(
    metadata: pd.DataFrame,
    predictions: np.ndarray,
    scores: np.ndarray,
) -> pd.DataFrame:

    results = metadata.copy()

    results["risk_score_raw"] = scores

    results["is_anomaly"] = (
        predictions == -1
    ).astype(int)

    # Convert the model's decision function into a more
    # intuitive 0-100 risk score.
    #
    # Lower decision-function values are more abnormal.
    score_min = scores.min()
    score_max = scores.max()

    if score_max == score_min:
        results["risk_score"] = 0.0
    else:
        results["risk_score"] = (
            100
            * (
                score_max - scores
            )
            / (
                score_max - score_min
            )
        )

    results["risk_category"] = pd.cut(
        results["risk_score"],
        bins=[
            -0.01,
            25,
            50,
            75,
            100.01,
        ],
        labels=[
            "Low",
            "Moderate",
            "High",
            "Critical",
        ],
        include_lowest=True,
    )

    return results


# ============================================================
# EVALUATION SUMMARY
# ============================================================

def create_summary(
    results: pd.DataFrame,
    feature_dataframe: pd.DataFrame,
) -> None:

    total_records = len(results)

    anomaly_count = int(
        results["is_anomaly"].sum()
    )

    anomaly_rate = (
        anomaly_count / total_records
        if total_records
        else 0
    )

    print("\n" + "=" * 60)
    print("MODEL EVALUATION")
    print("=" * 60)

    print(
        f"Transactions scored: {total_records:,}"
    )

    print(
        f"Features used: {feature_dataframe.shape[1]}"
    )

    print(
        f"Detected anomalies: {anomaly_count:,}"
    )

    print(
        f"Anomaly rate: {anomaly_rate:.2%}"
    )

    print("\nRisk category distribution:")

    print(
        results["risk_category"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\nRisk score statistics:")

    print(
        results["risk_score"]
        .describe()
        .round(2)
        .to_string()
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print("=" * 60)
    print("FinPay Analytics - Risk Model Training")
    print("=" * 60)

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("\nLoading feature dataset...")

    dataframe = load_feature_data()

    print(
        f"Loaded {len(dataframe):,} records."
    )

    print("\nPreparing model features...")

    metadata, feature_dataframe = (
        prepare_features(dataframe)
    )

    print(
        f"Prepared {feature_dataframe.shape[1]} "
        f"numerical features."
    )

    print("\nTraining Isolation Forest...")

    (
        model,
        scaler,
        predictions,
        scores,
    ) = train_model(
        feature_dataframe
    )

    print("Model training completed.")

    print("\nGenerating risk scores...")

    results = build_results(
        metadata,
        predictions,
        scores,
    )

    results.to_csv(
        RESULT_FILE,
        index=False,
    )

    joblib.dump(
        model,
        MODEL_FILE,
    )

    joblib.dump(
        scaler,
        SCALER_FILE,
    )

    create_summary(
        results,
        feature_dataframe,
    )

    print(
        f"\nModel saved to:\n{MODEL_FILE}"
    )

    print(
        f"Scaler saved to:\n{SCALER_FILE}"
    )

    print(
        f"Results saved to:\n{RESULT_FILE}"
    )

    print("\nRisk model training completed.")


if __name__ == "__main__":
    main()