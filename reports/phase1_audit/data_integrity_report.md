# Phase 1 Data Integrity Report — MRCDSS

**Date:** 2026-11-12  
**Scope:** Repository and data integrity audit (Phase 1, Foundation Stabilisation)  
**Audit mode:** Read-only inspection of code, raw data, derived artifacts, provenance records, and tests. This report is the only artifact created.  
**Status:** Audit complete.

**Important:** No source datasets, preprocessing logic, six-feature model definition, cluster labels, reported metrics, backend services, or frontend files were modified. No fixes were implemented.

---

## 1. Executive Summary

The repository and data layer are structurally sound. Historical row counts, year coverage, state/district counts, six-feature schemas, duplicate checks, provenance columns, raw-file hashes, Dataset 3 reconciliation, and unified-dataset reconciliation all pass.

Two **High-severity research-validity risks** remain:

1. **Era-confounded risk labels:** The K-Means-derived risk classes partially encode dataset era/source rather than maternal-health risk alone. Medium Risk is 93.4% Dataset 2, and Dataset 2 records are classified Medium 59.5% of the time versus 1.4% for Dataset 1.
2. **Unresolved Severe Anemia comparability:** `Severe_Anemia_Pct` is documented in the harmonization report as “UNCERTAIN” and “not safely harmonizable,” yet it remains one of the six primary modelling features and is the dominant differentiator of the Medium Risk cluster.

These are not file-corruption findings. They are concerns about the validity and interpretation of the derived risk profiles. They require documented acknowledgement, sensitivity analysis, and external validation; they do not justify silently changing the primary model now.

---

## 2. Repository Structure Summary

| Area | Purpose |
|---|---|
| `src/preprocessing/` | Raw D1/D2 loading, cleaning, percentage validation, median imputation, preprocessing report |
| `src/feature_selection/` | Harmonization of candidate features, harmonization validation, final six-feature selection |
| `src/clustering/` | K-Means risk clustering and cluster profiling |
| `src/classification/` | Supervised classification of derived risk labels |
| `src/explainability/` | SHAP-based feature attribution |
| `src/decision_support/` | Priority levels, contributing features, planning rules |
| `src/api/` | Shared API utilities |
| `backend/` | FastAPI application, routes, schemas, services |
| `frontend/` | React/TypeScript dashboard |
| `outputs/` | Preprocessed data, selected features, clustering, classification, explainability, DSS reports |
| `models/` | Persisted classification models |
| `data/recent_hmis/` | Raw HMIS files, inspection artifacts, Dataset 3 build, provenance, coverage audit |
| `data/unified/` | Unified historical + recent data layer and integration reports |
| `tests/` | Preprocessing, feature selection, clustering, classification, explainability, DSS, Dataset 3, coverage, unified, assistant API tests |
| `reports/phase1_audit/` | This audit report |

---

## 3. Dataset Inventory

| Dataset | Path | Rows | Columns | Period | Role |
|---|---|---:|---:|---|---|
| Dataset 1 | `dataset1.csv` | 6,293 | 166 | 2008–2016 | Historical raw source |
| Dataset 2 | `dataset2.csv` | 2,112 | 202 | 2017–2019 | Historical raw source |
| Preprocessed historical pool | `outputs/preprocessed_output.csv` | 8,405 | 290 | 2008–2019 | Cleaned/imputed historical pool |
| Candidate features | `outputs/selected_features/maternal_model_features.csv` | 8,405 | 12 | 2008–2019 | Eight candidate indicators |
| Final model features | `outputs/selected_features/final_model_features.csv` | 8,405 | 10 | 2008–2019 | Four keys + six modelling features |
| Risk clusters | `outputs/risk_classification/district_year_risk_clusters.csv` | 8,405 | 12 | 2008–2019 | Six features + `cluster_id` + `risk_class` |
| Decision support | `outputs/decision_support/district_decision_support.csv` | 8,405 | 12 | 2008–2019 | Risk/priority/planning outputs |
| District priority summary | `outputs/decision_support/district_priority_summary.csv` | 707 | — | 2008–2019 | One row per State–District |
| Dataset 3 | `data/recent_hmis/dataset3/dataset3_recent_hmis.csv` | 3,306 | 8 | 2020-21 to 2024-25 | Recent HMIS extension |
| Unified dataset | `data/unified/unified_mr_cdss_data.csv` | 11,711 | 24 | 2008–2025 coverage | Historical + recent, kept separate by era |

