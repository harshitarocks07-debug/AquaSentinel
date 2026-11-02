import pandas as pd

file_path = "data/processed/gujarat_district_monthly_rainfall.csv"

df = pd.read_csv(file_path)

print("Dataset shape:", df.shape)
print("\nColumns:")
print(df.columns.tolist())

print("\nFirst five records:")
print(df.head())

print("\nDistrict count:")
print(df["district"].nunique())

print("\nMissing values:")
print(df.isnull().sum())