from fastapi import APIRouter

from services.recent_hmis_service import (
    get_recent_hmis_overview,
    get_recent_hmis_coverage,
    get_recent_hmis_indicators,
    get_recent_hmis_districts_latest,
)
from schemas import (
    RecentHmisOverviewResponse,
    RecentHmisCoverageResponse,
    RecentHmisIndicatorsResponse,
)

router = APIRouter()


@router.get("/overview", response_model=RecentHmisOverviewResponse)
def recent_hmis_overview():
    return get_recent_hmis_overview()


@router.get("/coverage", response_model=RecentHmisCoverageResponse)
def recent_hmis_coverage():
    return get_recent_hmis_coverage()


@router.get("/indicators", response_model=RecentHmisIndicatorsResponse)
def recent_hmis_indicators():
    return get_recent_hmis_indicators()


@router.get("/districts/latest")
def recent_hmis_districts_latest():
    return get_recent_hmis_districts_latest()