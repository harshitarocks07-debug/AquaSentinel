
from fastapi import APIRouter, HTTPException, Query

from app.services.drought_engine import (
    get_district_drought_risk,
    get_drought_history
)

router = APIRouter(
    prefix="/api/drought",
    tags=["Drought"]
)


@router.get("/latest")
def latest_drought_risk():
    try:
        return get_district_drought_risk()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{district}")
def drought_history(district: str):
    result = get_drought_history(district)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="District not found"
        )

    return {
        "district": district.upper(),
        "records": len(result),
        "history": result
    }
