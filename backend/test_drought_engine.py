
from app.services.drought_engine import (
    get_drought_data,
    get_district_drought_risk,
    get_drought_history
)

# Test 1: Load SPI data
df = get_drought_data()
print("Total records:", len(df))
print("Districts:", df["district"].nunique())

# Test 2: Latest district risk
result = get_district_drought_risk()

print("\nLatest date:", result["latest_date"])
print("Total districts:", result["total_districts"])

for district in result["districts"][:10]:
    print(district)

# Test 3: Historical district data
history = get_drought_history("RAJKOT")

print("\nRajkot historical records:", len(history) if history else 0)
