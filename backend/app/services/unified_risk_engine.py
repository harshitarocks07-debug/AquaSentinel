
from app.services.drought_engine import get_district_drought_risk
from app.services.flood_engine import get_latest_flood_risk


# --------------------------------------------------
# 1. RISK PRIORITY CONFIGURATION
# --------------------------------------------------

# Ordinal priority for alert ordering.
# This is NOT a statistically calibrated combined risk score.

DROUGHT_PRIORITY = {
    "Extreme Drought": 4,
    "Severe Drought": 3,
    "Moderate Drought": 2,
    "Normal": 0,
    "Insufficient Data": -1,
}

FLOOD_PRIORITY = {
    "Very High": 4,
    "High": 3,
    "Moderate": 2,
    "Low": 1,
    "Insufficient Data": -1,
}


# --------------------------------------------------
# 2. ALERT PRIORITY
# --------------------------------------------------

def get_alert_priority(drought_status, flood_status):

    drought_priority = DROUGHT_PRIORITY.get(
        drought_status, -1
    )

    flood_priority = FLOOD_PRIORITY.get(
        flood_status, -1
    )

    available = [
        value
        for value in [drought_priority, flood_priority]
        if value >= 0
    ]

    if not available:
        return -1

    return max(available)


# --------------------------------------------------
# 3. OVERALL ALERT CLASSIFICATION
# --------------------------------------------------

def classify_overall_alert(priority):

    if priority == 4:
        return "Critical"

    elif priority == 3:
        return "High"

    elif priority == 2:
        return "Moderate"

    elif priority == 1:
        return "Low"

    elif priority == 0:
        return "Normal"

    return "Insufficient Data"


# --------------------------------------------------
# 4. UNIFIED DISTRICT RISK ENGINE
# --------------------------------------------------

def get_unified_district_risk():

    drought_data = get_district_drought_risk()
    flood_data = get_latest_flood_risk()

    drought_districts = drought_data.get(
        "districts", []
    )

    flood_districts = flood_data.get(
        "districts", []
    )

    # Index datasets by normalized district name.

    drought_map = {
        item["district"].strip().upper(): item
        for item in drought_districts
    }

    flood_map = {
        item["district"].strip().upper(): item
        for item in flood_districts
    }

    all_districts = sorted(
        set(drought_map) | set(flood_map)
    )

    results = []

    for district in all_districts:

        drought = drought_map.get(district, {})
        flood = flood_map.get(district, {})

        drought_status = drought.get(
            "risk_level",
            "Insufficient Data"
        )

        flood_status = flood.get(
            "risk_level",
            "Insufficient Data"
        )

        priority = get_alert_priority(
            drought_status,
            flood_status
        )

        # Existing rule-based and drought information
        drought_result = {
            "date": drought.get("date"),
            "spi_3": drought.get("spi_3"),
            "status": drought_status,
        }

        # Existing flood information + new ML predictions
        flood_result = {
            "date": flood.get("date"),
            "rainfall_1d_mm": flood.get("rainfall_1d_mm"),
            "rainfall_3d_mm": flood.get("rainfall_3d_mm"),
            "rainfall_7d_mm": flood.get("rainfall_7d_mm"),
            "rainfall_30d_mm": flood.get("rainfall_30d_mm"),

            # Existing rule-based assessment
            "risk_score": flood.get("risk_score"),
            "status": flood_status,

            # New XGBoost output
            "extreme_rainfall_model_score": flood.get(
                "extreme_rainfall_model_score"
            ),

            "extreme_rainfall_warning": flood.get(
                "extreme_rainfall_warning"
            ),

            "model_decision_threshold": flood.get(
                "model_decision_threshold"
            ),
        }

        results.append({
            "district": (
                drought.get("district")
                or flood.get("district")
                or district
            ),

            "drought": drought_result,
            "flood": flood_result,

            "overall_alert": classify_overall_alert(
                priority
            ),

            "alert_priority": priority,
        })

    # Most urgent districts first
    results.sort(
        key=lambda item: item["alert_priority"],
        reverse=True
    )

    return {
        "drought_data_date": drought_data.get(
            "latest_date"
        ),

        "flood_data_date": flood_data.get(
            "latest_date"
        ),

        "total_districts": len(results),

        # Model availability and evaluation metadata
        "flood_model_status": flood_data.get(
            "model_status",
            {"available": False}
        ),

        "districts": results,
    }
