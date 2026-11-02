
import ee
import csv
import os

# -----------------------------------
# 1. Initialize Google Earth Engine
# -----------------------------------

PROJECT_ID = "gen-lang-client-0439006539"

ee.Initialize(project=PROJECT_ID)

print("Earth Engine initialized.")

# -----------------------------------
# 2. Define Gujarat geographical area
# -----------------------------------

india_states = ee.FeatureCollection(
    "FAO/GAUL/2015/level1"
)

gujarat = india_states.filter(
    ee.Filter.eq("ADM0_NAME", "India")
).filter(
    ee.Filter.eq("ADM1_NAME", "Gujarat")
)

gujarat_geometry = gujarat.geometry()

print("Gujarat boundary loaded.")

# -----------------------------------
# 3. Load CHIRPS daily rainfall
# -----------------------------------

chirps = (
    ee.ImageCollection("UCSB-CHC/CHIRPS/V3/DAILY_RNL")
    .filterDate("1981-01-01", "2026-08-01")
    .select("precipitation")
)

# -----------------------------------
# 4. Calculate monthly rainfall
# -----------------------------------

start_date = ee.Date("1981-01-01")
end_date = ee.Date("2026-08-01")

number_of_months = int(
    end_date.difference(start_date, "month").getInfo()
)

print("Months to process:", number_of_months)

months = ee.List.sequence(0, number_of_months - 1)


def calculate_monthly_rainfall(month_index):

    month_start = start_date.advance(month_index, "month")
    month_end = month_start.advance(1, "month")

    monthly_collection = chirps.filterDate(
        month_start, month_end
    )

    monthly_rainfall = monthly_collection.sum()

    # Spatial average of monthly rainfall across Gujarat
    result = monthly_rainfall.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=gujarat_geometry,
        scale=5566,
        maxPixels=1e13,
        tileScale=4
    )

    return ee.Feature(None, {
        "year": month_start.get("year"),
        "month": month_start.get("month"),
        "date": month_start.format("YYYY-MM"),
        "rainfall_mm": result.get("precipitation")
    })


monthly_results = ee.FeatureCollection(
    months.map(calculate_monthly_rainfall)
)

# -----------------------------------
# 5. Retrieve results
# -----------------------------------

print("Extracting monthly rainfall data...")

results = monthly_results.getInfo()

rows = []

for feature in results["features"]:

    properties = feature["properties"]

    rows.append({
        "year": properties["year"],
        "month": properties["month"],
        "date": properties["date"],
        "rainfall_mm": properties["rainfall_mm"]
    })

# -----------------------------------
# 6. Save CSV
# -----------------------------------

output_folder = "data/processed"

os.makedirs(output_folder, exist_ok=True)

output_file = os.path.join(
    output_folder,
    "gujarat_monthly_rainfall.csv"
)

with open(output_file, "w", newline="", encoding="utf-8") as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "year",
            "month",
            "date",
            "rainfall_mm"
        ]
    )

    writer.writeheader()
    writer.writerows(rows)

print("\nExtraction completed successfully!")
print("Total monthly records:", len(rows))
print("Saved to:", output_file)

print("\nFirst five records:")

for row in rows[:5]:
    print(row)
