import ee

PROJECT_ID = "gen-lang-client-0439006539"

try:
    ee.Initialize(project=PROJECT_ID)

    print("Google Earth Engine connected successfully!")

    image = ee.Image("USGS/SRTMGL1_003")

    elevation = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=ee.Geometry.Point([72.5714, 23.0225]),
        scale=30
    ).getInfo()

    print("Sample elevation:", elevation)

except Exception as e:
    print("Earth Engine connection failed:", e)