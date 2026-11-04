from fastapi import APIRouter, HTTPException
from app.services.unified_risk_engine import get_unified_district_risk

router = APIRouter(prefix="/api/risk", tags=["Unified Risk"])


@router.get("/latest")
@router.get("/districts")
def unified_district_risk():
    try:
        return get_unified_district_risk()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))