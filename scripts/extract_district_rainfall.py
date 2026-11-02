
import ee
import geopandas as gpd
import pandas as pd
import os

# -----------------------------------------
# 1. Initialize Earth Engine
# -----------------------------------------

PROJECT_ID = "gen-lang-client-0439006539"

ee.Initialize(project=PROJECT_ID)

print("Earth Engine initialized successfully.")

# -----------------------------------------
# 2. Load Gujarat village boundaries
# -----------------------------------------

GEOJSON_PATH = (
    "data/raw/villages_extracted/vb_soi_gj.GeoJSON"
)

gdf = gpd.read_file(GEOJSON_PATH)

# Find district column
district_col = next(
    (col for col in gdf.columns
     if col.lower() == "district"),
    None
)

if district_col is None:
    raise ValueError(
        f"District column not found. Available columns: {list(gdf.columns)}"
    )

gdf = gdf[gdf.geometry.notna()].copy()
gdf = gdf[~gdf.geometry.is_empty].copy()

gdf[district_col] = (
    gdf[district_col].astype(str).str.strip()
)

gdf = gdf[gdf[district_col] != ""]

# Ensure geographic coordinates
gdf = gdf.to_crs("EPSG:4326")

print("Village boundaries loaded:", len(gdf))

# -----------------------------------------
# 3. Create district boundaries
# -----------------------------------------

districts = gdf.dissolve(
    by=district_col,
    as_index=False
)

# Simplify geometries to reduce Earth Engine payload
districts["geometry"] = districts.geometry.simplify(
    tolerance=0.005,
    preserve_topology=True
)

print("Number of districts:", len(districts))

# -----------------------------------------
# 4. Convert district polygons to EE
# -----------------------------------------

ee_features = []

for _, row in districts.iterrows():

    geometry = ee.Geometry(
        row.geometry.__geo_interface__
    )

    feature = ee.Feature(
        geometry,
        {"district": str(row[district_col])}
    )

    ee_features.append(feature)

district_fc = ee.FeatureCollection(ee_features)

print("District boundaries converted to Earth Engine.")

# -----------------------------------------
# 5. Load CHIRPS daily rainfall
# -----------------------------------------

chirps = (
    ee.ImageCollection("UCSB-CHC/CHIRPS/V3/DAILY_RNL")
    .filterDate("1981-01-01", "2026-08-01")
    .select("precipitation")
)

# -----------------------------------------
# 6. Prepare monthly periods
# -----------------------------------------

start_date = ee.Date("1981-01-01")
end_date = ee.Date("2026-08-01")

number_of_months = int(
    end_date.difference(start_date, "month").getInfo()
)

months = ee.List.sequence(
    0, number_of_months - 1
)

print("Months to process:", number_of_months)

# -----------------------------------------
# 7. Calculate monthly rainfall by district
# -----------------------------------------

def calculate_district_rainfall(index):

    month_start = start_date.advance(index, "month")
    month_end = month_start.advance(1, "month")

    monthly_rainfall = (
        chirps
        .filterDate(month_start, month_end)
        .sum()
    )

    results = monthly_rainfall.reduceRegions(
        collection=district_fc,
        reducer=ee.Reducer.mean(),
        scale=5566,
        tileScale=4
    )

    return results.map(
        lambda feature: feature.set({
            "year": month_start.get("year"),
            "month": month_start.get("month"),
            "date": month_start.format("YYYY-MM")
        })
    )


monthly_results = ee.FeatureCollection(
    months.map(calculate_district_rainfall)
).flatten()

# -----------------------------------------
# 8. Export results to Google Drive
# -----------------------------------------

task = ee.batch.Export.table.toDrive(
    collection=monthly_results,
    description="AquaSentinel_District_Rainfall",
    folder="AquaSentinel",
    fileNamePrefix="gujarat_district_monthly_rainfall",
    fileFormat="CSV"
)

task.start()

print("\nEarth Engine export task started!")
print("Task status:", task.status())

print(
    "\nCheck Google Drive for the AquaSentinel folder "
    "after the export completes."
)
