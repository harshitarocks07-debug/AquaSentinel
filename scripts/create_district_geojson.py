
import geopandas as gpd
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    BASE_DIR
    / "Data"
    / "Raw"
    / "villages_extracted"
    / "vb_soi_gj.GeoJSON"
)

OUTPUT_DIR = BASE_DIR / "Data" / "Processed"
OUTPUT_FILE = OUTPUT_DIR / "gujarat_districts.geojson"

def main():
    print("Loading village boundaries...")

    gdf = gpd.read_file(INPUT_FILE)

    # Remove whitespace from column names
    gdf.columns = gdf.columns.str.strip()

    # Validate required columns
    required = ["district", "dtcode", "geometry"]
    missing = [col for col in required if col not in gdf.columns]

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    print("Village features:", len(gdf))
    print("Unique districts:", gdf["district"].nunique())

    # Remove invalid or missing district names
    gdf = gdf.dropna(subset=["district", "geometry"]).copy()
    gdf["district"] = gdf["district"].astype(str).str.strip()
    gdf = gdf[gdf["district"] != ""]

    # Dissolve village polygons into district boundaries
    print("Dissolving village boundaries...")

    districts = gdf.dissolve(
        by="dtcode",
        aggfunc={"district": "first"}
    ).reset_index()

    # Repair invalid geometries if necessary
    districts["geometry"] = districts.geometry.make_valid()

    # Keep only required properties
    districts = districts[["dtcode", "district", "geometry"]]

    # Reproject to WGS84 for Leaflet
    districts = districts.to_crs(epsg=4326)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    districts.to_file(
        OUTPUT_FILE,
        driver="GeoJSON"
    )

    print("\nDistrict GeoJSON created successfully.")
    print("Output:", OUTPUT_FILE)
    print("District features:", len(districts))
    print("District names:")
    print(districts["district"].sort_values().to_list())


if __name__ == "__main__":
    main()

