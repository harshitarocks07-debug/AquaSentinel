
import ee
import geopandas as gpd

# =========================================
# 1. CONFIGURATION
# =========================================

PROJECT_ID = "gen-lang-client-0439006539"

GEOJSON_PATH = "data/raw/villages_extracted/vb_soi_gj.GeoJSON"

# Five-year batches
BATCHES = [
    (1983, 1992),
    (1993, 2002),
    (2003, 2012),
    (2013, 2022),
    (2023, 2026)
]

# CHIRPS V3 daily reanalysis ends on 31 July 2026
DATASET_END = "2026-08-01"

# Initially submit only the first batch
BATCH_INDEX = 4

# =========================================
# 2. INITIALIZE EARTH ENGINE
# =========================================

ee.Initialize(project=PROJECT_ID)

print("Earth Engine initialized successfully.")

# =========================================
# 3. LOAD DISTRICT BOUNDARIES
# =========================================

gdf = gpd.read_file(GEOJSON_PATH)

district_col = next(
    (col for col in gdf.columns if col.lower() == "district"),
    None
)

if district_col is None:
    raise ValueError("District column not found.")

gdf = gdf[gdf.geometry.notna()].copy()
gdf = gdf[~gdf.geometry.is_empty].copy()

gdf[district_col] = gdf[district_col].astype(str).str.strip()
gdf = gdf[gdf[district_col] != ""]

gdf = gdf.to_crs("EPSG:4326")

districts = gdf.dissolve(
    by=district_col,
    as_index=False
)

districts["geometry"] = districts.geometry.simplify(
    tolerance=0.005,
    preserve_topology=True
)

print("Districts loaded:", len(districts))

# =========================================
# 4. CONVERT TO EARTH ENGINE FEATURES
# =========================================

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

print("District boundaries converted.")

# =========================================
# 5. SELECT BATCH
# =========================================

start_year, end_year = BATCHES[BATCH_INDEX]

start_date = f"{start_year}-01-01"

end_date = (
    f"{end_year + 1}-01-01"
    if end_year < 2026
    else DATASET_END
)

print("\nSelected batch:", start_year, "-", end_year)
print("Date range:", start_date, "to", end_date)

# =========================================
# 6. LOAD DAILY CHIRPS
# =========================================

chirps = (
    ee.ImageCollection("UCSB-CHC/CHIRPS/V3/DAILY_RNL")
    .filterDate(start_date, end_date)
    .select("precipitation")
)

image_count = chirps.size().getInfo()

print("Daily images:", image_count)

if image_count == 0:
    raise ValueError("No CHIRPS images found.")

# =========================================
# 7. CALCULATE DAILY DISTRICT RAINFALL
# =========================================

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

        return ee.Feature(None, {
            "district": feature.get("district"),
            "date": date,
            "rainfall_mm": feature.get("mean")
        })

    return results.map(prepare_feature)


image_list = chirps.toList(image_count)

daily_results = ee.FeatureCollection(
    image_list.map(calculate_daily_rainfall)
).flatten()

print("Daily rainfall collection prepared.")

# =========================================
# 8. EXPORT TO GOOGLE DRIVE
# =========================================

file_name = (
    f"gujarat_district_daily_rainfall_"
    f"{start_year}_{end_year}"
)

task = ee.batch.Export.table.toDrive(
    collection=daily_results,
    description=f"AquaSentinel_Daily_{start_year}_{end_year}",
    folder="AquaSentinel",
    fileNamePrefix=file_name,
    fileFormat="CSV",
    selectors=["district", "date", "rainfall_mm"]
)

task.start()

print("\nExport task submitted!")
print("File:", file_name + ".csv")
print("Expected records:", image_count * len(districts))
print("Task status:", task.status())