Raw HMIS inventory: 419 XLSX files plus `data/recent_hmis/raw/_manifest.json`. Dataset 3 uses 161 annual `UpTo_Mar` source files.

The six primary modelling features are:

1. `ANC_First_Trimester_Pct`
2. `TT2_Booster_Pct`
3. `Severe_Anemia_Pct`
4. `Institutional_Delivery_Pct`
5. `PNC_48h_Pct`
6. `Obstetric_Complications_Pct`

`IFA_Pct` and `SBA_Home_Delivery_Pct` are excluded for comparability reasons.

---

## 4. Actual vs Expected Counts

| Expectation | Actual | Result |
|---|---:|---|
| Dataset 1 covers 2008–2016 | 2008–2016 confirmed | PASS |
| Dataset 2 covers 2017–2019 | 2017–2019 confirmed | PASS |
| Combined historical rows = 8,405 | 6,293 + 2,112 = 8,405 | PASS |
| Historical district-state units = 707 | 707 | PASS |
| States/UTs = 36 | 36 in D1, 36 in D2, 36 combined | PASS |
| Historical modelling period = 2008–2019 | 2008–2019 | PASS |
| Dataset 3 rows = 3,306 | 3,306 | PASS |
| Unified rows = 11,711 | 8,405 historical + 3,306 recent | PASS |
| Final features = exactly six | Six features + four key columns = 10 columns | PASS |

### Historical rows by year

| Year | Rows | Source |
|---|---:|---|
| 2008 | 699 | D1 |
| 2009 | 699 | D1 |
| 2010 | 698 | D1 |
| 2011 | 698 | D1 |
| 2012 | 698 | D1 |
| 2013 | 698 | D1 |
| 2014 | 697 | D1 |
| 2015 | 703 | D1 |
| 2016 | 703 | D1 |
| 2017 | 704 | D2 |
| 2018 | 704 | D2 |
| 2019 | 704 | D2 |

### Dataset 3 rows by fiscal year

| Fiscal year | Rows | Notes |
|---|---:|---|
| 2020-2021 | 782 | Full annual panel |
| 2021-2022 | 782 | Full annual panel |
| 2022-2023 | 791 | Full annual panel |
| 2023-2024 | 783 | Full annual panel |
| 2024-2025 | 168 | Partial: 17 states with `UpTo_Mar` files |

---

## 5. Missing-Value Statistics

### 5.1 Historical raw data

Total raw missing values across all columns: **126,911**

- Dataset 1: 104,715
- Dataset 2: 22,196

### 5.2 Six primary historical features

Counts below are raw missing and invalid (>100) values that were set to missing and then median-imputed in the final feature pipeline. “Relevant imputed cells” excludes structural NaNs created because D1 and D2 use different source column names.

| Feature | D1 missing | D1 invalid >100 | D2 missing | D2 invalid >100 | Relevant imputed cells |
|---|---:|---:|---:|---:|---:|
| `ANC_First_Trimester_Pct` | 214 | 15 | 0 | 0 | 229 |
| `TT2_Booster_Pct` | 214 | 425 | 0 | 284 | 923 |
| `Severe_Anemia_Pct` | 608 | 23 | 26 | 59 | 716 |
| `Institutional_Delivery_Pct` | 214 | 179 | 0 | 136 | 529 |
| `PNC_48h_Pct` | 212 | 243 | 84 | 1,136 | 1,675 |
| `Obstetric_Complications_Pct` | 213 | 2 | 0 | 3 | 218 |
| **Total** | | | | | **4,290** |

The full preprocessing report accounts for **1,117,706** imputed cells when structural cross-source NaNs are included:

- Missing before cleaning: 126,911
- Invalid percentages (>100 or <0): 33,012
- Structural misalignment (D1/D2 different column names): 957,783

Final six-feature output has **zero missing values**, minimum 0, maximum 100.

### 5.3 Dataset 3 missingness

