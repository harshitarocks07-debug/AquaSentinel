
import pandas as pd

files = {
    "SPI-3": "data/processed/gujarat_district_spi.csv",
    "SPEI-4": "data/processed/gujarat_district_spei_validated.csv"
}

for name, path in files.items():
    df = pd.read_csv(path)

    print(f"\n{'='*45}")
    print(name)
    print("="*45)

    print("Columns:", df.columns.tolist())
    print("Shape:", df.shape)

    print("\nSample records:")
    print(df.head(3).to_string(index=False))

    print("\nDate range:")
    print(df["date"].min(), "to", df["date"].max())

    print("\nDistrict examples:")
    print(df["district"].drop_duplicates().head(10).tolist())
