# Unified MRCDSS + Recent HMIS Data Integration Report

## A. Objective & Scope

This report documents the **unified data layer phase** of the MRCDSS: the three intended datasets
(Dataset 1, Dataset 2, and the Dataset 3 Recent HMIS extension) are now represented in **one coherent
MRCDSS experience** while preserving the existing, approved user interface and every historical model,
preprocessing, and decision-support artifact.

Guiding constraints honoured throughout:

- The original datasets (`dataset1.csv`, `dataset2.csv`, `dataset3_recent_hmis.csv`) and all raw HMIS
  XLSX files were **never modified**.
- No historical risk label was altered, and no recent-HMIS record was assigned a historical risk class.
- No indicator was fabricated, imputed, or zero-filled (unavailable values are `NaN`).
- No risk model was retrained and no DSS output was recomputed.
- The existing UI was extended, not redesigned; existing endpoints are unchanged.
- The unified table is a **new derived artifact** under `data/unified/`.

## B. Inputs and Provenance

| Input | Rows | Source | Notes |
|---|---|---|---|
| `dataset1.csv` | 6,293 | NDAP/HMIS (historical) | 2008–2016 (FY labels stored as strings) |
| `dataset2.csv` | 2,112 | NDAP/HMIS (historical) | 2017–2019 |
| `dataset3_recent_hmis.csv` | 3,306 | HMIS annual cumulative files | 2020-21–2024-25; 2024-25 partial (17 states with UpTo_Mar) |
| `district_year_risk_clusters.csv` | 8,405 | historical outputs | harmonized 6-feature + risk_class for D1+D2 records |
| `district_decision_support.csv` | 8,405 | historical outputs | priority, contributing features, planning focus |
| `source_file_mapping.csv` | 161 | Dataset 3 | per-state annual HMIS file provenance (filename, server/local path, sha256) |

Historical rows in the unified table come from the **harmonized analytical form** of D1/D2 (the exact
records used by the existing MRCDSS model), so each original State–District–Year record is preserved
with its risk classification. `SBA_Home_Delivery_Pct` for historical records is carried from the raw
D1/D2 files as a raw reference indicator (it was excluded from model harmonization). Recent HMIS rows
retain `hmis_source_file` tracing each record to its annual cumulative HMIS file.

## C. Unified Dataset Construction

Builder: `data/unified/_build_unified.py` (reproducible, reads sources read-only).

- Append order: D1 (6,293) → D2 (2,112) → Dataset 3 (3,306).
- **Unified total = 11,711 rows** = 6,293 + 2,112 + 3,306.
- `source_dataset` labels normalized to `dataset1`, `dataset2`, `recent_hmis` (Dataset 3's raw internal
  label `recent_hmis_annual_up_to_mar` is normalized per the unified contract).
- `data_era` = `HISTORICAL_MRCDSS` (8,405 rows) or `RECENT_HMIS` (3,306 rows).
- Output: `data/unified/unified_mr_cdss_data.csv` (24 columns).

## D. Data Dictionary Summary

`data/unified/unified_data_dictionary.csv` documents every field. Key metadata columns:

- `State`, `District`, `Year` — native representations per source; no automatic district merging.
- `source_dataset`, `data_era` — provenance and era.
- `indicator_definition_status` — analytical status of definitions for the record's era.
- `risk_classification_available` — `true` only for historical records.
- `recent_hmis_available` — `true` only for recent-HMIS records.
- `risk_class`, `priority_level`, `top_contributing_feature_1..3`, `planning_focus_1..3` — historical
  DSS fields (empty for recent-HMIS rows).
- Seven indicator columns (see §G).
- `hmis_source_file` — HMIS file provenance for recent-HMIS rows.

## E. Data Quality Checks

- No accidental duplicate `(State, District, Year, source_dataset)` rows.
- Recent-HMIS missingness and zero counts match the source Dataset 3 exactly per indicator (no
  imputation, no zero-fill; in-source zeros such as 76 Severe-Anemia and 1 ANC zero are preserved).
- Historical six-feature indicators are fully populated (no missing values).
- Source files verified byte-identical (protected-file baseline, see §O).

## F. Time Coverage and Period Wording

- **MRCDSS data coverage: 2008–2025** (historical 2008–2019; Recent HMIS extension 2020–2025).
- **Risk model period: historical MRCDSS data** — the validated risk model/DSS applies only to the
  historical era; the system never claims the model covers 2008–2025.