| Feature | Missing | Missing % of 3,306 | Notes |
|---|---:|---:|---|
| `ANC_First_Trimester_Pct` | 158 | 4.8% | No imputation |
| `TT2_Booster_Pct` | 158 | 4.8% | No imputation |
| `Severe_Anemia_Pct` | 168 | 5.1% | No imputation |
| `Obstetric_Complications_Pct` | 1,087 | 32.9% | 951 structural NaNs from 2023-24 onward plus 136 in-source gaps |
| `Institutional_Delivery_Pct` | 3,306 | 100% | Not available in recent schema |
| `PNC_48h_Pct` | 3,306 | 100% | Not available in recent schema |
| `SBA_Home_Delivery_Pct` | 3,306 | 100% | Not available in recent schema |

---

## 6. Invalid-Value Statistics

### Historical data

- Six primary features contain **2,505** values above 100; there are no negative values in the six features.
- Invalid values are converted to `NaN`, not clipped, then median-imputed.
- All-column invalid percentage count: 23,680 in D1 and 9,332 in D2.
- Negative values exist only in non-modelling percentage columns (immunization dropout), are treated as invalid, and number 1,928 in D1 and 253 in D2.

### Dataset 3

Dataset 3 preserves invalid values and records them in `percent_invalid_flags.csv` (1,955 flagged row-feature entries):

| Feature | Invalid >100 | Rationale |
|---|---:|---|
| `TT2_Booster_Pct` | 368 | Denominator is ANC registrations; TT2 plus booster may double-count women given both doses |
| `Severe_Anemia_Pct` | 5 | Preserved, not adjusted |
| `Obstetric_Complications_Pct` | 11 | Preserved, not adjusted |

This is a deliberate difference from the historical policy and is documented as a provenance/interpretation issue in §11.2.

---

## 7. Duplicate Checks

| Check | Result |
|---|---|
| Exact duplicate rows in `dataset1.csv` | 0 |
| Exact duplicate rows in `dataset2.csv` | 0 |
| Duplicate `(State, District, Year)` in D1 | 0 |
| Duplicate `(State, District, Year)` in D2 | 0 |
| Duplicate `(State, District, Year, source_dataset)` in final features | 0 |
| Duplicate keys in risk clusters | 0 |
| Duplicate keys in DSS output | 0 |
| Duplicate `(State, District, Year)` in Dataset 3 | 0 |
| Duplicate `(State, District, Year, source_dataset)` in unified data | 0 |

Three district names legitimately occur in more than one state:

- `Bilaspur` — Chhattisgarh and Himachal Pradesh
- `Hamirpur` — Himachal Pradesh and Uttar Pradesh
- `Pratapgarh` — Rajasthan and Uttar Pradesh

These are real same-name districts, not duplicate records.

---

## 8. District-State Mapping Findings

| Metric | Value |
|---|---:|
| States/UTs | 36 |
| Dataset 1 State–District units | 706 |
| Dataset 2 State–District units | 704 |
| Combined historical reference units | 707 |
| Dataset 3 State–District units | 812 |
| Dataset 3 units not in historical reference | 105 |

Structural differences:

- D1 has three districts absent from D2: `Narayanpet`, `Eluru`, `Alluri Sitharama Raju`.
- D2 has one district absent from D1: `Charki Dadri`.
- Coverage audit normalisation maps all 707 historical reference units successfully.

Cross-era state-name spelling differences:

| Historical spelling | Recent HMIS spelling |
|---|---|
| `Andaman And Nicobar Islands` | `Andaman & Nicobar Islands` |
| `Jammu And Kashmir` | `Jammu and Kashmir` |
| `The Dadra and Nagar Haveli And Daman And Diu` | `The Dadra and Nagar Haveli and Daman and Diu` |

These are spelling/case/punctuation variants, not new states. Raw names are intentionally preserved in the unified dataset; cross-era joins by raw `State` therefore require normalisation.

---

## 9. Provenance and Hash Integrity

### 9.1 Raw historical data

| File | SHA-256 |
|---|---|
| `dataset1.csv` | `47139383ff42d83a0b0d920046f6cc56fe3a051e8539e0824327d4494a1d6e95` |
| `dataset2.csv` | `612f002de33d3624c4104d4087e552d0de8dd81f6c08a7e0b82056d01621fadd` |

Both hashes match `data/recent_hmis/dataset3/_protected_files_baseline.json`.

### 9.2 Raw HMIS files

- 419 XLSX files plus `_manifest.json`
- All 420 baseline entries exist and match their recorded SHA-256

### 9.3 Dataset 3 source mapping

