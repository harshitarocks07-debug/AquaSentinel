
import ee
from datetime import datetime, timezone

PROJECT_ID = "gen-lang-client-0439006539"

# Initialize Earth Engine
ee.Initialize(project=PROJECT_ID)

print("Earth Engine initialized successfully.")

# Load CHIRPS V3 daily rainfall
chirps = (
    ee.ImageCollection("UCSB-CHC/CHIRPS/V3/DAILY_RNL")
    .filterDate("1981-01-01", "2026-08-01")
    .select("precipitation")
)

# Check dataset coverage
count = chirps.size().getInfo()

first_image = chirps.sort("system:time_start").first()
last_image = chirps.sort("system:time_start", False).first()

first_date = ee.Date(
    first_image.get("system:time_start")
).format("YYYY-MM-dd").getInfo()

last_date = ee.Date(
    last_image.get("system:time_start")
).format("YYYY-MM-dd").getInfo()

print("Total daily images:", count)
print("First available date:", first_date)
print("Last available date:", last_date)

# Ahmedabad sample location
point = ee.Geometry.Point([72.5714, 23.0225])

# Get latest available daily rainfall
latest_rainfall = last_image.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=point,
    scale=5566
).getInfo()

print("Latest rainfall at Ahmedabad:", latest_rainfall)

# Calculate annual rainfall for 2025
rainfall_2025 = (
    chirps
    .filterDate("2025-01-01", "2026-01-01")
    .sum()
)

annual_value = rainfall_2025.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=point,
    scale=5566
).getInfo()

print("2025 annual rainfall at Ahmedabad:", annual_value)

print("CHIRPS integration test completed.")
