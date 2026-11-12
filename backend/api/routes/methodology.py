from fastapi import APIRouter
from services.methodology_service import get_methodology
from schemas import MethodologyResponse

router = APIRouter()


@router.get("", response_model=MethodologyResponse)
def methodology():
    data = get_methodology()
    return data
