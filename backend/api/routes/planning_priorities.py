from fastapi import APIRouter
from services.planning_service import get_planning_priorities
from schemas import PlanningPrioritiesResponse

router = APIRouter()


@router.get("", response_model=PlanningPrioritiesResponse)
def planning_priorities():
    data = get_planning_priorities()
    return data
