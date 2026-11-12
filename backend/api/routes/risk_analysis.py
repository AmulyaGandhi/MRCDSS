from fastapi import APIRouter
from services.risk_analysis_service import get_risk_analysis
from schemas import RiskAnalysisResponse

router = APIRouter()


@router.get("", response_model=RiskAnalysisResponse)
def risk_analysis():
    data = get_risk_analysis()
    return data