`data/recent_hmis/dataset3/source_file_mapping.csv`:

- 161 rows, 11 columns
- All 161 `local_path` files exist
- All 161 SHA-256 values match the actual files
- Mapping includes fiscal year, state, filename, cumulative month, server path, local path, hash, size, modification date, parsed district count, and duplicate-district names

### 9.4 Protected-file baseline

`data/recent_hmis/dataset3/_protected_files_baseline.json`:

- 730 entries
- 729 match
- 1 mismatch: `.gitignore`

| File | Expected SHA-256 | Actual SHA-256 |
|---|---|---|
| `.gitignore` | `0c3e6edae5cd404b848bf3b864a0a10a8e45e74c1ff6247791d69ca2df7d3b58` | `01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b` |

The mismatch is a policy/config file, not a data file.

`data/recent_hmis/dataset3/coverage_audit/_audit_assets_baseline.json`:

- 20 entries
- 19 match
- 1 mismatch: `data/recent_hmis/dataset3/_protected_files_baseline.json`, which is the expected cascade from the `.gitignore` baseline update

### 9.5 Leakage check

No recent HMIS records entered historical model training:

- `train_models.py` reads `outputs/risk_classification/district_year_risk_clusters.csv`
- `evaluate_models.py` reads the same risk-cluster output
- Clustering and sensitivity analysis read `outputs/selected_features/final_model_features.csv`
- Both files contain 8,405 rows covering 2008–2019 only
- The unified dataset and Dataset 3 are not used by the training scripts

### 9.6 Provenance gaps

- `data/recent_hmis/dataset3/dataset3_recent_hmis.csv` is not itself hash-pinned in `_protected_files_baseline.json`; raw HMIS files and the unified dataset are pinned.
- `source_file_mapping.csv` stores absolute local paths, making provenance machine-specific.

---

## 10. Integrity Test Status

Test suites exist for:

- `tests/test_preprocessing.py`
- `tests/test_feature_selection.py`
- `tests/test_final_features.py`
- `tests/test_clustering.py`
- `tests/test_classification.py`
- `tests/test_explainability.py`
- `tests/test_decision_support.py`
- `tests/test_sensitivity.py`
- `tests/recent_hmis/test_dataset3.py`
- `tests/recent_hmis/test_coverage_audit.py`
- `tests/recent_hmis/test_recent_hmis_api.py`
- `tests/unified/test_unified_dataset.py`
- `tests/assistant/test_assistant_api.py`

Static review confirmed the checks exist and cover schemas, row counts, duplicates, ranges, provenance, API registration, and unified-data invariants.

**Execution status:** The full suite was not executed during this audit because several tests are not read-only:

- `tests/test_preprocessing.py` calls `preprocess.run_pipeline()` and rewrites `outputs/preprocessed_output.csv`
- `tests/test_final_features.py` deletes and recreates `final_model_features.csv`
- `tests/test_feature_selection.py` deletes and recreates `maternal_model_features.csv`

Existing reports document a 16-passed Dataset 3 suite, but this audit did not independently rerun it.

**Test-quality observation:** `tests/unified/test_unified_dataset.py::test_source_files_byte_identical` checks existence, row counts, and column presence, not SHA-256 byte equality. Its name overstates what it verifies.

---

## 11. Problems Discovered

| ID | Severity | Problem | Affected files/datasets |
|---|---|---|---|
| H-01 | **High** | Risk labels are era-confounded | `final_model_features.csv`, `district_year_risk_clusters.csv`, clustering outputs |
| H-02 | **High** | Severe Anemia comparability remains unresolved but the feature is retained | `harmonization_validation_report.md`, `final_features.py`, `final_model_features.csv`, `district_year_risk_clusters.csv` |
| M-01 | Medium | Invalid-value policy differs between historical and recent data | `preprocess.py`, Dataset 3 files, unified dataset |
| M-02 | Medium | Median imputation pools D1/D2 for shared-name columns | `preprocess.py` |
| M-03 | Medium | State/district names are not harmonised across eras | `data/unified/*`, unified backend service |
| M-04 | Medium | Dataset 3 zero-denominator counts disagree across artifacts | `_build_run_summary.json`, `_zero_denominators.json` |
| M-05 | Medium | Some integrity tests rewrite artifacts; byte-identical test is weak | `tests/test_preprocessing.py`, `tests/test_final_features.py`, `tests/test_feature_selection.py`, `tests/unified/test_unified_dataset.py` |
| L-01 | Low | `drop_empty_rows()` is a no-op | `src/preprocessing/preprocess.py` |
| L-02 | Low | `.gitignore` no longer matches the protected baseline | `.gitignore`, `_protected_files_baseline.json` |
| L-03 | Low | Documentation drift on feature count and comparability | `README.md`, `src/preprocessing/config.py`, `data/unified/_build_unified.py` |
| L-04 | Low | Dataset 3 primary CSV is not hash-pinned | `dataset3_recent_hmis.csv`, `_protected_files_baseline.json` |
| L-05 | Low | Absolute local paths in source mapping | `source_file_mapping.csv` |
| L-06 | Low | 2024-25 recent HMIS is partial | `dataset3_recent_hmis.csv` |

