# MRCDSS — Judge Demo Guide

**8–12 minute demonstration sequence for academic evaluators.**  
MRCDSS is a district-level maternal-health risk decision-support prototype. Emphasize that it is a **research prototype with disclosed limitations**, not a clinically validated predictive tool.

## Before you begin (one-time setup)

Prerequisites: Python 3.10+, Node.js 18+, internet access for package install only (the app runs offline once installed).

```bash
# 1. Backend
cd /Users/amulyapagidimarri/Desktop/MRCDSS
source .venv/bin/activate
pip install -r requirements.txt   # already satisfied in .venv
uvicorn backend.main:app --host 127.0.0.1 --port 8000
# Confirm: http://127.0.0.1:8000/api/health  -> {"status":"ok"}

# 2. Frontend (separate terminal)
cd frontend
npm ci                            # or npm install
npm run dev                       # http://localhost:5173
```

Leave both servers running during the demo. The frontend calls the backend at `http://localhost:8000`.

## Demonstration sequence (8–12 minutes)

| Minute | Section | What to show | Key talking point |
|--------|---------|--------------|-------------------|
| 0–1 | **About** | Open `/about`. Read System Purpose, Intended Users, Technology Stack, Limitations, Disclaimer. | Set expectations: planning support, not clinical diagnosis; no external validation. |
| 1–2 | **Methodology** | Open `/methodology`. Walk the pipeline steps and caveats. Note "Six features used across all methods" (not "validated"). | Six fixed features; K=3 K-Means; silhouette ≈ 0.238 (weak–moderate separation); labels derived, not clinical. |
| 2–3 | **Overview** | Open `/`. Observe the map (latest historical MRCDSS risk per district, 2008–2019), the risk/priority distribution bars, and the SHAP feature bar chart. Select a district to bring up the info panel with recent HMIS evidence. | Map shows **latest historical** assessment, not current status. Recent HMIS is contextual evidence only, no risk class assigned. |
| 3–4 | **District Details** | From the map/table, open a High, a Medium, a Low, and a no-recent-data district. Confirm: risk class, priority, year, historical timeline table, Recent HMIS table (or "no Recent HMIS observations"), contributing factors with **no direction inferred**, planning focus, indicator values with "no clinical threshold applied." | Signed district-specific SHAP direction is **not stored**; indicators carry no clinical threshold. Historical vs recent clearly separated. |
| 4–5 | **Planning Priorities** | Open `/planning`. Confirm the wording: historical district-year records, repeated-priority rule (≥2 years at same level), latest historical distribution (High 91 / Medium 493 / Low 123 out of 707 units), planning rules table, contributing-indicator counts. | "Repeated" ≠ "persistent/current." Latest distribution differs from repeated counts (441 repeated High vs 91 latest High). |
| 5–6 | **Risk Analysis** | Open `/risk-analysis`. Show clustering metrics (silhouette 0.238081, DBI 1.473643, CHI 2276.14), model comparison (Logistic Regression selected by macro-F1), evaluation-design disclosure (100% of test records share a training unit), SHAP summary with positive/negative split, sensitivity table (excluding Severe Anemia changes 54.35% of classes). | Metrics reproduce derived labels on seen units — **not** external predictive accuracy. Labels are sensitive to feature choice. |
| 6–7 | **Recent HMIS** | Open `/recent-hmis`. Show 3,306 observations (2020–2025), 812 units, 36 states, partial 2024–25 (17 states), 2025–26 excluded. Indicator availability/missingness (ANC 3,148 valid / 158 missing; TT2 3,148/158; Severe Anemia 3,138/168; Obstetric 2,219/1,087). Data-quality flags (TT2 368 out-of-range, max 185.93; Severe Anemia 5, max 354.55; Obstetric 11, max 762.43). | Invalid values are retained and flagged, never clipped. Recent HMIS was not used to retrain the model. |
| 7–8 | **Disha assistant** | Open the assistant overlay. Ask: (a) "What is the risk classification of Warangal?" → latest historical year 2019, not clinical. (b) "Why was Dataset 3 not used to retrain?" → definition incompatibility. (c) "Can this diagnose a patient?" → no. (d) "Is the moon made of cheese?" → not available. | Grounded, deterministic fallback; no invented statistics; no "validated" overclaims. |
| 8–9 | **API spot check** | `curl http://127.0.0.1:8000/api/unified/overview` → 11,711 observations, 36 normalized states, 812 normalized units (850 raw entries → 38 duplicates reconciled). | State/district identity normalized at the API boundary; raw spellings retained for provenance. |
| 9–10 | **Tests** | Run `pytest tests/ -q` → 281 passed. | Read-only integrity suite; raw data, models, and outputs unchanged. |
| 10–12 | **Limitations & Q&A** | Re-open About → Limitations and Methodological Caveats. Invite difficult questions (see `docs/judge_questions_and_answers.md`). | Disclose circularity, train/test unit overlap, weak separation, Severe Anemia comparability, no external validation. |

## District representatives to use during the demo

- **High / repeated High:** pick any district from the Overview latest-High table (assessment year shown, 2008–2019).
- **Medium / Low:** any Medium or Low district from the map or District Explorer.
- **No recent HMIS:** a district whose District Details Recent HMIS section says "No Recent HMIS observations are available for this district."
- **Warangal (Telangana):** latest historical year 2019, Low Risk / Low Priority, has Recent HMIS evidence — good for Disha.

## What judges should NOT hear

Do not claim:
- that risk classes are clinically validated or diagnose patients;
- that supervised accuracy/F1/ROC-AUC is external predictive performance;
- that SHAP direction is known per district (it is not stored);
- that recent HMIS changes a district's risk class (it never does);
- that "persistent High" means current High (it means repeated historical observations).

## Rollback / troubleshooting

- Backend won't start: ensure `.venv` activated and `requirements.txt` installed; port 8000 free.
- Frontend can't reach API: confirm backend is running and `VITE_API_BASE_URL` defaults to `http://localhost:8000`.
- Map tiles blank: Leaflet needs network for tiles; the rest of the app works offline.

## Deliverables referenced

- `docs/judge_questions_and_answers.md` — 25+ judge Q&A including difficult methodology questions.
- `docs/research_paper_draft.md` — paper draft grounded in actual project evidence (no fabricated references).
- `reports/final_project_completion_report.md` — changes, files modified, test/build/API results, limitations, readiness verdict.
- `reports/final_comprehensive_audit_report.md` — prior audit (read-only, not modified).
- `README.md` — startup and integrity summary.
