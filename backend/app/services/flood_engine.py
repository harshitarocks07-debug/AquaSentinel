
from pathlib import Path
import pandas as pd
import numpy as np


BASE_DIR = Path(__file__).resolve().parents[3]

DATA_FILE = (
    BASE_DIR
    / "Data"
    / "Processed"
    / "daily_rainfall"
    / "gujarat_district_flood_features.csv"
)


# --------------------------------------------------
# 1. Load only required district data
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
        "rainfall_intensity"
    ]

    # Read only the required columns
    df = pd.read_csv(
        DATA_FILE,
        usecols=required_columns
    )

    if district:
        df = df[
            df["district"].str.upper() == district.upper()
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
        "rainfall_anomaly"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    df = df.dropna(
        subset=["district", "date"]
    )

    return df.sort_values("date")


# --------------------------------------------------
# 2. Vectorized flood risk calculation
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

    df["risk_score"] = score.clip(upper=100).astype(object)
    df.loc[~valid, "risk_score"] = None

    df["risk_level"] = np.select(
        [
            df["risk_score"].notna() & (score >= 70),
            df["risk_score"].notna() & (score >= 50),
            df["risk_score"].notna() & (score >= 30)
        ],
        [
            "Very High",
            "High",
            "Moderate"
        ],
        default="Low"
    )

    df.loc[~valid, "risk_level"] = "Insufficient Data"

    return df


# --------------------------------------------------
# 3. Latest flood risk across districts
# --------------------------------------------------

def get_latest_flood_risk():

    df = get_flood_data()

    latest_date = df["date"].max()

    latest = df[
        df["date"] == latest_date
    ].copy()

    latest = calculate_flood_scores(latest)

    latest["date"] = latest["date"].dt.strftime(
        "%Y-%m-%d"
    )

    latest = latest.replace(
        [np.inf, -np.inf, np.nan],
        None
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
            "risk_level"
        ]
    ].sort_values(
        "risk_score",
        ascending=False,
        na_position="last"
    )

    return {
        "latest_date": latest_date.strftime("%Y-%m-%d"),
        "total_districts": len(results),
        "districts": results.to_dict(orient="records")
    }


# --------------------------------------------------
# 4. Historical flood risk with date limit
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
