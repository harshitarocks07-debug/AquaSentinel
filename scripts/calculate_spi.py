
import pandas as pd
import numpy as np
from scipy.stats import gamma, norm
import os

INPUT_FILE = "data/processed/gujarat_district_monthly_rainfall.csv"
OUTPUT_FILE = "data/processed/gujarat_district_spi.csv"

# Load data
df = pd.read_csv(INPUT_FILE)

# Rename rainfall column
df = df.rename(columns={"mean": "rainfall_mm"})

# Clean data
df["date"] = pd.to_datetime(df["date"])
df["rainfall_mm"] = pd.to_numeric(
    df["rainfall_mm"], errors="coerce"
)

df = df.dropna(subset=["rainfall_mm", "district"])
df = df.sort_values(["district", "date"])

# Three-month accumulated rainfall
df["rainfall_3month"] = (
    df.groupby("district")["rainfall_mm"]
    .transform(lambda x: x.rolling(3, min_periods=3).sum())
)

# SPI-3 calculation
def calculate_spi(group):

    group = group.copy()
    group["spi_3"] = np.nan

    # Calculate separately for each calendar month
    for month in range(1, 13):

        mask = (
            (group["date"].dt.month == month)
            & group["rainfall_3month"].notna()
        )

        values = group.loc[mask, "rainfall_3month"]

        if len(values) < 20:
            continue

        # Gamma distribution is fitted to positive rainfall
        positive = values[values > 0]

        if len(positive) < 20:
            continue

        try:
            shape, loc, scale = gamma.fit(
                positive, floc=0
            )

            zero_probability = (values == 0).mean()

            probabilities = np.where(
                values == 0,
                zero_probability / 2,
                zero_probability
                + (1 - zero_probability)
                * gamma.cdf(
                    values,
                    shape,
                    loc=0,
                    scale=scale
                )
            )

            probabilities = np.clip(
                probabilities, 0.0001, 0.9999
            )

            group.loc[mask, "spi_3"] = norm.ppf(
                probabilities
            )

        except (ValueError, FloatingPointError):
            print(
                f"Could not calculate SPI for "
                f"{group['district'].iloc[0]}, month {month}"
            )

    return group


# Apply calculation district-wise
# Apply SPI calculation separately to each district
district_results = []

for district_name, district_data in df.groupby("district"):

    processed = calculate_spi(district_data.copy())

    # Explicitly preserve district name
    processed["district"] = district_name

    district_results.append(processed)

result = pd.concat(
    district_results,
    ignore_index=True
)

# Classify drought severity
def classify_spi(value):

    if pd.isna(value):
        return "Insufficient data"
    elif value <= -2.0:
        return "Extreme drought"
    elif value <= -1.5:
        return "Severe drought"
    elif value <= -1.0:
        return "Moderate drought"
    elif value >= 2.0:
        return "Extremely wet"
    elif value >= 1.5:
        return "Very wet"
    elif value >= 1.0:
        return "Moderately wet"
    else:
        return "Near normal"


result["drought_status"] = result["spi_3"].apply(
    classify_spi
)

# Save results
os.makedirs("data/processed", exist_ok=True)

result.to_csv(OUTPUT_FILE, index=False)

print("SPI calculation completed.")
print("Dataset shape:", result.shape)
print("Districts:", result["district"].nunique())
print("SPI values available:", result["spi_3"].notna().sum())
print("Saved to:", OUTPUT_FILE)

print("\nLatest district drought status:")

latest = (
    result.dropna(subset=["spi_3"])
    .sort_values("date")
    .groupby("district")
    .tail(1)
)

print(
    latest[
        ["district", "date", "rainfall_3month",
         "spi_3", "drought_status"]
    ].to_string(index=False)
)
