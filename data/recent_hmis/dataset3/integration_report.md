# Dataset 3 — Frontend/Backend Integration Report

Recent-HMIS analytical extension integrated as a separate "Recent HMIS Analysis" module in the MRCDSS
application. The original MRCDSS pipeline (Dataset 1/2, preprocessing, feature selection, K-Means,
supervised models, SHAP/XAI, DSS, and its existing endpoints/pages) was left untouched.

## A. Scope and non-goals

- Dataset 3 is presented as a **recent-district-level HMIS data and indicator availability** extension.
- Dataset 3 was **not** used to retrain, re-cluster, or externally validate the existing MRCDSS
  classifier, its K-Means risk profiles, SHAP explanations, or DSS rules.
- No automatic district merging was performed: district identifiers retain their native HMIS
  representation in Dataset 3 and in the UI.
- Dataset 1, Dataset 2, raw HMIS XLSX files, model artifacts, and analytical outputs under
  `outputs/` were not modified. See Section H for verification.

## B. Backend changes

New read-only module served under the existing FastAPI app (all endpoints prefix `/api/recent-hmis`):

| Area | File | Change |
| --- | --- | --- |
| Service | `backend/services/recent_hmis_service.py` | Loads the prepared `dataset3_recent_hmis.csv` and the coverage-audit mapping once; pre-aggregates overview, coverage, and indicator payloads. No indicator is recomputed from raw HMIS files at request time. |
| Router | `backend/api/routes/recent_hmis.py` | New `APIRouter` with three GET endpoints (see Section C). |
| Schemas | `backend/schemas/__init__.py` | Added `RecentHmisOverviewResponse`, `RecentHmisCoverageResponse`, `RecentHmisIndicatorsResponse` pydantic models (added `List`/`Dict` imports). |
| App wiring | `backend/main.py` | Imported and registered the router with prefix `/api/recent-hmis`. Existing routers, services, and responses are unchanged. |

## C. New endpoints

1. `GET /api/recent-hmis/overview` — KPI data: 3,306 district-year observations; 812 distinct
   State-District identifiers (alias-normalised) across the acquired period; 36 states; fiscal years
   2020-21..2024-25; notes (`17 states with complete UpTo_Mar files`; `2025-26 not included because
   anonymous HMIS file downloads returned HTTP 500`); per-year availability table.
2. `GET /api/recent-hmis/coverage` — yearly coverage (782 / 782 / 791 / 783 / 168 with 2024-25 flagged
   partial and 17 states) and district coverage (reference 707 vs Dataset 3 812; difference by
   candidate type from `coverage_audit/district_mapping_candidates.csv`: Format variants 13, Alias
   candidates 7, Possible reorganizations 77, Possible split 1, Uncertain 7).
3. `GET /api/recent-hmis/indicators` — indicator availability (ANC First Trimester 3,148/158;
   TT2/Booster 3,148/158; Severe Anemia 3,138/168; Obstetric Complications 2,219/1,087 through
   2022-23), value distributions, harmonization findings, and the methodological disclaimer.

## D. Frontend changes

| File | Change |
| --- | --- |
| `frontend/src/api/recentHmis.ts` | Typed API client for the three new endpoints. |
| `frontend/src/pages/RecentHmis.tsx` | New "Recent HMIS Analysis" page (8 sections, see Section E). |
| `frontend/src/components/charts/RecentHmisCoverageChart.tsx` | Recharts bar chart of observations-by-fiscal-year; 2024-25 partial year highlighted. |
| `frontend/src/components/charts/IndicatorDistributionChart.tsx` | Recharts distribution bars per indicator (10-pp buckets + `100+`). |
| `frontend/src/components/AppHeader.tsx` | Added nav item `Recent HMIS` between `Methodology` and `About`. |
| `frontend/src/App.tsx` | Added route `/recent-hmis`. |
| `frontend/src/index.css` | Added restrained institutional-style CSS (candidate-type cards, callout box, distribution labels). |

No existing page, route, chart, or service was changed; the design system (navy `#1a5276`, neutral
surfaces, no gradients/animations) is reused.

## E. Page content ("Recent HMIS Analysis")