---

### 11.1 High-Severity Research-Validity Risks

#### H-01 — Era-confounded risk labels

**Severity:** High (research validity and interpretation; data integrity is intact).

**What is confirmed**

- K-Means labels are derived from the six features in `final_model_features.csv`. They are not clinical ground truth.
- Cluster composition is highly era-dependent:

| Cluster / risk class | D1 rows | D2 rows | D2 share |
|---|---:|---:|---:|
| Cluster 0 / Low Risk | 3,931 | 515 | 11.6% |
| Cluster 1 / Medium Risk | 89 | 1,256 | **93.4%** |
| Cluster 2 / High Risk | 2,273 | 341 | 13.0% |

- Dataset-level risk distribution is strongly asymmetric:

| Source | Low Risk | Medium Risk | High Risk |
|---|---:|---:|---:|
| D1 (6,293 rows) | 3,931 (62.5%) | 89 (1.4%) | 2,273 (36.1%) |
| D2 (2,112 rows) | 515 (24.4%) | 1,256 (59.5%) | 341 (16.1%) |

- The Medium Risk cluster is 93.4% D2, and D2 records are 42 times more likely to be Medium Risk than D1 records (59.5% vs 1.4%).
- The Medium Risk cluster profile has median `Severe_Anemia_Pct` = 67.6, versus 3.6 in Low Risk and 4.9 in High Risk.
- Dataset 2 raw `Severe_Anemia_Pct` median is 52.95 versus 3.60 in Dataset 1.
- The supervised classification report shows Logistic Regression test accuracy 0.9958; the report itself notes feature-target leakage potential because labels and features are derived from the same data.

**Affected datasets/artifacts**

- `outputs/selected_features/final_model_features.csv`
- `outputs/risk_classification/district_year_risk_clusters.csv`
- `outputs/risk_classification/cluster_profiles.csv`
- `outputs/risk_classification/risk_classification_report.md`
- `outputs/decision_support/district_decision_support.csv`
- `outputs/decision_support/district_priority_summary.csv`
- `outputs/classification/classification_report.md`
- `data/unified/unified_mr_cdss_data.csv` (historical risk labels are carried through)
- Backend/frontend surfaces that display risk classes and priority levels

**Potential impact on validity and interpretation**

- Risk profiles may partly measure data-source era, reporting practice, or measurement scale rather than maternal-health risk.
- “Medium Risk” is not evenly distributed across eras and may be misleading when compared across 2008–2016 versus 2017–2019.
- DSS priority levels and planning focus that consume these labels may inherit the same era bias.
- Supervised model accuracy is inflated because the target is derived from the same six features; high accuracy does not establish clinical validity.
- Longitudinal trends that cross the D1/D2 boundary may reflect label artefacts rather than real change.

**Confirmed finding vs methodological concern**

- **Confirmed:** Cluster composition, class imbalance by source, and the clustering/classification pipeline design.
- **Methodological concern:** The degree to which era confounds true risk, the causal interpretation of clusters, and the appropriateness of applying one clustering solution across two measurement eras.

**Recommended sensitivity analysis**

- Re-run clustering within each era separately and compare cluster profiles and assignments.
- Report all clustering and classification metrics stratified by `source_dataset`.
- Test K = 2 through 6 and alternative clustering algorithms; report stability (e.g., bootstrap ARI).
- Standardise or rank-normalise features within era before clustering as a sensitivity scenario.
- Evaluate a model without `Severe_Anemia_Pct` and compare cluster composition and DSS priorities.
- Quantify how many State–District–Year units change risk class under each sensitivity scenario.

