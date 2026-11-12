from fastapi import APIRouter

from services.unified_service import (
    get_unified_overview,
    get_unified_districts,
    get_unified_district,
    get_unified_years,
)

router = APIRouter()


@router.get("/overview")
def unified_overview():
    return get_unified_overview()


@router.get("/districts")
def unified_districts():
    return get_unified_districts()


@router.get("/districts/{state}/{district}")
def unified_district(state: str, district: str):
    return get_unified_district(state, district)


@router.get("/years")
def unified_years():
    return get_unified_years()