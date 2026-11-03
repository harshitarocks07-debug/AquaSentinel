
import pandas as pd
import numpy as np
from pathlib import Path

# =========================================
# 1. LOAD MASTER DATASET
# =========================================

input_path = Path(
    "data/processed/daily_rainfall/"
    "gujarat_district_daily_rainfall_master.csv"
)

output_path = Path(
    "data/processed/daily_rainfall/"
    "gujarat_district_flood_features.csv"
)

df = pd.read_csv(input_path)

df["date"] = pd.to_datetime(df["date"])
df["rainfall_mm"] = pd.to_numeric(
    df["rainfall_mm"], errors="coerce"
)

df = df.sort_values(
    ["district", "date"]
).reset_index(drop=True)

# =========================================
# 2. VALIDATE INPUT
# =========================================

if df[["district", "date", "rainfall_mm"]].isna().any().any():
    raise ValueError("Input contains missing required values.")

if df.duplicated(["district", "date"]).any():
    raise ValueError("Duplicate district-date records found.")

# Ensure daily continuity within every district
for district, group in df.groupby("district"):
    expected_dates = pd.date_range(
        group["date"].min(),
        group["date"].max(),
        freq="D"
    )

    if len(group) != len(expected_dates) or not group["date"].reset_index(drop=True).equals(
        pd.Series(expected_dates, name="date")
    ):
        raise ValueError(
            f"Missing or irregular daily dates in {district}."
        )

print("Input validation successful.")

# =========================================
# 3. ROLLING RAINFALL FEATURES
# =========================================

grouped = df.groupby("district", sort=False)["rainfall_mm"]

df["rainfall_1d_mm"] = grouped.transform(
    lambda x: x.rolling(1, min_periods=1).sum()
)

df["rainfall_3d_mm"] = grouped.transform(
    lambda x: x.rolling(3, min_periods=3).sum()
)

df["rainfall_7d_mm"] = grouped.transform(
    lambda x: x.rolling(7, min_periods=7).sum()
)

df["rainfall_30d_mm"] = grouped.transform(
    lambda x: x.rolling(30, min_periods=30).sum()
)

# =========================================
# 4. HISTORICAL RAINFALL ANOMALY
# =========================================

# Compare each day's rainfall with the historical
# average for the same calendar month and district.

df["month"] = df["date"].dt.month

monthly_avg = (
    df.groupby(["district", "month"])["rainfall_mm"]
    .transform("mean")
)

monthly_std = (
    df.groupby(["district", "month"])["rainfall_mm"]
    .transform("std")
)

df["rainfall_anomaly"] = (
    (df["rainfall_mm"] - monthly_avg)
    / monthly_std.replace(0, np.nan)
)

# =========================================
# 5. RAINFALL INTENSITY CATEGORY
# =========================================

df["rainfall_intensity"] = pd.cut(
    df["rainfall_mm"],
    bins=[-np.inf, 2.5, 15.6, 64.4, 115.6, 204.5, np.inf],
    labels=[
        "Very Light",
        "Light",
        "Moderate",
        "Heavy",
        "Very Heavy",
        "Extremely Heavy"
    ]
)

# =========================================
# 6. SAVE FEATURES
# =========================================

df.to_csv(output_path, index=False)

print("\nFLOOD FEATURES CREATED")
print("Total rows:", len(df))
print("Districts:", df["district"].nunique())
print("Date range:", df["date"].min(), "to", df["date"].max())
print("Missing values:\n", df.isna().sum())
print("Saved to:", output_path)
