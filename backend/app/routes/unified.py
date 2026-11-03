
from fastapi import APIRouter, HTTPException

from app.services.unified_risk_engine import (
    get_unified_district_risk
)

router = APIRouter(
    prefix="/api/risk",
    tags=["Unified Risk"]
)


@router.get("/latest")
def latest_unified_risk():

    try:
        return get_unified_district_risk()

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
