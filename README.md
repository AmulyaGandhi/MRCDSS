# MRCDSS Public Health Data Science Platform

Local development only. No deployment.

## Quick Start

### 1. Setup Environment

```bash
cp .env.example .env
pip install -r requirements.txt
```

### 2. Run Data Pipeline

```bash
python src/preprocessing/preprocess.py
python src/feature_selection/select_features.py
python src/clustering/risk_clustering.py
python src/feature_selection/final_features.py
python src/clustering/sensitivity.py
python src/classification/train_models.py
python src/classification/evaluate_models.py
python src/explainability/shap_analysis.py
python src/decision_support/decision_engine.py
```

### 3. Run API Server

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Run Tests

```bash
pytest tests/ -v
```

### 5. Start Frontend

```bash
cd frontend && npm install && npm start
```

## Project Structure

```
src/
  preprocessing/      Data loading and cleaning
  feature_selection/  Feature mapping and selection
  clustering/         K-Means risk clustering
  classification/     Supervised ML models
  explainability/     SHAP analysis
  decision_support/   DSS rules and engine
  api/                FastAPI backend
frontend/             React frontend (placeholder)
outputs/              All pipeline outputs
tests/                All tests
config.yaml           Pipeline configuration
```

## Configuration

Edit `config.yaml` or `.env` to change settings. No hardcoded URLs in application code.

## Modules

| Module | Purpose |
|--------|---------|
| preprocessing | Load, clean, transform raw data |
| feature_selection | Map 8 maternal-health indicators |
| clustering | K-Means risk classification |
| classification | Logistic Regression, Decision Tree, Random Forest, XGBoost |
| explainability | SHAP feature importance |
| decision_support | Planning priorities from risk + SHAP |
| api | REST API serving all outputs |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| /api/health | Health check |
| /api/features | List all features |
| /api/final-features | Get final model features |
| /api/risk-clusters | Get risk clusters |
| /api/decision-support | Get DSS records |
| /api/decision-support/summary | Get district summaries |
| /api/shap-values | Get SHAP values |
| /api/feature-importance | Get feature importance |
| /api/model-metrics | Get classification metrics |
| /api/planning-rules | Get planning rules |
