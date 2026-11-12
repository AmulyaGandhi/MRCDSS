from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from services.districts_service import (
    get_districts,
    get_district_detail,
    get_all_states,
    get_all_years,
    get_latest_district_observations,
)

router = APIRouter()


@router.get("", tags=["districts"])
def list_districts(
    state: Optional[str] = Query(None, description="Filter by state"),
    district: Optional[str] = Query(None, description="Search by district name"),
    risk_class: Optional[str] = Query(None, description="Filter by risk class (Low/Medium/High)"),
    priority: Optional[str] = Query(None, description="Filter by priority (Low/Medium/High)"),
    year: Optional[int] = Query(None, description="Filter by year"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Records per page"),
):
    result = get_districts(
        state=state,
        district=district,
        risk_class=risk_class,
        priority=priority,
        year=year,
        page=page,
        per_page=per_page,
    )
    return result


@router.get("/states", tags=["districts"])
def list_states():
    return {"states": get_all_states()}


@router.get("/years", tags=["districts"])
def list_years():
    return {"years": get_all_years()}


@router.get("/latest", tags=["districts"])
def latest_observations():
    """Return the latest available observation for each (State, District) unit.

    Used by the District Risk Landscape map. No year control is exposed to the UI.
    """
    return get_latest_district_observations()


@router.get("/{state}/{district}", tags=["districts"])
def district_detail(state: str, district: str):
    result = get_district_detail(state, district)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No data found for {state} / {district}")
    return result