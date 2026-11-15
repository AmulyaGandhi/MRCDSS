# MRCDSS — Final Project Completion Report

**Repository:** `/Users/amulyapagidimarri/Desktop/MRCDSS`  
**Commit baseline:** `453bfd0` (`main`)  
**Work completed:** single completion pass implementing corrections, UI polish, verification, and judge deliverables.  
**Readiness verdict:** functionally stable and professionally polished; suitable for academic demonstration with disclosed limitations; **not** a clinically validated predictive tool.

---

## 1. Summary of completed work

### 1.1 Semantic / research-integrity corrections (P0–P1)

- **DSS priority terminology:** "Persistent" replaced by "Repeated" throughout backend (`planning_service.py`, `districts_service.py`) and frontend (`Assistant.tsx` suggested question). The repeated-priority rule (≥2 historical district-year records at the same level) is explicitly described as a historical pattern, not current/latest status.
- **Planning-focus descriptions:** labelled "Model-attributed planning focus" with the note that it indicates where the model attributed influence, **not** a verified district needs assessment.
- **SHAP direction:** no longer hardcoded as risk-increasing. `DistrictDetails.tsx` reports "Contribution direction unavailable" and "Attribution does not establish causality"; the unused `ContributingFactors.tsx` uses neutral "Pushes toward / away from High Risk" wording.
- **Clinical thresholds removed:** indicator interpretations state "Observed value; no clinical threshold applied." Hardcoded 15/25/50/30-style thresholds are gone from the rendered UI.
- **Historical vs current labels:** Overview presents "Latest historical … not current or live status"; district detail shows the assessment year; Disha distinguishes historical risk from recent HMIS evidence; Recent HMIS never reassigns risk class.
- **"Validated" overclaims removed** from rendered code paths: no "validated MRCDSS" risk classes/features/system in backend services or frontend pages; "validated" retained only in disclaimers stating validation does **not** exist and in preserved historical output reports (not modified).
- **Disha fixes:** coverage lookup now reads `district_coverage` (was silently skipped); high-priority list uses latest historical observations (not 2016 record-level); district risk counts use the explicit 707-unit latest projection; "validated" wording removed; unsupported questions return "not available."

### 1.2 Data / API corrections

- **Unified state/district normalization:** `GET /api/unified/overview` now reports 36 normalized states and 812 normalized units (39 raw state strings and 850 raw entries reconciled, 38 duplicate normalized entries). Raw aliases preserved for provenance.
- **Global error handler:** `backend/main.py` returns HTTP 404 (instead of 500) for missing data files (`FileNotFoundError`).
- **Hardcoded values removed:** `risk_analysis_service.py` reads silhouette/DBI/CHI and sensitivity sizes from artifacts (no hardcoded fallback 961 / 0.231).
- **Frontend/client consistency:** API client interfaces match backend schemas; district detail lookup uses normalized keys via the unified endpoint.

### 1.3 Recent HMIS presentation

- Missingness (ANC 158, TT2 158, Severe Anemia 168, Obstetric 1,087), invalid-value flags (1,955 total), partial 2024–25 (17 states), and excluded 2025–26 are displayed accurately across `/recent-hmis`, Overview, and Risk Analysis. Values are retained, never clipped.

### 1.4 Documentation

- `README.md` rewritten to reflect actual implementation (backend `backend.main:app`, real endpoints, six-feature model, limitations, integrity rules).
- Created `docs/judge_demo_guide.md` (startup + 8–12 minute demo sequence).
- Created `docs/judge_questions_and_answers.md` (36 technically accurate Q&A including difficult methodology questions).
- Created `docs/research_paper_draft.md` (paper draft using only actual project evidence; no fabricated references).
- Created this report (`reports/final_project_completion_report.md`).

### 1.5 UI polish

The existing React frontend was already component-based with a restrained palette. Verified consistent typography/spacing/colour, professional headers and section hierarchy, clean cards/tables/charts/map, consistent legends/labels/units/formatting, readable district details and SHAP explanations, clear historical vs recent HMIS presentation, consistent buttons/navigation/loading/empty/error states, and responsive desktop/mobile layouts. No decorative elements were added and no functionality removed.

---

## 2. Files modified

### Backend
- `backend/main.py` — added `Request`/`JSONResponse` imports and a global `FileNotFoundError` → 404 exception handler.
- `backend/services/planning_service.py` — repeated-priority semantics (label, note, rule) already aligned; kept consistent.
- `backend/services/districts_service.py` — priority history exposes latest historical class/proportion and the repeated-priority rule; latest observation documented as historical not current.
- `backend/services/risk_analysis_service.py` — reads clustering/sensitivity metrics from artifacts; evaluation design discloses circularity, unit overlap, and absence of grouped/temporal validation.
- `backend/services/unified_service.py` — normalized state/district identity (36 states / 812 units) with raw-entry reconciliation.
- `backend/services/recent_hmis_service.py` — missingness, invalid flags, partial-year and 2025–26 exclusion disclosed.
- `backend/services/assistant_service.py` — coverage key fixed (`district_coverage`); high-priority list uses latest observations; "validated" overclaims removed; SHAP treated as attribution not causation.
- `backend/services/methodology_service.py` — "six selected" terminology (no "validated" feature claim).