**Recommended external validation**

- Validate derived risk profiles against independent maternal-health outcomes or survey data (e.g., NFHS or clinical/administrative maternal outcome data) not used to construct the labels.
- Obtain domain-expert review of cluster profiles and risk ordering.
- Do not present derived classes as clinical diagnoses or validated risk predictions without external validation.

**Actions not taken:** Clusters were not relabelled, the six-feature model was not changed, source data were not modified, and reported metrics were not altered.

---

#### H-02 — Unresolved Severe Anemia comparability

**Severity:** High (research validity and interpretation; data integrity is intact).

**What is confirmed**

- The harmonization report classifies `Severe_Anemia_Pct` as **UNCERTAIN** and lists it under “Not safely harmonizable.”
- The same report documents:
  - D1 median = 3.6%; D2 raw median = 51.5% (selected-feature median 52.95%)
  - D1 maximum = 2087.6%; D2 maximum = 665.8%
  - 59 D2 values >100% and 23 D1 values >100%
- The feature remains in the final six-feature model.
- The feature is the dominant differentiator of the Medium Risk cluster (median 67.6%).
- Dataset 3 separately documents a definition change from Hb <7 to Hb ≤7 from 2023-24 onward and states it is a recent-HMIS indicator only, not claimed as harmonized with D1/D2.

**Affected datasets/artifacts**

- `outputs/selected_features/harmonization_validation_report.md`
- `src/feature_selection/final_features.py`
- `outputs/selected_features/maternal_model_features.csv`
- `outputs/selected_features/final_model_features.csv`
- `outputs/risk_classification/district_year_risk_clusters.csv`
- `outputs/risk_classification/risk_classification_report.md`
- `outputs/decision_support/district_decision_support.csv`
- `data/recent_hmis/dataset3/dataset3_recent_hmis.csv` (separate recent definition)
- `data/unified/unified_mr_cdss_data.csv`

**Potential impact on validity and interpretation**

- A feature with unresolved definition/measurement comparability may drive cluster assignment and risk labels.
- Medium Risk may reflect era-specific anemia measurement rather than anemia burden.
- SHAP importance and DSS “contributing indicators” may overstate the role of severe anemia.
- Recent-HMIS severe anemia is not directly comparable to historical severe anemia; cross-era comparisons would conflate definitions.

**Confirmed finding vs methodological concern**

- **Confirmed:** The distributional divergence, the harmonization report’s uncertainty classification, and the feature’s retention in the primary model.
- **Methodological concern:** Whether the divergence reflects true burden differences, data-collection changes, scaling/unit errors, or denominator changes. The dataset alone cannot determine the cause.

**Recommended sensitivity analysis**

- Re-run clustering without `Severe_Anemia_Pct` and compare cluster composition, risk ordering, and DSS priorities.
- Use robust scaling or within-era standardisation for this feature and compare assignments.
- Apply winsorisation/truncation sensitivity at plausible bounds and report class stability.
- If raw numerator/denominator fields permit, reconstruct the indicator under alternative severe-anemia definitions and test agreement.
- Report results separately for D1 and D2, and report how many units change risk class.

**Recommended external validation**

- Compare historical severe-anemia levels against independent sources (NFHS or state health reports) for overlapping periods.
- Obtain clinical/domain review of the indicator definition and denominator.
- Treat recent-HMIS severe anemia as a separate definitional series; do not pool it with historical severe anemia without an explicit harmonization study.

**Actions not taken:** The six-feature primary model was not changed, the feature was not removed, source data were not modified, and reported metrics were not altered.

---

### 11.2 Medium-Severity Findings

#### M-01 — Invalid-value policy differs by era

- Historical: invalid percentages (<0 or >100) are set to `NaN` and median-imputed.
- Recent HMIS: invalid values are preserved and flagged. TT2 >100 is explicitly documented as legitimate double-counting; Severe Anemia and Obstetric Complications anomalies are preserved but not adjusted.
- **Affected:** `src/preprocessing/preprocess.py`, `data/recent_hmis/dataset3/*`, `data/unified/unified_mr_cdss_data.csv`.
- **Impact:** A reader may assume one global invalid-value policy; recent invalid values remain in the data layer even though they are not used in historical training.
- **Recommendation:** Document the era-specific policy explicitly. If recent data are ever used for modelling, define whether to exclude, cap, or model the flagged values.