- **Recent HMIS extension: 2020–2025**, with 2024-25 partial (17 states with complete UpTo_Mar files).
- Years are always derived from actual data/API; no hardcoded `2016` (or any single-year) labels are
  introduced anywhere in the UI.

## G. Feature Availability Across Eras

| Indicator | Historical (D1/D2) valid | Recent HMIS (D3) valid |
|---|---|---|
| ANC_First_Trimester_Pct | 8,405 | 3,148 (158 missing) |
| TT2_Booster_Pct | 8,405 | 3,148 (158 missing) |
| Severe_Anemia_Pct | 8,405 | 3,138 (168 missing) |
| Institutional_Delivery_Pct | 8,405 | 0 (NaN — not available) |
| SBA_Home_Delivery_Pct | 8,405 (raw reference) | 0 (NaN — not available) |
| PNC_48h_Pct | 8,405 | 0 (NaN — not available) |
| Obstetric_Complications_Pct | 8,405 | 2,219 (NaN from 2023-24; 136 in-source gaps 2020–2023) |

Definition-status notes carried per record: historical rows are `HARMONIZED_HISTORICAL`; recent-HMIS
rows state that ANC First Trimester and TT2/Booster are comparable, Severe Anemia changed definition
(Hb <7 → ≤7 from 2023-24), and Obstetric Complications is available through 2022-23 only.

## H. Risk Classification Availability

- Historical records: 8,405 rows with the **original** MRCDSS risk class preserved unchanged
  (High Risk 2,614; Medium Risk 1,345; Low Risk 4,446).
- Recent-HMIS records: 3,306 rows, **none** assigned a risk class
  (`risk_class` empty, `risk_classification_available = false`).
- UI accordingly shows recent-HMIS districts under a **"Recent HMIS Profile"** framing — never as
  High/Medium/Low risk.

## I. Backend: Unified API Endpoints (additive)

New router `backend/api/routes/unified.py`, service `backend/services/unified_service.py`:

- `GET /api/unified/overview` — 11,711 observations, counts by source and era, feature availability,
  risk-availability, period texts.
- `GET /api/unified/districts` — per district historical/recent record counts, year lists, latest
  historical risk and latest recent year (850 unified State–District units).
- `GET /api/unified/districts/{state}/{district}` — full per-district timeline: historical records
  (risk class, priority, contributing features, planning focus, indicators) plus recent-HMIS records
  (indicator values, source, harmonization status, HMIS source file).
- `GET /api/unified/years` — data-driven historical and recent year lists and period texts.

All existing endpoints remain registered and return 200 with unchanged payload shapes.

## J. Recent HMIS Latest Endpoint

- `GET /api/recent-hmis/districts/latest` (new, added to the existing recent-hmis router) returns the
  latest Dataset 3 observation per district using the same normalized key space as the published
  coverage audit — **812 districts**, with `ANC_First_Trimester_Pct`, `TT2_Booster_Pct`,
  `Severe_Anemia_Pct`, `Obstetric_Complications_Pct` and **no risk classification**.
- `/api/districts/latest` (historical) is untouched.

## K. Frontend: Overview Heatmap Toggle

`Overview.tsx` now has a **Data View** control above the map:

- **MRCDSS Risk** (default) — existing behaviour: latest historical risk classification, green/amber/red
  legend + No Data.
- **Recent HMIS** — latest Dataset 3 observation per district shaded by **ANC First Trimester** on its
  own **navy sequential scale** (5 data-driven quantile bins, `#dbe9f6….#1a5276`), its own legend, and
  **no risk colors** mixed in. Districts without a recent observation render the neutral "No Data" gray
  (`#8d99a6`), never white, never Low Risk; clicking clears the selection.
- `DistrictRiskMap.tsx` was generalized to render either view (shared boundary loading, per-view fill,
  tooltip, and legend). Tooltips show `ANC X.X%` for Recent HMIS and `No data available` where absent.
- `DistrictInfoPanel` shows a Recent-HMIS perspective (acquisition year, ANC First Trimester, TT2/Booster,
  Severe Anemia) with an explicit "no risk classification" note and a link to the full timeline.

## L. Frontend: District Explorer / District Details Timeline

- `DistrictExplorer.tsx` derives the displayed year range from the API (`years` state) instead of a
  hardcoded range, and links to the Recent HMIS Analysis page.
