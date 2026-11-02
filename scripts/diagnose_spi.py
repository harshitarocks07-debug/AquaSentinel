
import pandas as pd

df = pd.read_csv(
    "data/processed/gujarat_district_spi.csv"
)

df["date"] = pd.to_datetime(df["date"])

print("TOTAL ROWS:", len(df))
print("TOTAL DISTRICTS:", df["district"].nunique())

print("\nMISSING SPI BY DISTRICT:")

print(
    df.groupby("district")["spi_3"]
    .apply(lambda x: x.isna().sum())
    .to_string()
)

print("\nMONTHLY RECORD COUNT BY DISTRICT:")

print(
    df.groupby("district")
    .size()
    .describe()
)

print("\nSPI VALUE RANGE:")
print(df["spi_3"].describe())

print("\nMISSING RAINFALL:")
print(df["rainfall_mm"].isna().sum())

print("\nDUPLICATE DISTRICT-DATE RECORDS:")
print(
    df.duplicated(["district", "date"]).sum()
)

print("\nDATE RANGE:")
print(df["date"].min(), "to", df["date"].max())