#### M-02 — Pooled median imputation for shared-name columns

- `Institutional_Delivery_Pct`, `PNC_48h_Pct`, and `Obstetric_Complications_Pct` share identical source column names across D1 and D2.
- After concatenation, missing values in these columns are imputed with a median pooled across both eras.
- **Affected:** `src/preprocessing/preprocess.py`.
- **Impact:** Imputed values may blend era-specific distributions, particularly where missingness or reporting quality differs by era.
- **Recommendation:** For future work, compare within-source median imputation against the current approach as a sensitivity analysis.

#### M-03 — State/district naming is not harmonised across eras

- Three state names differ by punctuation/case between historical and recent data.
- District names are native to each era; Dataset 3 has 105 units not in the 707 reference.
- **Affected:** `data/unified/*`, `backend/services/unified_service.py`.
- **Impact:** Raw-state joins split three states; district-level longitudinal joins require normalisation.
- **Recommendation:** Add or document a State–District alias crosswalk for analytical joins.

#### M-04 — Dataset 3 zero-denominator count inconsistency

- `_build_run_summary.json` reports Obstetric zero denominators = 0.
- `_zero_denominators.json` and the build report report 2.
- `indicator_counts.csv` confirms 2 rows with a zero Obstetric denominator, both with blank numerators.
- **Affected:** `data/recent_hmis/dataset3/_build_run_summary.json`.
- **Impact:** Low data impact; confusing provenance for anyone reconciling artefact counts.
- **Recommendation:** Correct the summary artefact in a later maintenance task.

#### M-05 — Test side effects and weak byte-identical test

- Three tests rewrite or delete/recreate generated outputs.
- `test_source_files_byte_identical` checks existence, row counts, and columns rather than SHA-256 equality.
- **Affected:** `tests/test_preprocessing.py`, `tests/test_final_features.py`, `tests/test_feature_selection.py`, `tests/unified/test_unified_dataset.py`.
- **Impact:** A full test run is not a clean read-only integrity check; the byte-identical claim is weaker than its name suggests.
- **Recommendation:** Add a read-only test profile and a SHA-256 comparison against the protected baseline.

---

### 11.3 Low-Severity Findings

- **L-01 — `drop_empty_rows` no-op:** `df.drop(...)` result is not assigned. No all-numeric-null rows currently exist, so impact is zero.
- **L-02 — `.gitignore` baseline mismatch:** The protected baseline expects a different `.gitignore` hash. This is not a data file.
- **L-03 — Documentation drift:** README/config refer to eight indicators while the final model uses six. `D3_COMPARABLE_INDICATORS` includes Severe Anemia despite the definition-change caveat.
- **L-04 — Dataset 3 CSV not hash-pinned:** The raw files and unified CSV are pinned; the primary Dataset 3 CSV is not in the protected baseline.
- **L-05 — Absolute paths in mapping:** `source_file_mapping.csv` stores machine-specific `local_path` values.
- **L-06 — Partial 2024-25 coverage:** 168 rows from 17 states; documented, but limits trend interpretation.

---

## 12. Recommended Corrections (Not Implemented)

These are recommendations for later phases. Nothing below was executed during this audit.

1. **Document the Severe Anemia decision.** Record explicitly that the feature remains in the primary model despite the UNCERTAIN harmonization status, and pair that decision with the sensitivity analyses in §11.1.
2. **Add era-stratified diagnostics.** Report clustering composition, classification metrics, and DSS priorities by `source_dataset`.
3. **Run the recommended sensitivity analyses.** Within-era clustering, leave-one-feature-out, robust scaling/winsorisation, alternative K, and cluster-stability checks.
4. **Clarify the recent-HMIS invalid-value policy.** State whether flagged invalid values are excluded from any future modelling, capped, or modelled as-is.
5. **Compare imputation strategies for shared columns.** Test within-source median imputation against the current pooled approach.
6. **Add a State–District crosswalk.** Normalise the three state-name variants and document district aliases for longitudinal joins.
7. **Correct the Dataset 3 zero-denominator summary artifact.**
8. **Harden the test suite.** Add a read-only integrity profile and replace the weak byte-identical test with SHA-256 checks.
9. **Resolve provenance gaps.** Add the Dataset 3 CSV to the protected baseline and make mapping paths portable.
10. **Update documentation drift.** Align README/config/unused constants with the six-feature primary model.

