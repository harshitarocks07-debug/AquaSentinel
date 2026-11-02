
import geopandas as gpd
import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"

print("=" * 50)
print("AQUASENTINEL DATA INSPECTION")
print("=" * 50)

# 1. IMD rainfall CSV
csv_path = RAW_DIR / "rainfall_districtwise_daily_imd.csv"

print("\n[1] IMD RAINFALL")

df = pd.read_csv(csv_path)

print("Shape:", df.shape)
print("Columns:", df.columns.tolist())
print("\nFirst 3 records:")
print(df.head(3))

# 2. Gujarat village GeoJSON
geojson_path = RAW_DIR / "villages_extracted" / "vb_soi_gj.GeoJSON"

print("\n[2] VILLAGE BOUNDARIES")

gdf = gpd.read_file(geojson_path)

print("Total villages:", len(gdf))
print("Columns:", gdf.columns.tolist())
print("Geometry types:", gdf.geom_type.value_counts())
print("Coordinate system:", gdf.crs)

print("\nFirst 3 villages:")
print(gdf.head(3))

print("\nInspection completed.")
