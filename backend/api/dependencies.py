from typing import Optional
from pydantic import BaseModel


class PaginationParams(BaseModel):
    page: int = 1
    per_page: int = 10


class DistrictFilters(BaseModel):
    state: Optional[str] = None
    district: Optional[str] = None
    risk_class: Optional[str] = None
    priority: Optional[str] = None
    year: Optional[int] = None
