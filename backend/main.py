import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.overview import router as overview_router
from api.routes.districts import router as districts_router
from api.routes.risk_analysis import router as risk_analysis_router
from api.routes.planning_priorities import router as planning_router
from api.routes.methodology import router as methodology_router
from api.routes.recent_hmis import router as recent_hmis_router
from api.routes.unified import router as unified_router
from api.routes.assistant import router as assistant_router

app = FastAPI(
    title="District-Level Maternal Health Risk Decision Support System",
    version="1.0.0",
    description="API serving district-level maternal health risk analysis, planning priorities, and methodology",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.environ.get("FRONTEND_URL", "http://localhost:3000"),
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(overview_router, prefix="/api/overview", tags=["Overview"])
app.include_router(districts_router, prefix="/api/districts", tags=["Districts"])
app.include_router(risk_analysis_router, prefix="/api/risk-analysis", tags=["Risk Analysis"])
app.include_router(planning_router, prefix="/api/planning-priorities", tags=["Planning Priorities"])
app.include_router(methodology_router, prefix="/api/methodology", tags=["Methodology"])
app.include_router(recent_hmis_router, prefix="/api/recent-hmis", tags=["Recent HMIS Extension"])
app.include_router(unified_router, prefix="/api/unified", tags=["Unified Dataset"])
app.include_router(assistant_router, prefix="/api/assistant", tags=["MRCDSS Assistant"])


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
