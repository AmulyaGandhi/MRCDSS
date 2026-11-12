import os
import json
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _load_csv(path):
    full = os.path.join(BASE_DIR, path)
    if not os.path.exists(full):
        return None
    return pd.read_csv(full)

app = FastAPI(title="MRCDSS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/api/features")
def get_features():
    df = _load_csv("outputs/selected_features/final_model_features.csv")
    if df is None:
        raise HTTPException(status_code=404, detail="Features not found")
    return {"features": [c for c in df.columns if c not in ["State", "District", "Year", "source_dataset"]]}

@app.get("/api/final-features")
def get_final_features(
    source_dataset: str = Query(None),
    year: int = Query(None),
    limit: int = Query(100),
):
    df = _load_csv("outputs/selected_features/final_model_features.csv")
    if df is None:
        raise HTTPException(status_code=404, detail="Features not found")
    if source_dataset:
        df = df[df["source_dataset"] == source_dataset]
    if year is not None:
        df = df[df["Year"] == year]
    return {
        "count": len(df),
        "records": df.head(limit).to_dict(orient="records"),
    }

@app.get("/api/risk-clusters")
def get_risk_clusters(
    source_dataset: str = Query(None),
    cluster_id: int = Query(None),
    risk_class: str = Query(None),
    limit: int = Query(100),
):
    df = _load_csv("outputs/risk_classification/district_year_risk_clusters.csv")
    if df is None:
        raise HTTPException(status_code=404, detail="Risk clusters not found")
    if source_dataset:
        df = df[df["source_dataset"] == source_dataset]
    if cluster_id is not None:
        df = df[df["cluster_id"] == cluster_id]
    if risk_class:
        df = df[df["risk_class"] == risk_class]
    return {
        "count": len(df),
        "records": df.head(limit).to_dict(orient="records"),
    }

@app.get("/api/decision-support")
def get_decision_support(
    priority_level: str = Query(None),
    state: str = Query(None),
    limit: int = Query(100),
):
    df = _load_csv("outputs/decision_support/district_decision_support.csv")
    if df is None:
        raise HTTPException(status_code=404, detail="Decision support not found")
    if priority_level:
        df = df[df["priority_level"] == priority_level]
    if state:
        df = df[df["State"] == state]
    return {
        "count": len(df),
        "records": df.head(limit).to_dict(orient="records"),
    }

@app.get("/api/decision-support/summary")
def get_dss_summary(state: str = Query(None)):
    df = _load_csv("outputs/decision_support/district_priority_summary.csv")
    if df is None:
        raise HTTPException(status_code=404, detail="Summary not found")
    if state:
        df = df[df["State"] == state]
    return {
        "count": len(df),
        "districts": df.to_dict(orient="records"),
    }

@app.get("/api/shap-values")
def get_shap_values(limit: int = Query(100)):
    df = _load_csv("outputs/explainability/shap_values_test.csv")
    if df is None:
        raise HTTPException(status_code=404, detail="SHAP values not found")
    return {
        "count": len(df),
        "features": list(df.columns),
        "records": df.head(limit).to_dict(orient="records"),
    }

@app.get("/api/feature-importance")
def get_feature_importance():
    df = _load_csv("outputs/explainability/feature_importance.csv")
    if df is None:
        raise HTTPException(status_code=404, detail="Feature importance not found")
    return {"features": df.to_dict(orient="records")}

@app.get("/api/model-metrics")
def get_model_metrics():
    path = os.path.join(BASE_DIR, "outputs", "classification", "model_comparison.csv")
    if not os.path.exists(path):
        return {"error": "Model comparison not found"}
    df = pd.read_csv(path)
    return {"models": df.to_dict(orient="records")}

@app.get("/api/classification/report")
def get_classification_report():
    path = os.path.join(BASE_DIR, "outputs", "classification", "classification_report.md")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Report not found")
    with open(path) as f:
        return {"report": f.read()}

@app.get("/api/planning-rules")
def get_planning_rules():
    df = _load_csv("outputs/decision_support/planning_rules.csv")
    if df is None:
        raise HTTPException(status_code=404, detail="Planning rules not found")
    return {"rules": df.to_dict(orient="records")}
