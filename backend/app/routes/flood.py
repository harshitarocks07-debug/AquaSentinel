
from fastapi import APIRouter, HTTPException, Query

from app.services.flood_engine import (
    get_latest_flood_risk,
    get_flood_history
)

router = APIRouter(
    prefix="/api/flood",
    tags=["Flood"]
)


# Latest flood risk across all districts
@router.get("/latest")
def latest_flood_risk():

    try:
        return get_latest_flood_risk()

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# Historical flood risk for a district
@router.get("/history/{district}")
def flood_history(
    district: str,
    days: int = Query(default=90, ge=1, le=3650)
):

    try:
        result = get_flood_history(
            district,
            days
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"No flood history found for district: {district}"
            )

        return result

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