---

## 13. Confirmed Findings vs Methodological Concerns

| Topic | Confirmed | Requires Further Investigation |
|---|---|---|
| Historical row counts and coverage | 8,405 rows, 707 units, 36 states, 2008–2019 | — |
| Duplicates | No exact or key duplicates | — |
| Raw-file integrity | Dataset 1/2 and 419 HMIS XLSX match baseline hashes | — |
| Dataset 3 provenance | 161/161 mappings match | Dataset 3 CSV not independently hash-pinned |
| Unified reconciliation | 11,711 = 8,405 + 3,306; no duplicate keys; no recent risk labels | — |
| Recent-data leakage into training | None found | — |
| Risk labels | Strong era confounding and medium-cluster composition | Causal interpretation and stability under alternative methods |
| Severe Anemia | Distributional divergence and retention in primary model | Cause of divergence; true comparability; external validation |
| Imputation | Pooled medians for three shared columns | Magnitude of era-blurring and best sensitivity method |
| Invalid values | Historical vs recent policies differ | Appropriate handling if recent data enter future models |
| State/district mapping | 707 reference units, 105 recent additions, 3 state spelling variants | Best crosswalk design and analytical join policy |
| Test status | Some tests mutate outputs; one byte-identical test is weak | Full test execution in an isolated environment |

---

## 14. Concise Summary

- **Data integrity:** PASS. Row counts, year coverage, state/district counts, six-feature schemas, duplicate checks, raw-file hashes, Dataset 3 provenance, and unified reconciliation are consistent with expectations.
- **No leakage:** Recent HMIS data did not enter historical model training.
- **No changes made:** Source data, preprocessing, model definition, cluster labels, metrics, and frontend were untouched.
- **High-severity risk H-01:** Risk classes are era-confounded. Medium Risk is 93.4% D2; D2 is Medium 59.5% of the time versus 1.4% for D1. Cluster composition and derived labels require era-stratified sensitivity analysis and external validation.
- **High-severity risk H-02:** Severe Anemia is documented as UNCERTAIN/not safely harmonizable yet remains in the primary six-feature model and dominates the Medium Risk cluster. This requires documented acceptance, sensitivity analysis, and external validation.
- **Secondary issues:** Era-specific invalid-value policy, pooled median imputation for shared columns, cross-era naming inconsistency, a stale zero-denominator summary, and test/provenance hygiene gaps.

**Stop point:** This report is submitted for review. No fixes or model changes have been implemented.

---

## Appendix A — Audit Checks Performed

- Loaded and profiled `dataset1.csv`, `dataset2.csv`, `dataset3_recent_hmis.csv`, and `unified_mr_cdss_data.csv`.
- Recomputed row counts, column counts, year coverage, state counts, and State–District unit counts.
- Recomputed exact and key duplicate counts.
- Recomputed missing and invalid counts for the six primary features and for all percentage columns.
- Recomputed relevant imputation counts and reconciled them with `outputs/data_quality_report.txt`.
- Compared final feature columns with the documented six-feature contract.
- Recomputed risk-class distribution by source dataset and cluster composition.
- Verified `dataset1.csv` and `dataset2.csv` SHA-256 values.
- Verified all 161 Dataset 3 source mappings (existence and SHA-256).
- Verified all 730 protected-baseline entries and all 20 coverage-audit entries.
- Inspected training, preprocessing, feature-selection, clustering, classification, DSS, unified-build, and integrity-test code.
- Inspected Dataset 3 metadata, provenance, zero-denominator, invalid-value, and coverage artifacts.

## Appendix B — Reproduction Notes

Use the project virtual environment:

```bash
.venv/bin/python -B <script>
```

`python` is not available on `PATH` in this environment. `-B` prevents bytecode writes during read-only checks.

Full `pytest` was intentionally deferred because `tests/test_preprocessing.py` rewrites `outputs/preprocessed_output.csv`, `tests/test_final_features.py` recreates `final_model_features.csv`, and `tests/test_feature_selection.py` recreates `maternal_model_features.csv`. A future integrity run should snapshot generated outputs or execute in a disposable copy.

