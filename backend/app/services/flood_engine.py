
from pathlib import Path
from functools import lru_cache
import json

import joblib
import numpy as np
import pandas as pd


# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[3]

DATA_FILE = (
    BASE_DIR
    / "Data"
    / "Processed"
    / "daily_rainfall"
    / "gujarat_district_flood_features.csv"
)

MODEL_FILE = BASE_DIR / "ml" / "models" / "flood_xgb_model.joblib"
METRICS_FILE = BASE_DIR / "ml" / "models" / "flood_model_metrics.json"

MODEL_FEATURES = [
    "rainfall_mm",
    "rainfall_3d_mm",
    "rainfall_7d_mm",
    "rainfall_30d_mm",
    "month",
    "district"
]


# --------------------------------------------------
# 1. LOAD TRAINED MODEL
# --------------------------------------------------

@lru_cache(maxsize=1)
def load_flood_model():

    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            f"Flood model not found: {MODEL_FILE}"
        )

    if not METRICS_FILE.exists():
        raise FileNotFoundError(
            f"Flood model metrics not found: {METRICS_FILE}"
        )

    model = joblib.load(MODEL_FILE)

    with open(METRICS_FILE, "r", encoding="utf-8") as file:
        metrics = json.load(file)

    threshold = float(metrics["decision_threshold"])

    return model, threshold, metrics


# --------------------------------------------------
# 2. LOAD DISTRICT DATA
# --------------------------------------------------

