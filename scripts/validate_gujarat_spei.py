
from pathlib import Path
import pandas as pd
import numpy as np

# Load dataset
path = Path("data/processed/gujarat_district_spei.csv")
df = pd.read_csv(path, parse_dates=["date"])

print("\n========== SPEI DATA QUALITY VALIDATION ==========")

# 1. Basic information
print("\n1. DATASET OVERVIEW")
print("Total records:", len(df))
print("Unique districts:", df["district"].nunique())
print("Date range:", df["date"].min(), "to", df["date"].max())
print("Columns:", df.columns.tolist())

# 2. District coverage
print("\n2. DISTRICT COVERAGE")
print("Records per district:")
print(df.groupby("district").size().to_string())

# 3. Duplicate checks
print("\n3. DUPLICATE CHECKS")
print(
    "Duplicate district-month records:",
    df.duplicated(["district_id", "date"]).sum()
)

# 4. Missing values
print("\n4. MISSING VALUES")
print(df[["spei_1", "spei_4", "spei_12"]].isna().sum())

# 5. Date validation
print("\n5. DATE VALIDATION")
print("Invalid months:", (~df["month"].between(1, 12)).sum())
print("Invalid years:", df["year"].isna().sum())

# Check monthly continuity per district
gaps = []

for district, group in df.groupby("district"):
    dates = group["date"].sort_values()
    expected = pd.date_range(
        dates.min(), dates.max(), freq="MS"
    )
    missing_dates = expected.difference(dates)

    if len(missing_dates):
        gaps.append((district, len(missing_dates)))

print("Districts with missing months:", len(gaps))
print("Missing month details:", gaps)

# 6. SPEI value ranges
print("\n6. SPEI STATISTICS")
print(df[["spei_1", "spei_4", "spei_12"]].describe())

# 7. Check extreme values
for col in ["spei_1", "spei_4", "spei_12"]:
    print(
        f"{col} outside [-5, 5]:",
        ((df[col] < -5) | (df[col] > 5)).sum()
    )

# 8. SPEI-4 drought classification
def classify_spei(value):
    if pd.isna(value):
        return "Missing"
    if value <= -2:
        return "Extreme drought"
    if value <= -1.5:
        return "Severe drought"
    if value <= -1:
        return "Moderate drought"
    if value >= 2:
        return "Extremely wet"
    if value >= 1.5:
        return "Very wet"
    if value >= 1:
        return "Moderately wet"
    return "Near normal"

df["spei4_category"] = df["spei_4"].apply(classify_spei)

print("\n8. SPEI-4 CATEGORY DISTRIBUTION")
print(df["spei4_category"].value_counts(dropna=False))

# 9. Save validated copy
output = Path("data/processed/gujarat_district_spei_validated.csv")
df.to_csv(output, index=False)

print("\nValidated dataset saved:", output)
print("\n========== VALIDATION COMPLETED ==========")
