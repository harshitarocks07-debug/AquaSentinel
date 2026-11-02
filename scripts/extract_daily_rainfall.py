
import ee
import geopandas as gpd

# -----------------------------------------
# 1. Configuration
# -----------------------------------------

PROJECT_ID = "gen-lang-client-0439006539"

# Change this value for each yearly export.
YEAR = 1982

GEOJSON_PATH = "data/raw/villages_extracted/vb_soi_gj.GeoJSON"

# CHIRPS V3 daily reanalysis currently available
# through 31 July 2026.
DATASET_END = "2026-08-01"

ee.Initialize(project=PROJECT_ID)

print("Earth Engine initialized successfully.")

# -----------------------------------------
# 2. Load Gujarat village boundaries
# -----------------------------------------

gdf = gpd.read_file(GEOJSON_PATH)

district_col = next(
    (col for col in gdf.columns if col.lower() == "district"),
    None
)

if district_col is None:
    raise ValueError(
        f"District column not found. Available columns: {list(gdf.columns)}"
    )

gdf = gdf[gdf.geometry.notna()].copy()
gdf = gdf[~gdf.geometry.is_empty].copy()

gdf[district_col] = gdf[district_col].astype(str).str.strip()
gdf = gdf[gdf[district_col] != ""]

gdf = gdf.to_crs("EPSG:4326")

print("Village boundaries loaded:", len(gdf))

# -----------------------------------------
# 3. Create district boundaries
# -----------------------------------------

districts = gdf.dissolve(
    by=district_col,
    as_index=False
)

districts["geometry"] = districts.geometry.simplify(
    tolerance=0.005,
    preserve_topology=True
)

print("Districts:", len(districts))

# -----------------------------------------
# 4. Convert districts to Earth Engine
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

print("District boundaries converted successfully.")

# -----------------------------------------
# 5. Load daily CHIRPS rainfall
# -----------------------------------------

year_start = f"{YEAR}-01-01"

year_end = (
    f"{YEAR + 1}-01-01"
    if YEAR < 2026
    else DATASET_END
)

if YEAR < 1981 or YEAR > 2026:
    raise ValueError("YEAR must be between 1981 and 2026.")

if year_start >= DATASET_END:
    raise ValueError("No CHIRPS data available for this year.")

chirps = (
    ee.ImageCollection("UCSB-CHC/CHIRPS/V3/DAILY_RNL")
    .filterDate(year_start, year_end)
    .select("precipitation")
)

image_count = chirps.size().getInfo()

print(f"Year: {YEAR}")
print(f"Period: {year_start} to {year_end}")
print("Daily images found:", image_count)

if image_count == 0:
    raise ValueError("No CHIRPS images found for this period.")

# -----------------------------------------
# 6. Calculate daily rainfall by district
# -----------------------------------------

image_list = chirps.toList(image_count)


def calculate_daily_rainfall(image):

    image = ee.Image(image)

    date = image.date().format("YYYY-MM-dd")

    results = image.reduceRegions(
        collection=district_fc,
        reducer=ee.Reducer.mean(),
        scale=5566,
        tileScale=4
    )

    def prepare_feature(feature):

        feature = ee.Feature(feature)

        return feature.set({
            "date": date,
            "rainfall_mm": feature.get("mean")
        }).select([
            "district",
            "date",
            "rainfall_mm"
        ])

    return results.map(prepare_feature)


daily_results = ee.FeatureCollection(
    image_list.map(calculate_daily_rainfall)
).flatten()

print("Daily district rainfall collection prepared.")

# -----------------------------------------
# 7. Export yearly CSV to Google Drive
# -----------------------------------------

file_name = f"gujarat_district_daily_rainfall_{YEAR}"

task = ee.batch.Export.table.toDrive(
    collection=daily_results,
    description=f"AquaSentinel_Daily_Rainfall_{YEAR}",
    folder="AquaSentinel",
    fileNamePrefix=file_name,
    fileFormat="CSV",
    selectors=["district", "date", "rainfall_mm"]
)

task.start()

print("\nExport task started successfully!")
print("File:", file_name + ".csv")
print("Expected records:", image_count * len(districts))
print("Task status:", task.status())

print(
    "\nCheck Google Earth Engine Tasks and Google Drive "
    "for the export."
)
