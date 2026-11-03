
from pathlib import Path
import pandas as pd
import re

# Input and output paths
source_dir = Path("data/raw/drought_atlas_gujarat_districts")
output_dir = Path("data/processed")
output_dir.mkdir(parents=True, exist_ok=True)

mapping_file = source_dir / "gujarat_district_id_mapping.csv"

# Load district ID mapping
mapping = pd.read_csv(mapping_file)
mapping["ID"] = mapping["ID"].astype(int)

district_lookup = dict(zip(mapping["ID"], mapping["District"]))

all_data = []

# Read and combine district files
files = sorted(source_dir.glob("data_distwise_id_*"))

for file in files:
    match = re.fullmatch(r"data_distwise_id_(\d+)", file.name)

    if not match:
        continue

    district_id = int(match.group(1))
    district_name = district_lookup.get(district_id)

    if district_name is None:
        print(f"Skipping unmapped ID: {district_id}")
        continue

    df = pd.read_csv(
        file,
        sep=r"\s+",
        header=None,
        names=["year", "month", "spei_1", "spei_4", "spei_12"],
        na_values=["NaN", "nan"]
    )

    df["district_id"] = district_id
    df["district"] = district_name

    all_data.append(df)

# Combine
combined = pd.concat(all_data, ignore_index=True)

# Convert data types
combined["year"] = combined["year"].astype(int)
combined["month"] = combined["month"].astype(int)

for col in ["spei_1", "spei_4", "spei_12"]:
    combined[col] = pd.to_numeric(combined[col], errors="coerce")

# Create date column
combined["date"] = pd.to_datetime(
    dict(
        year=combined["year"],
        month=combined["month"],
        day=1
    )
)

# Arrange columns
combined = combined[
    [
        "date",
        "year",
        "month",
        "district_id",
        "district",
        "spei_1",
        "spei_4",
        "spei_12"
    ]
]

# Sort
combined = combined.sort_values(
    ["district", "date"]
).reset_index(drop=True)

# Save
output_file = output_dir / "gujarat_district_spei.csv"
combined.to_csv(output_file, index=False)

# Validation
print("\n========== SPEI DATASET SUMMARY ==========")
print("Districts:", combined["district"].nunique())
print("Total records:", len(combined))
print("Date range:", combined["date"].min(), "to", combined["date"].max())

print("\nMissing values:")
print(combined[["spei_1", "spei_4", "spei_12"]].isna().sum())

print("\nDuplicate district-month records:",
      combined.duplicated(["district_id", "date"]).sum())

print("\nRecords per district:")
print(combined.groupby("district").size())

print("\nSaved:", output_file.resolve())