### Frontend
- `frontend/src/pages/DistrictDetails.tsx` — no SHAP direction inferred; no clinical thresholds; historical year shown; recent HMIS separated.
- `frontend/src/pages/Overview.tsx` — latest-historical framing; "not current or live status" noted.
- `frontend/src/pages/Planning.tsx` — historical district-year framing; repeated vs latest priority distinguished.
- `frontend/src/pages/RiskAnalysis.tsx` — evaluation-design and limitations disclosed; ROC-AUC shown at full precision (0.999961).
- `frontend/src/pages/RecentHmis.tsx` — missingness/invalid flags/partial coverage displayed.
- `frontend/src/components/Assistant.tsx` — "repeated High Priority" suggestion (not "persistent").
- `frontend/src/components/ContributingFactors.tsx` — neutral SHAP direction wording.
- `frontend/src/index.css` — reviewed; restrained academic palette retained (no changes required).

### Tests (corrected assertions to match fixed behavior)
- `tests/assistant/test_assistant_api.py` — missing-evidence assertion now expects "no derived historical MRCDSS risk classification" (removed the removed "validated" claim).
- `tests/recent_hmis/test_dataset3.py` — narrowed `test_mrcdss_outputs_unchanged` to `models`, `outputs`, `src`; `backend`/`frontend` intentionally refined per task scope and excluded from byte-identity protection.

### Documentation (new)
- `README.md` — rewritten.
- `docs/judge_demo_guide.md` — new.
- `docs/judge_questions_and_answers.md` — new.
- `docs/research_paper_draft.md` — new.
- `reports/final_project_completion_report.md` — this file.

### Not modified (preserved)
- `dataset1.csv`, `dataset2.csv` (raw inputs)
- `data/recent_hmis/raw/*` (source HMIS files)
- `models/*.pkl` (saved trained models)
- `outputs/` (clustering, classification, SHAP, DSS artifacts and metrics)
- `src/` pipeline code (preprocessing, clustering, classification, SHAP, DSS) — primary model and research design unchanged

---

## 3. Backend test results

Command: `source .venv/bin/activate && pytest tests/ -q`  
Result: **281 passed, 0 failed** (10 warnings, all pre-existing deprecation/performance notes).

The suite is read-only: row counts, duplicate absence, schema preservation, raw-data hash checks, clustering reproducibility (with pinned BLAS/OpenMP threads so protected `outputs/` stay byte-identical), model evaluation, and Disha grounding behavior. No test modifies raw data, saved metrics, or historical labels.

---

## 4. Frontend build and test results

Command: `cd frontend && npm run build` (`tsc -b && vite build`)  
Result: **Build succeeded.**  
- `dist/index.html`, `dist/assets/index-CQ-0hxQy.css` (46.96 kB), `dist/assets/index-ClqBT3Dk.js` (846.37 kB gzip 247.09 kB).  
- One non-fatal chunk-size warning (>500 kB); no errors. TypeScript type-check (`tsc -b`) passed.  
- No frontend test script is configured; no frontend test suite exists to run.

---

## 5. API and Disha verification

The backend was started (`uvicorn backend.main:app --port 8000`) and every major endpoint was exercised with `curl`, plus Disha with representative and unsupported questions. All returned HTTP 200 with grounded, internally consistent answers.

### 5.1 API endpoint results

| Endpoint | Result |
|----------|--------|
| `GET /api/health` | `{"status":"ok"}` |
| `GET /api/overview` | 8,405 records; 707 units; 36 states; risk 2,614/1,345/4,446; SHAP ranking present |
| `GET /api/districts/states` | 36 states |
| `GET /api/districts/latest` | 707 units (latest historical observation per unit) |
| `GET /api/districts/{state}/{district}` | Warangal: latest year 2019, priority history "Repeated High Priority Observations", 12 records |
| `GET /api/risk-analysis` | clustering metrics; model comparison; evaluation design (654/654 test units overlap train); SHAP summary; sensitivity |
| `GET /api/planning-priorities` | repeated High 441 / Medium 220 / Low 46 / insufficient 0; latest High 91 / Medium 493 / Low 123; label "Model-attributed planning focus" |
| `GET /api/methodology` | six features (no "validated" claim); disclaimers present |
| `GET /api/recent-hmis/overview` | 3,306 observations; 812 units; 36 states; 2020–2025; partial 2024–25 |
| `GET /api/recent-hmis/coverage` | reference 707 vs Dataset 3 812 units; per-year observations/states |
| `GET /api/recent-hmis/indicators` | missingness + data-quality flags per indicator (1,955 total flags) |
| `GET /api/unified/overview` | 11,711 observations; 36 normalized states; 812 normalized units; identity reconciliation block |
| `GET /api/unified/districts` | 812 normalized units; 850 raw entries |
| `GET /api/unified/districts/{state}/{district}` | normalized lookup with historical + recent records |
| `GET /api/unified/years` | historical + recent year coverage |
| `POST /api/assistant/chat` | grounded responses for all intents; unsupported → not-available |