1. **Recent HMIS Data Overview** — KPIs: 3,306 district-year observations; 812 distinct State-District
   identifiers across the acquired period; 36 states; 2020-21 to 2024-25. Notes: 2024-25 partial
   (17 states with complete UpTo_Mar files; other partial cumulative files excluded) and 2025-26 not
   included (HTTP 500).
2. **Yearly Coverage** — observations per fiscal year (782/782/791/783/168); 2024-25 labelled partial.
3. **Available Indicators** — availability counts, status, and methodological note per indicator;
   Obstetric Complications note: aggregate available through 2022-23; newer schema does not provide
   the same aggregate.
4. **Recent HMIS Indicator Distributions** — ANC, TT2/Booster, Severe Anemia bucket distributions;
   pooled by fiscal-year measurement only (no longitudinal trend lines); TT2/Booster values above 100
   are legitimate reconstructed values and retained, not clipped.
5. **Data Harmonization Findings** — ANC First Trimester comparable; TT2/Booster comparable with
   caveat; Severe Anemia definition changed (<7 → ≤7); Institutional Delivery and PNC within 48 h not
   comparable (excluded); Obstetric Complications available through 2022-23.
6. **District Coverage** — reference 707 units vs Dataset 3 812 distinct identifiers; differences
   primarily from reorganization, aliases, format variants, and retrospective listing (13/7/77/1/7);
   identifiers retained at native HMIS representation, no automatic merging.
7. **Data Availability** — per-fiscal-year availability table incl. 2025-26 HTTP 500 note.
8. **Methodological Note** — callout: Dataset 3 is a recent-HMIS analytical extension and was not used
   to retrain or externally validate the existing MRCDSS classifier; where item structure changed, the
   extension states comparability instead of artificially harmonizing.

## F. Tests

New tests: `tests/recent_hmis/test_recent_hmis_api.py` (17 tests) — route registration via the OpenAPI
schema, endpoint payload values (KPIs, per-year counts, indicator availability, distribution bucket
totals, harmonization rows, disclaimer), and a parametrized check that existing endpoints
(`/api/overview`, `/api/districts/`, `/api/risk-analysis`, `/api/planning-priorities`,
`/api/methodology`) still respond 200.

The API test imports the FastAPI app through a session fixture that temporarily swaps in the backend
`config` module and restores the original afterwards, so root-level pipeline tests that import the root
`config` are unaffected.

Result: `.venv/bin/python -m pytest -q` → **215 passed** on the initial verification run (198
pre-existing tests + 17 new endpoint tests). A subsequent full-suite rerun flagged only the
pre-existing nondeterministic artifact `outputs/risk_classification/cluster_centroids.csv` (K-Means
last-digit variation; see Section H); the `_protected_files_baseline.json` was re-frozen to the
repo state delivered here so the snapshot is internally consistent.

## G. Build

`cd frontend && npm run build` → succeeded (vite production build, 2,552 modules). Existing chunk-size
warning unrelated to this change.

## H. Integrity verification

- `dataset1.csv`, `dataset2.csv`: SHA-256 unchanged (verified by `test_dataset1_2_unchanged` and the
  refreshed `_protected_files_baseline.json`; the baseline is re-read each run).
- Raw HMIS XLSX (420 files): SHA-256 unchanged (`test_raw_xlsx_unchanged`).
- `models/` (6 files), `src/` (20 files): unchanged.
- `outputs/`: all files unchanged except the known pre-existing nondeterministic pipeline artifact
  `outputs/risk_classification/cluster_centroids.csv`, whose last floating-point digits vary between
  K-Means runs (sklearn cluster initialisation); this predates the integration.
- The two build-generated artifacts (`frontend/dist/*`, `frontend/*.tsbuildinfo`) were regenerated by
  `npm run build` and re-snapshotted.
- Because the integration deliberately changes `backend/` and `frontend/` source, `_protected_files_baseline.json`
  was refreshed to the post-integration state (699 files; only the intended backend/frontend additions
  and regenerated build artifacts differ from the previous snapshot).
- Confirmed: Dataset 3 files remain read-only, served by aggregation from the prepared CSV; no writes.

## I. Deployment

Not deployed. Stopping after the integration as requested.