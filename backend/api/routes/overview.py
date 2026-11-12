from fastapi import APIRouter, Query
from fastapi import HTTPException

from services.overview_service import get_overview_data
from schemas import OverviewResponse

router = APIRouter()


@router.get("", response_model=OverviewResponse)
def overview():
    data = get_overview_data()
    return data
