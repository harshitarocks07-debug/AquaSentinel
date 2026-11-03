
import pandas as pd
from pathlib import Path

data_dir = Path("data/processed/daily_rainfall")

files = [
    "gujarat_district_daily_rainfall_1981.csv",
    "gujarat_district_daily_rainfall_1982.csv",
    "gujarat_district_daily_rainfall_1983_1992.csv",
    "gujarat_district_daily_rainfall_1993_2002.csv",
    "gujarat_district_daily_rainfall_2003_2012.csv",
    "gujarat_district_daily_rainfall_2013_2022.csv",
    "gujarat_district_daily_rainfall_2023_2026.csv"
]

frames = []

for filename in files:
    path = data_dir / filename

    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    print("Loading:", filename)
    frames.append(pd.read_csv(path))

# Combine all datasets
df = pd.concat(frames, ignore_index=True)

# Standardize dates and data types
df["date"] = pd.to_datetime(df["date"])
df["district"] = df["district"].astype(str).str.strip()
df["rainfall_mm"] = pd.to_numeric(df["rainfall_mm"], errors="coerce")

# Sort records
df = df.sort_values(["district", "date"]).reset_index(drop=True)

# Check duplicate district-date records
duplicates = df.duplicated(["district", "date"]).sum()

if duplicates > 0:
    raise ValueError(f"Found {duplicates} duplicate district-date records.")

# Save master dataset
output_path = data_dir / "gujarat_district_daily_rainfall_master.csv"
df.to_csv(output_path, index=False)

print("\nMASTER DATASET CREATED")
print("Rows:", len(df))
print("Districts:", df["district"].nunique())
print("Unique dates:", df["date"].nunique())
print("First date:", df["date"].min())
print("Last date:", df["date"].max())
print("Missing values:\n", df.isna().sum())
print("Duplicates:", duplicates)
print("Saved to:", output_path)
