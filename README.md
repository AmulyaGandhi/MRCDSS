# MRCDSS — Maternal Health Risk Decision Support System

A district-level maternal-health decision-support prototype built for public-health planning research. MRCDSS derives district risk profiles (Low / Medium / High) from historical district-year maternal-health indicators (Datasets 1 + 2, 2008–2019), replicates them with supervised models, explains them with SHAP, and maps them to planning priorities through a rule-based Decision Support System (DSS). A Recent HMIS extension (Dataset 3, 2020–2025) adds contextual indicator evidence without retraining the historical model.

**Research status:** working analytical prototype. The derived risk classes and supervised metrics are **not** externally or clinically validated and must not be used for diagnosis, treatment, or operational decisions.

## Key design facts (read before demonstrating)

- **Six-feature primary model:** ANC First Trimester, TT2 / Booster, Severe Anemia, Institutional Delivery, PNC within 48h, Obstetric Complications. Fixed across clustering, classification, SHAP, DSS, and the dashboard.
- **Labels are derived:** risk classes come from K-Means clustering (K=3) on the same six features; they are analytical groups, not clinical diagnoses or ground truth.
- **Supervised metrics are label-reproduction:** Logistic Regression, Decision Tree, Random Forest, and XGBoost reproduce the K-Means-derived labels on a record-level 80/20 split. Every test record belongs to a State–District unit also seen in training, so scores (e.g. accuracy ≈ 0.996) measure consistency with derived labels, not external predictive accuracy.
- **Circularity & overlap:** labels and features share the same six-feature space; there is no grouped or temporal validation and no external clinical validation.
- **Weak separation:** silhouette ≈ 0.238; removing Severe Anemia changes the risk class of 54.35% of records. Labels are materially sensitive to feature choice.
- **SHAP is attribution, not causation:** global test-set SHAP explains the High Risk class; signed district-specific direction is not stored for individual records.
- **Recent HMIS is contextual only:** Dataset 3 (2020–2025, partial 2024–25; 2025–26 excluded) was not used to retrain or re-classify and carries no risk class. Several indicators are not comparable across periods (e.g. Severe Anemia Hb threshold changed <7 to ≤7 g/dl).
- **"Persistent / repeated" priority:** a unit-level historical pattern label (≥2 district-year records at the same level). It is not the latest priority and not current status.

See `reports/final_comprehensive_audit_report.md` and `reports/final_project_completion_report.md` for the full limitation register.

## Repository layout

```
backend/            FastAPI API (main.py) + services + routes + schemas
data/               Unified dataset and Recent HMIS extension (derived, read-only)
dataset1.csv        Raw Dataset 1 (6,293 rows, 2008–2019) — do not modify
dataset2.csv        Raw Dataset 2 (2,112 rows, 2008–2019) — do not modify
frontend/           React + TypeScript + Vite dashboard
models/             Saved trained models (do not regenerate)
outputs/            Pipeline artifacts (clusters, metrics, SHAP, DSS) — do not modify
reports/            Audit and completion reports
src/                Training pipeline (preprocessing, clustering, classification, SHAP, DSS)
tests/              Backend test suite
```

## Quick start

### 1. Backend

```bash
# From repository root
cp .env.example .env   # optional
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The API serves `http://localhost:8000` and exposes `/api/health`, `/api/overview`, `/api/districts/*`, `/api/districts/latest`, `/api/risk-analysis`, `/api/planning-priorities`, `/api/methodology`, `/api/recent-hmis/*`, `/api/unified/*`, and `/api/assistant/chat`.

### 2. Frontend

```bash
cd frontend
npm install        # or npm ci
npm run dev        # Vite dev server, http://localhost:5173
npm run build      # production build
npm run preview    # serve the production build locally
```

The frontend calls the backend at `http://localhost:8000` by default (set `VITE_API_BASE_URL` to override).

### 3. Tests

```bash
# Backend (read-only integrity tests; do not modify data or models)
source .venv/bin/activate
pytest tests/ -q
```

### 4. Disha assistant

`POST /api/assistant/chat` is retrieval-grounded and works without an LLM (deterministic fallback). Set `MRCDSS_LLM_PROVIDER=ollama` and `MRCDSS_OLLAMA_MODEL` to use a local Ollama model for phrasing; answers are still grounded in MRCDSS evidence.

## API endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Health check |
| `GET /api/overview` | Historical overview: counts, risk/priority distribution, feature ranking (SHAP magnitude) |
| `GET /api/districts` | Historical district-year records (paginated, filterable by state/district/risk/priority/year) |
| `GET /api/districts/states` | List of states |
| `GET /api/districts/years` | List of years |
| `GET /api/districts/latest` | Latest historical observation per State–District unit (not current status) |
| `GET /api/districts/{state}/{district}` | District detail: full historical record list + priority history |
| `GET /api/risk-analysis` | Clustering metrics, profiles, model comparison, evaluation design, SHAP summary, sensitivity |
| `GET /api/planning-priorities` | Priority distribution, repeated-priority summary, planning rules, contributing-indicator counts |
| `GET /api/methodology` | Methodology items and disclaimers |
| `GET /api/recent-hmis/overview` | Dataset 3 observations, years, states, coverage notes |
| `GET /api/recent-hmis/coverage` | Yearly coverage + district identity coverage vs 707-unit reference |
| `GET /api/recent-hmis/indicators` | Indicator availability/missingness, distributions, harmonization, data-quality flags |
| `GET /api/recent-hmis/districts/latest` | Latest Recent HMIS observation per district (no risk class) |
| `GET /api/unified/overview` | Unified dataset counts, normalized state/district identity reconciliation, feature availability |
| `GET /api/unified/districts` | One row per normalized State–District unit with raw aliases |
| `GET /api/unified/districts/{state}/{district}` | Historical + Recent HMIS records for a normalized unit |
| `GET /api/unified/years` | Historical and recent year coverage |
| `POST /api/assistant/chat` | Disha: grounded natural-language Q&A |

## Data and model integrity

- Raw inputs (`dataset1.csv`, `dataset2.csv`, `data/recent_hmis/raw/*`) are **not** modified by the API or tests.
- Saved models (`models/*.pkl`), clustering outputs, metrics, SHAP values, and DSS outputs under `outputs/` are **not** retrained or regenerated at runtime. The API only reads them.
- Dataset 3 (`data/recent_hmis/dataset3/dataset3_recent_hmis.csv`) is read-only and was not used to retrain the historical model.

## Tests

Run `pytest tests/` from the repository root with the virtualenv activated. Tests are read-only integrity checks: row counts, duplicate absence, schema preservation, raw-data hash checks, and assistant grounding behavior. The clustering reproducibility test re-derives centroids with pinned BLAS/OpenMP threads so the protected `outputs/` artifacts stay byte-identical.

## Limitations

This is a research prototype. Notable limitations are disclosed in the application (Risk Analysis → Methodological Caveats; About → Limitations) and in `reports/final_comprehensive_audit_report.md`:

- Derived (K-Means) risk classes are not clinical diagnoses; no external clinical validation exists.
- Supervised metrics reproduce derived labels on seen units; 100% of test records share a State–District unit with training.
- Weak cluster separation (silhouette ≈ 0.238); K=3 fixed; Severe Anemia has cross-dataset harmonization uncertainty and drives label sensitivity.
- Recent HMIS is contextual evidence only; 2024–25 is partial (17 states) and 2025–26 is excluded.
- SHAP indicates model contribution, not causation; planning focus is model-attributed guidance, not a verified needs assessment.

Do not use this system for clinical decisions or as evidence of predictive performance.
