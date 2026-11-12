from typing import Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from services.assistant_service import chat

router = APIRouter()


class AssistantTurn(BaseModel):
    role: Literal["user", "assistant"]
    text: str


class AssistantScope(BaseModel):
    state: Optional[str] = None
    district: Optional[str] = None
    matched: bool = False
    risk_class: Optional[str] = None
    topic: Optional[str] = None


class AssistantChatRequest(BaseModel):
    message: str
    state: Optional[str] = None
    district: Optional[str] = None
    page_context: Optional[Literal[
        "overview",
        "district_explorer",
        "risk_analysis",
        "planning_priorities",
        "methodology",
        "about",
    ]] = None
    history: Optional[list[AssistantTurn]] = None
    scope: Optional[AssistantScope] = None


class AssistantContext(BaseModel):
    state: Optional[str] = None
    district: Optional[str] = None
    matched: bool
    risk_class: Optional[str] = None
    topic: Optional[str] = None


class AssistantChatResponse(BaseModel):
    answer: str
    grounded: bool
    sources: list[str]
    mode: Literal["ollama", "fallback", "general"]
    intent: str
    context: Optional[AssistantContext] = None


@router.post("/chat", response_model=AssistantChatResponse)
def assistant_chat(body: AssistantChatRequest):
    return chat(
        message=body.message,
        state=body.state,
        district=body.district,
        page_context=body.page_context,
        history=[t.model_dump() for t in (body.history or [])],
        scope=body.scope.model_dump() if body.scope else None,
    )