Representative district check: Warangal (Telangana) → latest historical year 2019, Low Risk / Low Priority. High, Medium, Low, and no-recent-data districts behave consistently (historical year shown, recent table present or "no observations").

### 5.2 Disha verification (representative questions)

| Question | Intent | Grounded | Key point in answer |
|----------|--------|----------|---------------------|
| Risk classification of Warangal? | district_risk | yes | Latest historical assessment year 2019; not clinical diagnoses |
| Priority of Warangal? | district_priority | yes | Low Priority at assessment year 2019 |
| Difference historical vs recent HMIS? | dataset | yes | 11,711 obs; 36 states; 812 units; distinct eras |
| Why was Dataset 3 not used to retrain? | methodology | yes | Definition incompatibility (Severe Anemia threshold, Institutional Delivery/PNC) |
| Limitations of the system? | limitations | yes | Derived groups; no external validation; SHAP not causation |
| Can this diagnose a patient? | limitations | yes | No diagnosis/treatment; planning support only |
| Explain SHAP | shap | yes | Attribution not causation; High Risk class; positive/negative split |
| Does recent HMIS reassign risk? | recent_risk_change | yes | Never used to assign/change historical class |
| Is the moon made of cheese? | unknown | no | "Not available in the current MRCDSS evidence" |
| Repeated High Priority districts? | aggregate | yes | 441 repeated High; not latest priority |

No "validated" overclaims, no invented statistics, no SHAP-as-causation statements.

---

## 6. Confirmation of preservation

- **Raw datasets:** `dataset1.csv` (6,293 rows) and `dataset2.csv` (2,112 rows) unchanged; raw HMIS files under `data/recent_hmis/raw/` hash-verified by `tests/recent_hmis/test_dataset3.py` (unchanged).
- **Saved model metrics / historical labels:** `models/*.pkl` and all `outputs/` artifacts (clusters, profiles, metrics, SHAP matrix, DSS CSV, planning rules) unchanged; test suite confirms byte-identity for `models`, `outputs`, `src`.
- **Primary model:** six-feature model preserved; no retraining; K=3; random_state=42 unchanged.

---

## 7. Remaining limitations (disclosed, not disguised)

1. **Feature–target circularity:** K-Means labels derived from the same six features used by the classifiers; metrics reproduce derived labels.
2. **Train/test unit overlap:** 100% of test records belong to a State–District unit also present in training; no grouped/temporal validation.
3. **Weak cluster separation:** silhouette 0.238; K fixed; no stability/ARI/bootstrap analysis.
4. **Label sensitivity:** removing Severe Anemia changes 54.35% of risk classes; Severe Anemia has cross-dataset harmonization uncertainty.
5. **No external clinical validation:** risk classes are not clinical diagnoses; no independent outcome or validation dataset.
6. **SHAP is attribution, not causation:** signed per-district direction not stored.
7. **Recent HMIS is partial and contextual:** 2024–25 covers 17 states only; 2025–26 excluded; no risk class assigned; not used to retrain.
8. **Planning focus is model-attributed guidance**, not a verified needs assessment.
9. **No clinical thresholds** are applied or justified.

---

## 8. Final judge-readiness verdict

**Verdict: READY FOR ACADEMIC DEMONSTRATION, WITH DISCLOSED LIMITATIONS.**

The MRCDSS application is functionally stable (all 281 backend tests pass; frontend production build succeeds; all major API endpoints and Disha paths verified), professionally polished (restrained, consistent UI; clear historical-vs-recent framing; honest SHAP and limitations messaging), and research-integrity preserving (raw data, saved models, and historical labels unchanged; six-feature primary model preserved; no validation overclaims).

It is **not** ready for operational decision support or for claims of clinical/predictive validity. Judges should evaluate it as a transparent, well-documented research prototype whose limitations are explicitly disclosed in the UI, README, methodology, and audit/completion reports.

**Recommended demo duration:** 8–12 minutes (see `docs/judge_demo_guide.md`).  
**Judge Q&A:** see `docs/judge_questions_and_answers.md` (36 questions).  
**Paper draft:** see `docs/research_paper_draft.md` (no fabricated references).
