
from pathlib import Path
import pandas as pd


# Project directory
BASE_DIR = Path(__file__).resolve().parents[3]

# Dataset paths
SPI_FILE = (
    BASE_DIR
    / "Data"
    / "Processed"
    / "gujarat_district_spi_deploy.csv"
)

SPEI_FILE = (
    BASE_DIR
    / "Data"
    / "Processed"
    / "gujarat_district_spei_validated.csv"
)


# Drought classification using SPI-3
def classify_drought(spi):

    if pd.isna(spi):
        return "Insufficient Data"

    if spi <= -2.0:
        return "Extreme Drought"

    if spi <= -1.5:
        return "Severe Drought"

    if spi <= -1.0:
        return "Moderate Drought"

    return "Normal"


# Load SPI dataset
def get_drought_data():

    if not SPI_FILE.exists():
        raise FileNotFoundError(
            f"SPI dataset not found: {SPI_FILE}"
        )

    df = pd.read_csv(SPI_FILE)

    if "date" not in df.columns:
        raise ValueError("SPI dataset is missing the date column")

    if "district" not in df.columns:
        raise ValueError("SPI dataset is missing the district column")

    if "spi_3" not in df.columns:
        raise ValueError("SPI dataset is missing the spi_3 column")

    # Convert dates to datetime
    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
        format="mixed"
    )

    # Remove invalid dates
    df = df.dropna(subset=["date"]).copy()

    # Normalize district names
    df["district"] = df["district"].astype(str).str.strip()

    # Convert SPI values to numeric
    df["spi_3"] = pd.to_numeric(
        df["spi_3"],
        errors="coerce"
    )

    df["risk_level"] = df["spi_3"].apply(classify_drought)

    return df


# Get latest drought risk for all districts
def get_district_drought_risk():

    df = get_drought_data()

    if df.empty:
        return {
            "latest_date": None,
            "total_districts": 0,
            "districts": []
        }

    latest_date = df["date"].max()

    latest = df[
        df["date"] == latest_date
    ].copy()

    result = latest[
        ["district", "date", "spi_3", "risk_level"]
    ].sort_values(
        "spi_3",
        na_position="last"
    )

    result["date"] = result["date"].dt.strftime("%Y-%m-%d")

    result["spi_3"] = result["spi_3"].replace(
        [float("inf"), float("-inf")],
        float("nan")
    )

    result = result.astype(object).where(
        pd.notna(result),
        None
    )

    return {
        "latest_date": latest_date.strftime("%Y-%m-%d"),
        "total_districts": len(result),
        "districts": result.to_dict(orient="records")
    }


# Get historical drought data for a district
def get_drought_history(district):

    df = get_drought_data()

    district_df = df[
        df["district"].str.upper() == district.strip().upper()
    ].sort_values("date").copy()

    if district_df.empty:
        return None

    history_df = district_df[
        ["date", "spi_3", "risk_level"]
    ].copy()

    history_df["date"] = history_df["date"].dt.strftime(
        "%Y-%m-%d"
    )

    history_df["spi_3"] = history_df["spi_3"].replace(
        [float("inf"), float("-inf")],
        float("nan")
    )

    history_df = history_df.astype(object).where(
        pd.notna(history_df),
        None
    )

    return history_df.to_dict(orient="records")