def get_flood_data(district=None):

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Flood dataset not found: {DATA_FILE}"
        )

    required_columns = [
        "district",
        "date",
        "rainfall_mm",
        "rainfall_1d_mm",
        "rainfall_3d_mm",
        "rainfall_7d_mm",
        "rainfall_30d_mm",
        "rainfall_anomaly",
        "rainfall_intensity",
        "month"
    ]

    df = pd.read_csv(
        DATA_FILE,
        usecols=required_columns
    )

    df["district"] = df["district"].astype(str).str.strip()

    if district:
        df = df[
            df["district"].str.upper() == district.strip().upper()
        ].copy()

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    numeric_columns = [
        "rainfall_mm",
        "rainfall_1d_mm",
        "rainfall_3d_mm",
        "rainfall_7d_mm",
        "rainfall_30d_mm",
        "rainfall_anomaly",
        "month"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    df = df.dropna(
        subset=["district", "date"]
    )

    return df.sort_values(
        ["district", "date"]
    ).reset_index(drop=True)


# --------------------------------------------------
# 3. RULE-BASED FLOOD RISK CALCULATION
# --------------------------------------------------

def calculate_flood_scores(df):

    df = df.copy()

    required = [
        "rainfall_1d_mm",
        "rainfall_3d_mm",
        "rainfall_7d_mm",
        "rainfall_30d_mm"
    ]

    valid = df[required].notna().all(axis=1)

    score = pd.Series(
        0,
        index=df.index,
        dtype="int64"
    )

    r1 = df["rainfall_1d_mm"]
    r3 = df["rainfall_3d_mm"]
    r7 = df["rainfall_7d_mm"]
    r30 = df["rainfall_30d_mm"]
    anomaly = df["rainfall_anomaly"]

    # Daily rainfall
    score += np.select(
        [r1 >= 204.5, r1 >= 115.6, r1 >= 64.4, r1 >= 15.6],
        [40, 30, 20, 10],
        default=0
    )

    # 3-day rainfall
    score += np.select(
        [r3 >= 200, r3 >= 150, r3 >= 100],
        [25, 20, 10],
        default=0
    )

    # 7-day rainfall
    score += np.select(
        [r7 >= 350, r7 >= 250, r7 >= 150],
        [20, 15, 10],
        default=0
    )

    # 30-day rainfall
    score += np.select(
        [r30 >= 500, r30 >= 300],
        [10, 5],
        default=0
    )

    # Rainfall anomaly
    score += (
        (anomaly >= 2).fillna(False).astype(int) * 5
    )

    df["risk_score"] = score.astype(object)
    df.loc[~valid, "risk_score"] = None

    df["risk_level"] = np.select(
        [
            valid & (score >= 70),
            valid & (score >= 50),
            valid & (score >= 30)
        ],
        [
            "Very High",
            "High",
            "Moderate"
        ],
        default="Low"
    )

    df.loc[
        ~valid,
        "risk_level"
    ] = "Insufficient Data"

    return df


# --------------------------------------------------
# 4. XGBOOST NEXT-DAY EXTREME RAINFALL PREDICTION
# --------------------------------------------------

def predict_next_day_extreme_rainfall(df):

    result = df.copy()

    result["extreme_rainfall_model_score"] = None
    result["extreme_rainfall_warning"] = None
    result["model_decision_threshold"] = None

    if result.empty:
        return result

    try:
        model, threshold, metrics = load_flood_model()

        valid = result[MODEL_FEATURES].notna().all(axis=1)

        if not valid.any():
            return result

        X = result.loc[valid, MODEL_FEATURES].copy()

        scores = model.predict_proba(X)[:, 1]

        result.loc[
            valid,
            "extreme_rainfall_model_score"
        ] = np.round(scores * 100, 2)

        result.loc[
            valid,
            "extreme_rainfall_warning"
        ] = scores >= threshold

        result.loc[
            valid,
            "model_decision_threshold"
        ] = threshold

    except Exception as error:
        print(f"Flood ML prediction error: {error}")

    return result


# --------------------------------------------------
# 5. LATEST DISTRICT-WISE FLOOD RISK
# --------------------------------------------------

def get_latest_flood_risk():

    df = get_flood_data()

    latest_date = df["date"].max()

    latest = df[
        df["date"] == latest_date
    ].copy()

    latest = calculate_flood_scores(latest)

    # Add next-day ML predictions
    latest = predict_next_day_extreme_rainfall(latest)

    latest["date"] = latest["date"].dt.strftime(
        "%Y-%m-%d"
    )

    results = latest[
        [
            "district",
            "date",
            "rainfall_1d_mm",
            "rainfall_3d_mm",
            "rainfall_7d_mm",
            "rainfall_30d_mm",
            "risk_score",
            "risk_level",
            "extreme_rainfall_model_score",
            "extreme_rainfall_warning",
            "model_decision_threshold"
        ]
    ].copy()

    results = results.sort_values(
        "risk_score",
        ascending=False,
        na_position="last"
    )

    results = results.replace(
        [np.inf, -np.inf, np.nan],
        None
    )

    try:
        _, threshold, metrics = load_flood_model()
        model_status = {
            "available": True,
            "name": "XGBoost Classifier",
            "decision_threshold": threshold,
            "test_f1": metrics.get("test_f1"),
            "test_pr_auc": metrics.get("test_pr_auc"),
            "prediction_target": (
                "Next-day rainfall exceeding district-specific "
                "training-period 95th percentile"
            ),
            "warning": (
                "Extreme-rainfall proxy, not verified flood occurrence "
                "or calibrated flood probability."
            )
        }

    except Exception as error:
        model_status = {
            "available": False,
            "error": str(error)
        }

    return {
        "latest_date": latest_date.strftime("%Y-%m-%d"),
        "total_districts": len(results),
        "model_status": model_status,
        "districts": results.to_dict(orient="records")
    }


# --------------------------------------------------
# 6. HISTORICAL FLOOD RISK
# --------------------------------------------------

def get_flood_history(district, days=90):

    if days < 1 or days > 3650:
        raise ValueError(
            "Days must be between 1 and 3650"
        )

    df = get_flood_data(district)

    if df.empty:
        return None

    latest_date = df["date"].max()

    start_date = latest_date - pd.Timedelta(
        days=days - 1,
        unit="D"
    )

    df = df[
        df["date"] >= start_date
    ].copy()

    df = calculate_flood_scores(df)

    df["date"] = df["date"].dt.strftime(
        "%Y-%m-%d"
    )

    output_columns = [
        "date",
        "rainfall_1d_mm",
        "rainfall_3d_mm",
        "rainfall_7d_mm",
        "risk_score",
        "risk_level"
    ]

    result = df[output_columns].replace(
        [np.inf, -np.inf, np.nan],
        None
    )

    return {
        "district": district.upper(),
        "period_days": days,
        "records": len(result),
        "history": result.to_dict(orient="records")
    }