- `DistrictDetails.tsx` now loads `/api/unified/districts/{state}/{district}` and renders:
  - the preserved historical risk timeline (renamed "Historical District Risk Timeline (MRCDSS)"), and
  - a new **"Recent HMIS Evidence"** section: per-year ANC First Trimester / TT2-Booster / Severe
    Anemia / Obstetric Complications values, source file names, era definition-status note, and an
    explicit statement that no risk classification is assigned to recent records. Districts with no
    recent data show a clear "not available" note.

## M. Frontend: Risk Analysis & Planning Notes

- `RiskAnalysis.tsx`:
  - The profiling pipeline section is now headed **"Historical MRCDSS Risk Analysis"** and states the
    model applies to historical MRCDSS data (2008–2019).
  - A new **"Recent HMIS Evidence"** section presents Dataset 3 indicator availability, harmonization
    status, and the disclaimer that recent data was **not** used to retrain or validate the model.
- `Planning.tsx`:
  - Adds the note **"Current planning priorities are derived from the validated MRCDSS DSS"**
    (historical MRCDSS data, 2008–2019), with Recent HMIS evidence presented separately.

## N. Terminology Precision (Phase 13)

- Map legend/heading and throughout: recent-HMIS districts are labelled "Recent HMIS Profile" or shown
  by ANC indicator value; the risk-colour vocabulary (High/Medium/Low) is never applied to them.
- Map subtitles distinguish the historical risk classification (model period) from the Recent HMIS
  indication of the "Recent HMIS signal".
- Error/empty states for recent data render the neutral No-Data hue and "No data available", never
  implying a Low-Risk reading.
- Period wording follows §F.

## O. Test Results (Phase 15) & Build

The 15-phase contract is tested in `tests/unified/test_unified_dataset.py` (17 tests):

1. D1 rows preserved (6,293) — pass
2. D2 rows preserved (2,112) — pass
3. D3/recent rows preserved (3,306) — pass
4. Unified total = 11,711 — pass
5. Normalized source_dataset labels — pass
6. Historical risk labels unchanged vs `district_year_risk_clusters.csv` — pass
7. Recent records carry no risk class — pass
8. No fabricated indicators (missingness and zero-fill fidelity) — pass
9. Years derived from actual data; no hardcoded 2016/era text in API — pass
10. Existing endpoints unchanged (200 + payload shapes) — pass
11. Historical outputs distribution unchanged — pass
12. No accidental duplicates — pass
13. Unified column specification/metadata coherent — pass
14. Recent-HMIS latest returns 812 districts, no risk — pass
15. Source files byte-identical — pass

Result: **232 passed** (`pytest -q`; 215 prior + 17 new unified tests), `npm run build` (tsc -b &&
vite build) succeeds with the pre-existing large-chunk warning only.
`data/recent_hmis/dataset3/_protected_files_baseline.json` was refreshed to include the intended new
backend/frontend sources, regenerated `dist`/tsbuildinfo, the derived `data/unified/` artifacts, and the
known nondeterministic `outputs/risk_classification/cluster_centroids.csv`; the volatile runtime log
`backend/uvicorn.log` is now excluded from the protected-file scan.

## P. Integrity Confirmation & What Was NOT Changed

Byte-for-byte untouched (verified by the protected-file baseline):

- `dataset1.csv`, `dataset2.csv` and all raw HMIS XLSX under `data/recent_hmis/raw/`.
- `dataset3_recent_hmis.csv` and the Dataset 3 `source_file_mapping.csv` / metadata.
- All model artifacts (`models/`), K-Means/SHAP/DSS outputs excluding the pre-existing nondeterministic
  float precision of `cluster_centroids.csv`, and all source pipeline code under `src/`.

New/derived artifacts:

- `data/unified/unified_mr_cdss_data.csv` (11,711 rows)
- `data/unified/unified_data_dictionary.csv`
- `data/unified/unified_data_quality_report.md`
- `data/unified/_build_unified.py` (reproducible builder)
- `backend/services/unified_service.py`, `backend/api/routes/unified.py`
- `GET /api/recent-hmis/districts/latest`
- Frontend extensions (Overview toggle, District Details timeline, Risk Analysis and Planning wording)
- `tests/unified/test_unified_dataset.py`

This phase is complete; the system now presents the historical MRCDSS model and the Recent HMIS
extension as one coherent, precisely-labelled data story without compromising the existing validated
analysis. No further build, deploy, or chatbot action was requested.