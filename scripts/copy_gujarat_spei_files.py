
from pathlib import Path
import pandas as pd
import shutil
import re

# Source paths
atlas_dir = Path(
    r"C:\Users\ADMIN\Downloads\DroughtAtlas_v2\DroughtAtlas_v2"
)

excel_path = atlas_dir / "Z-score" / "India_Districts.xlsx"
source_dir = atlas_dir / "Z-score" / "Districts"

# Destination inside AquaSentinel
destination_dir = Path("data/raw/drought_atlas_gujarat_districts")
destination_dir.mkdir(parents=True, exist_ok=True)

# Read district mapping
df = pd.read_excel(excel_path)

gujarat = df[
    df["State"].astype(str).str.strip().str.upper() == "GUJARAT"
].copy()

gujarat["ID"] = pd.to_numeric(gujarat["ID"], errors="coerce")
gujarat = gujarat.dropna(subset=["ID"])
gujarat["ID"] = gujarat["ID"].astype(int)

district_ids = set(gujarat["ID"])

print(f"Gujarat districts found in Excel: {len(district_ids)}")

# Index available SPEI files by district ID
available_files = {}

for file in source_dir.iterdir():
    match = re.fullmatch(r"data_distwise_id_(\d+)", file.name)

    if match and file.is_file():
        available_files[int(match.group(1))] = file

# Copy matching files
copied = []
missing = []

for district_id in sorted(district_ids):
    source_file = available_files.get(district_id)

    if source_file:
        shutil.copy2(source_file, destination_dir / source_file.name)
        copied.append(district_id)
    else:
        missing.append(district_id)

print(f"\nFiles copied: {len(copied)}")
print(f"District IDs not found: {missing}")

# Save district ID mapping
gujarat.to_csv(
    destination_dir / "gujarat_district_id_mapping.csv",
    index=False
)

print(f"\nDestination: {destination_dir.resolve()}")
print("\nCopied district files:")

for district_id in copied:
    district_name = gujarat.loc[
        gujarat["ID"] == district_id, "District"
    ].iloc[0]

    print(f"{district_id}: {district_name}")

if len(copied) != len(district_ids):
    print("\nWARNING: Not all Gujarat district files were found.")
else:
    print("\nSUCCESS: All Gujarat district files copied.")
