
import pandas as pd

file_path = "data/processed/gujarat_district_spi.csv"

df = pd.read_csv(file_path)

print("Dataset shape:", df.shape)
print("District count:", df["district"].nunique())

print("\nSPI statistics:")
print(df["spi_3"].describe())

print("\nDrought classification counts:")
print(df["drought_status"].value_counts())

print("\nDistrict-wise latest SPI:")

df["date"] = pd.to_datetime(df["date"])

latest = (
    df.dropna(subset=["spi_3"])
    .sort_values("date")
    .groupby("district")
    .tail(1)
)

print(
    latest[
        ["district", "date", "rainfall_3month",
         "spi_3", "drought_status"]
    ].sort_values("spi_3").to_string(index=False)
)

print("\nMissing SPI values:", df["spi_3"].isna().sum())
