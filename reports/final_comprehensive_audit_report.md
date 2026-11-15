# MRCDSS Comprehensive Audit Report

**Repository:** `/Users/amulyapagidimarri/Desktop/MRCDSS`  
**Commit:** `453bfd0` (`main`, 2026-11-12)  
**Audit date:** 2026-11-12  
**Mode:** Read-only inspection. No project source, data, model, metric, DSS output, configuration, test, documentation, or existing report was modified.  
**Deliverable:** This report only.

---

## 0. Verdict Summary

| Area | Verdict | Basis |
|---|---|---|
| Structural data integrity | **PASS WITH LIMITATIONS** | Row counts, duplicates, year coverage, six-feature schemas, provenance, and many hashes reconcile. Several historical invalid-value and imputation issues remain. |
| Dataset 3 acquisition and panel construction | **PASS WITH LIMITATIONS** | 3,306 rows and 161 selected files reconcile; 2025-26 is absent, 2024-25 is partial, and definition changes/outliers remain. |
| Unified dataset | **PASS WITH LIMITATIONS** | 11,711-row union reconciles exactly; state/district identity is not fully normalized at the API layer. |
| Pipeline traceability | **PASS WITH LIMITATIONS** | Artifacts are reproducible and traceable, but the evaluation design is structurally circular and grouped/temporal validation is absent. |
| Clustering validity | **NEEDS CORRECTION** | Silhouette 0.238 is weak; K=3 is fixed rather than justified; the risk ranking is an unweighted raw-median heuristic; labels are highly unstable under feature removal. |
| Supervised model evaluation | **NEEDS CORRECTION** | The target is derived from the same six features; 100% of test rows belong to State–District units also present in training; metrics are label-reproduction metrics, not external validity evidence. |
| DSS semantics | **NEEDS CORRECTION** | “Persistent High” means any two High years, not current or consistent High; planning focus is absolute-SHAP attribution, not a needs assessment. |
| Backend/API | **NEEDS CORRECTION** | Core endpoints work, but unified identity defects and hardcoded/inconsistent outputs remain. |
| Frontend/UX | **NEEDS CORRECTION** | Historical 2016 records are presented as “currently flagged”; SHAP direction is hardcoded as risk-increasing; indicator thresholds are hardcoded without provenance. |
| Disha assistant | **NEEDS CORRECTION** | Grounding design is sound, but several deterministic paths overclaim validation or return record-level/historical results as if current. |
| Paper/manuscript consistency | **NOT VALIDATED** | No paper or manuscript draft was found in the repository. |
| Overall readiness | **NEEDS CORRECTION** | The system is a functional prototype, but it is not ready for research claims or user-facing decision use without the corrections below. |

**Bottom line:** The data plumbing and artifact construction are substantially better than the interpretive layer. The most serious problems are not missing files or broken routes; they are **validity and semantics**: circular supervised evaluation, weak/unstable clustering, an overpermissive persistence rule, historical records presented as current, and hardcoded SHAP direction.

---

## 1. Evidence Inventory and Reconciled Counts

### 1.1 Historical core

| Item | Value | Evidence |
|---|---:|---|
| Dataset 1 rows | 6,293 | `outputs/risk_classification/district_year_risk_clusters.csv` |
| Dataset 2 rows | 2,112 | same |
| Historical total | 8,405 | same |
| Historical years | 2008–2019 | same |
| State–District units | 707 | `outputs/decision_support/district_priority_summary.csv` |
| States | 36 | same |
| Risk classes | High 2,614; Medium 1,345; Low 4,446 | clusters CSV |
| Latest unit-level risk | High 91; Medium 493; Low 123 | `/api/districts/latest` projection |
| Persistence labels | Persistent High 441; Persistent Medium 220; Persistent Low 46; Insufficient History 0 | priority summary |
| DSS mapping mismatches | 0 | High→High, Medium→Medium, Low→Low |

### 1.2 Recent HMIS / Dataset 3

| Item | Value | Evidence |
|---|---:|---|
| Manifest files | 487 | `data/recent_hmis/raw/_manifest.json` |
| Downloaded and SHA-verified | 419 | `data/recent_hmis/acquisition_report.md` |
| Failed | 68 | all 2025-26, HTTP 500 |
| Downloaded bytes | 118,808,935 | acquisition report |
| Selected annual files | 161 | `dataset3/source_file_mapping.csv` |
| Actual selected-file bytes | 43,346,349 | filesystem sum |
| Rows | 3,306 | `dataset3_recent_hmis.csv` |
| State–District units | 812 normalized | build/quality reports |
| States | 36 | build/quality reports |
| Years | 2020-21, 2021-22, 2022-23, 2023-24, 2024-25 partial | build report |
| Rows by year | 782 / 782 / 791 / 783 / 168 | quality report |
| States by year | 36 / 36 / 36 / 36 / 17 | quality report |
| Source-map districts parsed | 3,306 | source mapping sum |
| Source-map SHA | 161/161 match | prior verification |
| Duplicate `(State,District,Year)` | 0 | quality report |

### 1.3 Unified layer

| Item | Value | Evidence |
|---|---:|---|
| Unified rows | 11,711 = 6,293 + 2,112 + 3,306 | `data/unified/unified_data_integration_report.md` |
| Historical era rows | 8,405 | unified CSV |
| Recent era rows | 3,306 | unified CSV |
| Normalized State–District units | 812 | unified reports |
| Raw state strings | 39 | unified overview |
| Raw State–District pairs | 850 | unified district list |
| Duplicate normalized keys | 38 | prior reconciliation |
| Recent-only raw entries | 143 | recomputed from unified service |
| Historical-only raw entries | 30 | recomputed from unified service |
| Unified raw keys with recent records | 820 | recomputed from unified service |

---

## 2. Prior Audit Consolidation

### 2.1 Data-integrity audit

The prior data-integrity audit found the structural layer sound:

- Historical row counts, years, states, and 707 units reconcile.
- No exact or key duplicates in the historical/unified sources.
- Six-feature schemas are present and fully populated in the historical modelling table.
- Dataset 3 and unified reconciliations are exact.
- Provenance columns and source hashes are broadly present and consistent.

Limitations that remain material:

- Historical invalid percentages are converted to `NaN` and **median-imputed** rather than excluded: 23,680 invalid values in D1 and 9,332 in D2.
- Missingness is imputed with medians pooled across D1 and D2, which can blend era-specific distributions.
- The historical final six-feature table has zero missing values because imputation is applied before modelling, not because the source data are complete.
- Recent HMIS invalid values are **preserved**, not median-imputed, so the project has two different invalid-value policies across eras.
- The source mapping’s `file_size_bytes` values are rounded metadata: all 161 entries differ from actual filesystem size; their sum is 41,400,000 while actual bytes are 43,346,349.

### 2.2 ML-pipeline audit

The prior ML audit found the following high-impact issues, all reconfirmed in this audit:

- **Feature-target circularity:** K-Means labels are derived from the same six features used to predict them.
- **Near-perfect metrics are expected:** Logistic Regression reports accuracy 0.995836, macro-F1 0.994984, and ROC-AUC 0.999961 on derived labels.
- **No grouped or temporal validation:** the split is random at the record level, not grouped by State–District or held out by year.
- **Weak cluster separation:** Silhouette 0.238081; five-feature sensitivity 0.231495.
- **Unstable labels:** removing Severe Anemia changes risk class for 54.35% of records; High Risk shrinks from 2,614 to 961 and Medium expands from 1,345 to 3,697.
- **Unnormalized cluster ranking:** the risk ranking is an additive raw-median score; the four protective features dominate the sum, so the High Risk cluster is largely “low protective coverage,” not necessarily high measured risk.
- **Severe Anemia problem:** the Medium cluster is 93.4% D2 and has a Severe Anemia median of 67.6; the harmonization report classifies the feature as UNCERTAIN.
- **Double scaling:** Logistic Regression’s saved pipeline includes a scaler and training/evaluation also apply a separate scaler.
- **Pre-split imputation leakage:** median imputation is performed on the full dataset before train/test splitting.
- **Displayed profiles use means while ranking uses medians:** the API/UI show `*_mean`; the risk logic uses `*_median`.

### 2.3 DSS-pipeline audit

The prior DSS audit found five High-severity interpretation/presentation issues:

- “Persistent” is an any-two-year rule, not consistency or current status.
- Planning focus is model attribution, not a district needs assessment.
- SHAP direction is not stored, yet the UI presents factors as risk-increasing.
- Historical record-level priorities are presented as current priorities.
- Planning focus is strongly era/source-confounded.

These are not cosmetic. They directly affect what a planner would conclude from the dashboard.

---

## 3. Dataset 3 Audit

### 3.1 Acquisition and provenance

Dataset 3 is a standalone Recent HMIS extension. Acquisition is documented and reproducible:

- 487 manifest entries; 419 files downloaded and SHA-256 verified; 68 failed.
- All 68 failures are 2025-26 files returning HTTP 500; no authenticated session was used.
- Downloaded bytes are 118,808,935.
- The analytical panel uses 161 annual `UpTo_Mar` files:
  - 2020-21 through 2023-24: 36 states per year.
  - 2024-25: 17 states only.
- The 161 selected files total **43,346,349** actual bytes. The `file_size_bytes` column in `source_file_mapping.csv` is rounded and does not match actual bytes for any of the 161 files; it should not be used as a byte-level provenance check.
- All 161 selected-file SHA-256 hashes matched prior verification.
- No duplicate `(State, District, Year)` rows; no parse errors.

### 3.2 Counts and coverage

| Year | Rows | States |
|---|---:|---:|
| 2020-21 | 782 | 36 |
| 2021-22 | 782 | 36 |
| 2022-23 | 791 | 36 |
| 2023-24 | 783 | 36 |
| 2024-25 | 168 | 17 |

- 3,306 rows total.
- 812 normalized State–District units.
- 36 raw state strings.
- 820 raw State–District pairs in Dataset 3 before normalization.
- Coverage audit: 707 reference units matched, 105 new units, 0 reference units absent across the full window.
- 2024-25 is partial; 2022-23 has 20 reference names spelled differently, resolved by normalization.

### 3.3 Missingness

Dataset 3 does **not** impute missing values.

| Feature | Valid | Missing | Missing % |
|---|---:|---:|---:|
| ANC First Trimester | 3,148 | 158 | 4.8% |
| TT2 / Booster | 3,148 | 158 | 4.8% |
| Severe Anemia | 3,138 | 168 | 5.1% |
| Obstetric Complications | 2,219 | 1,087 | 32.9% |

- All 158 ANC/TT2 missing rows are fully blank district rows.
- Obstetric missingness includes 951 structural NaNs: 783 in 2023-24 and 168 in 2024-25, when the aggregate item disappeared.
- The remaining 136 Obstetric nulls are genuine missing cells in 2020-21 through 2022-23.

### 3.4 Out-of-range values

Values are never clipped. They are recorded in `percent_invalid_flags.csv`.

| Feature | >100 count | Max | Interpretation |
|---|---:|---:|---|
| ANC First Trimester | 0 | 100.00 | — |
| TT2 / Booster | 368 | 185.9296 | Documented double-counting of TT2/Td2 and booster |
| Severe Anemia | 5 | 354.5455 | Physiologically impossible numerator > denominator; data anomaly |
| Obstetric Complications | 11 | 762.4329 | Mixture of plausible >100% case counts and a severe Ghazipur outlier |

**Important:** these values are documented in the build/quality reports but are **not excluded or visibly flagged** in the backend/API/UI paths. A user can see percentages above 100 with no warning that the value is flagged or structurally impossible.

### 3.5 Comparability and exclusions

| Indicator | Status | Consequence |
|---|---|---|
| ANC First Trimester | Comparable | Included |
| TT2 / Booster | Comparable with caveat | Included; values can exceed 100 |
| Severe Anemia | Definition changed (`<7` to `<=7`) | Included in historical model; cross-era comparability unresolved |
| Institutional Delivery | Not comparable | Excluded from Dataset 3 |
| PNC within 48h | Not comparable | Excluded from Dataset 3 |
| Obstetric Complications | Available through 2022-23 only | Included with structural NaNs afterward |

### 3.6 Dataset 3 verdict

**PASS WITH LIMITATIONS.** The panel is well documented and internally consistent, but it is not a complete 2020–2025 panel: 2025-26 is absent, 2024-25 is partial, Severe Anemia definitions changed, and invalid values remain in the analytical file.

---

## 4. Unified Dataset Audit

### 4.1 Reconciliation

The unified dataset is structurally correct at the row level:

- `6,293 + 2,112 + 3,306 = 11,711`.
- Historical rows retain risk/priority/DSS fields.
- Recent rows retain null risk/priority/DSS fields.
- No accidental duplicate `(State, District, Year, source_dataset)` rows.
- Recent missingness exactly matches Dataset 3.
- Historical six-feature values are fully populated.

### 4.2 Identity defects

The unified layer does **not** normalize state/district identity at the API boundary:

- Raw state strings: **39**, not 36.
- Raw State–District pairs: **850**, not 812 normalized units.
- Duplicate normalized keys: **38**.
- Recent-only raw entries: **143**; historical-only raw entries: **30**.
- `get_unified_overview()` reports `n_states = df["State"].nunique()` at `backend/services/unified_service.py:110`, so it exposes 39.
- `get_unified_districts()` groups by raw `State`/`District` at `backend/services/unified_service.py:132-152`, so it exposes 850 entries.
- `get_unified_district()` does normalize before lookup at `backend/services/unified_service.py:155-168`, so detail lookup is more robust than list identity.

Known state variants:

1. `Andaman & Nicobar Islands` vs `Andaman And Nicobar Islands`.
2. `Jammu and Kashmir` vs `Jammu And Kashmir` (case variant).
3. `The Dadra and Nagar Haveli and Daman and Diu` case variants.

Consequences:

- Dashboard counts can say 39 states.
- Frontend exact-string matching between historical map records and recent records can fail for these variants (`frontend/src/pages/Overview.tsx:164-168`).
- Disha reports 820 recent raw districts rather than 812 normalized units.
- The recent-HMIS latest endpoint itself is correct because it groups on normalized keys (`backend/services/recent_hmis_service.py:211-233`), creating an inconsistency between endpoints.

### 4.3 Unified verdict

**PASS WITH LIMITATIONS** at the data-union level; **NEEDS CORRECTION** at the API identity/presentation layer.

---

## 5. Pipeline Traceability and Validity

### 5.1 Reproducibility

The pipeline is script-based and traceable:

- Preprocessing: `src/preprocessing/preprocess.py`
- Feature selection: `src/feature_selection/select_features.py`, `final_features.py`
- Clustering: `src/clustering/risk_clustering.py`
- Sensitivity: `src/clustering/sensitivity.py`
- Classification: `src/classification/train_models.py`, `evaluate_models.py`
- Explainability: `src/explainability/shap_analysis.py`
- DSS: `src/decision_support/decision_engine.py`, `planning_rules.py`
- Backend: `backend/services/*`, `backend/api/routes/*`
- Frontend: `frontend/src/pages/*`, `frontend/src/components/*`

The six modelling features are fixed in `src/feature_selection/final_features.py:8-15` and repeated consistently across clustering, classification, SHAP, DSS, and frontend.

### 5.2 Clustering validity

K-Means uses K=3, `random_state=42`, and `n_init=10` (`src/clustering/risk_clustering.py:40-58`). The saved metrics are:

| Metric | Value |
|---|---:|
| Silhouette | 0.238081 |
| Davies-Bouldin | 1.473643 |
| Calinski-Harabasz | 2276.144882 |
| Cluster sizes | 4,446 / 1,345 / 2,614 |

Problems:

- **Weak separation:** silhouette 0.238 is below the usual 0.25 heuristic for meaningful structure and does not establish three clinically distinct groups.
- **K is fixed, not justified:** no elbow, gap statistic, bootstrap stability, ARI/NMI, or repeated-seed analysis is reported.
- **Risk ranking is a heuristic:** `rank_clusters_by_risk()` sums raw feature medians, subtracting protective features and adding risk features (`src/clustering/risk_clustering.py:105-124`). The features are not standardized or weighted, so protective features dominate.
- **Label semantics are not clinical:** the High Risk cluster is characterized largely by low protective coverage, not necessarily high measured risk.
- **Feature removal destabilizes labels:** removing Severe Anemia changes risk class for 54.35% of records and changes cluster sizes sharply.
- **Mean/median mismatch:** the UI/API display profile means, while ranking and reports use medians (`backend/services/risk_analysis_service.py:44-60`; `outputs/risk_classification/cluster_profiles.csv`).

### 5.3 Supervised evaluation

The supervised models reproduce K-Means-derived labels using the same six features. This is circular by construction:

- Labels are generated from the six features (`src/clustering/risk_clustering.py:127-149`).
- The classifiers use the same six features (`src/classification/train_models.py:24-31`).
- The split is random at the record level, not grouped by unit or held out by time (`src/classification/train_models.py:65-69`; `src/classification/evaluate_models.py:36-44`; `src/explainability/shap_analysis.py:51-60`).
- Recomputing the exact split shows:
  - Train rows: 6,724; test rows: 1,681.
  - Unique units in train: 707; in test: 654.
  - **654 units overlap; 1,681/1,681 test rows (100%) belong to a unit also present in training.**
  - Only 53 units are train-only; no unit is held out for a clean unit-level test.

Consequences:

- Accuracy 0.995836, macro-F1 0.994984, and ROC-AUC 0.999961 are **label-reproduction** metrics, not evidence of clinical or external predictive validity.
- The model comparison is still useful as a consistency check, but it cannot support claims that the model “predicts” maternal risk.
- Model selection is described as based on “accuracy, F1, and ROC-AUC” (`backend/services/methodology_service.py:45-48`), while code selects by macro-F1 only (`src/classification/evaluate_models.py:138-145`). The chosen model happens to be highest on all reported metrics, but the selection criterion is misstated.

### 5.4 Scaling and imputation leakage

- **Pre-split imputation:** median imputation is applied to the full historical dataset before the train/test split (`src/preprocessing/preprocess.py:102-128`, `182-252`). Test values influence training medians.
- **Double scaling:** the Logistic Regression pipeline includes a `StandardScaler` (`src/classification/train_models.py:36-41`), while training/evaluation also fit/apply a separate external scaler (`src/classification/train_models.py:115-121`; `src/classification/evaluate_models.py:61-65`). The saved model is therefore not self-contained for raw-feature inference.
- **SHAP target mismatch:** global SHAP importance in `shap_analysis.py` always explains the High Risk class (`src/explainability/shap_analysis.py:70-87`), while the DSS computes SHAP for the predicted class (`src/decision_support/decision_engine.py:37-66`). The two outputs are not the same quantity unless every record is predicted High Risk.

### 5.5 SHAP direction

The saved test SHAP matrix has 1,681 rows × 6 features and no identifiers.

- Top-3 contributions: 2,833/5,043 = **56.2% negative**.
- Rows with at least one negative top-3 factor: 1,363/1,681 = **81.1%**.
- Rows with a negative top-1 factor: 899/1,681 = **53.5%**.

Top-3 appearance and negative counts:

| Feature | Top-3 appearances | Negative |
|---|---:|---:|
| ANC First Trimester | 1,306 | 727 |
| TT2 / Booster | 939 | 635 |
| Severe Anemia | 717 | 318 |
| Institutional Delivery | 1,283 | 727 |
| PNC 48h | 729 | 371 |
| Obstetric Complications | 69 | 55 |

The frontend nevertheless hardcodes all three DSS “contributing factors” as `direction: 'positive'` and labels them “Increases risk” (`frontend/src/pages/DistrictDetails.tsx:59-63`; `frontend/src/components/ContributingFactors.tsx:25-28`). This is factually wrong for most top-3 factors.

### 5.6 Pipeline verdict

**Reproducible but not externally valid.** The code and artifacts are traceable; the evaluation design cannot support performance or clinical claims.

---

## 6. Backend/API Audit

### 6.1 Route surface

Observed routes include:

- `GET /api/overview`
- `GET /api/districts`, `/states`, `/years`, `/latest`, `/{state}/{district}`
- `GET /api/planning-priorities`
- `GET /api/risk-analysis`
- `GET /api/methodology`
- `GET /api/recent-hmis/overview`, `/coverage`, `/indicators`, `/districts/latest`
- `GET /api/unified/overview`, `/districts`, `/districts/{state}/{district}`, `/years`
- `POST /api/assistant/chat`

Route ordering for `/api/districts` is correct: `/states`, `/years`, and `/latest` are registered before `/{state}/{district}` (`backend/api/routes/districts.py:37-57`), so they are not shadowed.

### 6.2 Confirmed API issues

1. **Unified state count:** `get_unified_overview()` returns raw `nunique()` = 39 (`backend/services/unified_service.py:107-110`).
2. **Unified district identity:** `get_unified_districts()` returns 850 raw-key entries and 38 duplicate normalized keys (`backend/services/unified_service.py:124-152`).
3. **Record-level vs latest:** `get_districts()` returns unsorted record-level rows (`backend/services/districts_service.py:22-69`). The correct latest projection exists separately at `backend/services/districts_service.py:140-180`, but callers must opt in.
4. **Hardcoded sensitivity values:** `risk_analysis_service.py:88-96` hardcodes `sensitivity_high_risk_size: 961` and fallback silhouette/DBI/CHI values instead of reading the sensitivity artifact.
5. **Incomplete response contracts:** several routes (`/api/unified/*`, `/api/recent-hmis/districts/latest`, `/api/districts/latest`) have no `response_model`, increasing schema-drift risk.
6. **Limited error handling:** unified/recent routes generally let `FileNotFoundError` become a 500; only district detail returns an explicit 404 (`backend/api/routes/districts.py:56-61`).
7. **Exact-name detail lookup:** `get_district_detail()` requires exact `State` and `District` strings (`backend/services/districts_service.py:79-80`); normalized aliases are not accepted on this route.

### 6.3 API verdict

**NEEDS CORRECTION.** The core payloads are usable, but the unified identity defects and record-level/current ambiguity are user-facing, not merely internal.

---

## 7. Frontend/UX Audit

### 7.1 Current vs historical

- The Overview “Districts currently flagged at the highest planning priority” table calls `getDistricts({ priority: 'High', page: 1, per_page: 8 })` (`frontend/src/pages/Overview.tsx:119-140`).
- That endpoint returns the first eight High Priority **records** in CSV order. They are 2016 rows; 3 of the first 8 are not High Risk in their latest year.
- The page labels them “currently flagged” (`frontend/src/pages/Overview.tsx:283`), which is false.
- The map itself uses `/api/districts/latest` (`frontend/src/pages/Overview.tsx:123-141`), so the map is current while the adjacent table is not.
- The Planning page presents record-level priority counts (2,614 / 1,345 / 4,446) without consistently labeling them as district-year records (`frontend/src/pages/Planning.tsx:156-168`).

### 7.2 SHAP direction

- `DistrictDetails.tsx` hardcodes all three top factors as positive (`frontend/src/pages/DistrictDetails.tsx:59-63`).
- `ContributingFactors.tsx` renders `direction === 'positive' ? 'Increases risk' : 'Decreases risk'` (`frontend/src/components/ContributingFactors.tsx:25-28`).
- Given that 56.2% of top-3 SHAP contributions are negative, the UI systematically mislabels direction.

### 7.3 Hardcoded interpretation thresholds

`DistrictDetails.tsx:19-29` applies clinical-looking thresholds without provenance:

- Adverse indicators: `≤15` acceptable, `≤25` moderate, `>25` intervention.
- Protective indicators: `≥50` above target, `≥30` moderate, `<30` below target.

These thresholds are not in the saved model/DSS artifacts and are not justified in the methodology. They should either be sourced, configurable, or removed.

### 7.4 Cluster labels

`RiskAnalysis.tsx:169-170` maps cluster IDs directly:

- 0 → Low Risk
- 1 → Medium Risk
- 2 → High Risk

This matches the current `cluster_profiles.csv` and `assign_risk_classes()` ordering, but the mapping is not returned by the API and will silently mislabel if the cluster numbering changes. It also embeds the derived-label semantics in the UI.

### 7.5 Wording and claims

Examples:

- “The map shows the validated MRCDSS district risk classification” (`frontend/src/pages/Overview.tsx:237`).
- “Current planning priorities are derived from the validated MRCDSS decision support system” (`frontend/src/pages/Planning.tsx:147`).
- “6 validated features” (`frontend/src/pages/Methodology.tsx:69`).

These words imply external/clinical validation that the artifacts do not support. The UI elsewhere says “not validated against external clinical datasets” (`frontend/src/pages/RiskAnalysis.tsx:397`), so the messaging is internally inconsistent.

### 7.6 Frontend verdict

**NEEDS CORRECTION.** The visualizations are functional, but the current/historical framing and SHAP direction are materially misleading.

---

## 8. Disha Assistant Audit

### 8.1 Strengths

- The design is retrieval-grounded: the LLM is optional; deterministic answers are used when Ollama is unavailable (`backend/services/assistant_service.py:1-22`).
- The system prompt forbids invented statistics, causal SHAP claims, and patient-level clinical advice (`assistant_service.py:48-59`).
- The assistant returns source labels and separates historical risk from recent HMIS evidence.
- It does not write data or retrain models.

### 8.2 Confirmed defects

1. **Coverage answer silently omits coverage.** `_dataset_answer()` reads `cov.get("candidate_mapping", {})` (`backend/services/assistant_service.py:1037-1045`), but `get_recent_hmis_coverage()` returns the mapping under `district_coverage` (`backend/services/recent_hmis_service.py:186`). The coverage sentence is therefore silently skipped.
2. **High-priority list is historical record-level.** `_high_priority_district_names()` calls `districts_service.get_districts(priority="High", ...)` (`assistant_service.py:533-548`). That endpoint returns record-level rows in CSV order; the first 15 are all 2016. It is not a latest or persistent list.
3. **Recent-district count is raw-key-based.** `_feature_index()` uses `get_unified_districts()` (`assistant_service.py:120-124`), so the “recent evidence available for N districts” path counts 820 raw keys, not 812 normalized units (`assistant_service.py:864-866`).
4. **“Validated” overclaim.** Disha repeatedly says “validated historical MRCDSS risk classification” and “validated historical methodology” (`assistant_service.py:563-577`, `826-838`, `894-904`, `996-1024`). No external validation artifact exists; the supervised metrics are label-reproduction metrics.
5. **Risk counts are correct but fragile.** `_risk_counts()` counts `latest_historical_risk_class` over the 850 raw unified entries (`assistant_service.py:524-530`). It happens to return 91/493/123 because historical records occupy 707 unique raw keys, but the method depends on that coincidence rather than on an explicit 707-unit projection.
6. **No paper/manuscript evidence.** Disha cannot ground manuscript claims because no manuscript was found.

### 8.3 Disha verdict

**NEEDS CORRECTION.** The architecture is sound; the deterministic wording and retrieval choices overstate validation and mix historical records with current status.

---

## 9. Paper/Manuscript Consistency

No paper, manuscript, thesis, PDF, DOCX, or TeX draft was found in the repository. There is no `docs/` directory. The only narrative artifacts are:

- `README.md`
- `reports/phase1_audit/*`
- Dataset 3 build/quality/coverage reports
- Output reports under `outputs/`

`README.md` is outdated:

- It documents `src/preprocessing/preprocess.py`, `src/api.main:app`, and `frontend/` as a placeholder (`README.md:17-57`), while the actual API is `backend/main.py` and the frontend is implemented.
- It does not describe the current unified/Disha architecture or the validation limitations.

Because no manuscript exists, **paper consistency cannot be assessed.** The system’s own claims are inconsistent with its evidence in the places noted above.

---

## 10. Consolidated Risk Register

| ID | Severity | Finding | Evidence | Impact | Priority |
|---|---|---|---|---|---|
| R-01 | Critical | Supervised evaluation is structurally circular and not grouped/temporally held out; 100% of test rows share a State–District unit with training | `risk_clustering.py:127-149`; `train_models.py:65-69`; `evaluate_models.py:36-44`; computed overlap | Near-perfect metrics cannot support predictive/clinical claims | P0 |
| R-02 | Critical | “Persistent High” means any two High years, not current or consistent High; 441 Persistent High vs 91 latest High; 351/441 not latest High; 247/441 High share <50% | `decision_engine.py:106-149`; DSS audit | Planners may target districts that are no longer High and miss currently High units | P0 |
| R-03 | Critical | Planning focus uses absolute SHAP + generic actions, not indicator direction/gaps; 26.91% top-1 extreme-opposite, 15.15% all top features favorable | `decision_engine.py:69-72`; `planning_rules.py:15-22`; DSS audit | Recommendations can be the opposite of the district’s actual need | P0 |
| R-04 | High | Historical record-level priorities are presented as current; Overview’s “currently flagged” table is 2016 | `Overview.tsx:119-140`, `283`; `districts_service.py:22-69`; DSS audit | Misleads users about current district status | P1 |
| R-05 | High | SHAP direction is hardcoded positive in UI; 56.2% of top-3 contributions are negative | `DistrictDetails.tsx:59-63`; `ContributingFactors.tsx:25-28`; SHAP matrix | Most factors are displayed with the wrong direction | P1 |
| R-06 | High | Unified API exposes 39 states / 850 raw keys / 38 duplicate normalized keys | `unified_service.py:107-152`; unified reports | Wrong counts, duplicate rows, failed exact-name joins | P1 |
| R-07 | High | Severe Anemia comparability unresolved while it drives cluster/DSS focus; Medium cluster 93.4% D2 with median 67.6; feature removal changes 54.35% of classes | prior ML audit; `cluster_profiles.csv`; sensitivity outputs | Risk labels and planning focus may encode era/source rather than need | P0 for research, P1 for UI |
| R-08 | High | Clustering is over-interpreted: silhouette 0.238, K=3 fixed, no stability/ARI/bootstrap, unnormalized raw-median ranking | `risk_clustering.py:40-124`; `clustering_metrics.txt` | Three “risk” groups are not validated as clinically meaningful | P1 |
| R-09 | High | Dataset 3 invalid percentages (>100) remain in analytical data and are not excluded/flagged in API/UI | `data_quality_report.md`; `percent_invalid_flags.csv` | Users can see impossible values without warning | P1 |
| R-10 | High | Disha high-priority list uses 2016 record-level records; “validated” wording overclaims | `assistant_service.py:533-548`, `563-577`, `826-838` | Assistant gives misleading current-status and validation answers | P1 |
| R-11 | Medium | Dataset 3 is incomplete: 2025-26 absent; 2024-25 partial (17 states); no external validation | acquisition/build reports | “2020–2025” coverage is overstated if read as complete | P1 |
| R-12 | Medium | Frontend clinical-looking thresholds (15/25/50/30) are hardcoded without provenance | `DistrictDetails.tsx:19-29` | Unjustified “acceptable/elevated” labels | P1 |
| R-13 | Medium | Cluster ID→risk label mapping is hardcoded in frontend | `RiskAnalysis.tsx:169-170` | Silent mislabeling if cluster ordering changes | P2 |
| R-14 | Medium | Backend hardcodes sensitivity high-risk size 961 and fallback metrics | `risk_analysis_service.py:88-96` | Displayed sensitivity values can drift from artifacts | P2 |
| R-15 | Medium | Pre-split imputation and pooled D1/D2 medians; historical invalid values median-imputed | `preprocess.py:102-128`, `182-252` | Mild leakage and era blending | P2 |
| R-16 | Medium | Double scaling in Logistic Regression save/evaluate path | `train_models.py:36-41`, `115-121`; `evaluate_models.py:61-65` | Saved model is not self-contained for raw-feature inference | P2 |
| R-17 | Medium | Mean profiles displayed while median ranking used | `risk_analysis_service.py:44-60`; `risk_clustering.py:105-124` | UI can show a profile inconsistent with the label logic | P2 |
| R-18 | Medium | Source mapping `file_size_bytes` is rounded and mismatches actual bytes for all 161 files | `source_file_mapping.csv`; filesystem check | Provenance metadata cannot be used for byte-level verification | P2 |
| R-19 | Low | Disha coverage sentence silently skipped due to key mismatch | `assistant_service.py:1037-1045`; `recent_hmis_service.py:186` | Missing useful coverage explanation | P2 |
| R-20 | Low | Disha reports 820 recent raw districts rather than 812 normalized units | `assistant_service.py:120-124`, `864-866` | Minor count inconsistency | P2 |
| R-21 | Low | ROC-AUC displayed as 1.0000 while saved value is 0.999961 | prior ML audit; UI | Overstates certainty | P3 |
| R-22 | Low | Several API routes lack response models/error handling | `unified.py`; `recent_hmis.py` | Schema drift and generic 500s | P3 |
| R-23 | Low | README documents outdated paths and calls frontend a placeholder | `README.md:17-57` | Onboarding/error risk | P3 |

---

## 11. Correction Roadmap

### P0 — Before any public research or operational claim

1. **Freeze performance claims.** Label current accuracy/F1/ROC-AUC as label-reproduction metrics, not predictive/clinical validation.
2. **Redesign evaluation.** Use grouped splitting by State–District (and ideally temporal holdout) and report fold-level uncertainty. Do not tune/select on the test set.
3. **Resolve or explicitly bound circularity.** Report that labels are derived from the same six features; if possible, define an independent outcome or external validation dataset.
4. **Fix “persistent” semantics.** Either implement latest/majority/consecutive logic or rename the label to “Repeatedly observed High Priority” and show observed years, high-year share, and latest class beside it.
5. **Fix planning focus.** Use signed SHAP and indicator direction/gaps; do not map absolute SHAP alone to “improve” actions. Report the 26.91% opposite-side problem.
6. **Fix current/historical presentation.** Replace the Overview table with `/api/districts/latest` or explicit historical labels; remove “currently flagged” from 2016 records.
7. **Fix SHAP direction in UI.** Store signed SHAP values or derive direction from the model; stop hardcoding “Increases risk.”
8. **Normalize identity at the API boundary.** Return 36 states / 812 normalized units; deduplicate raw keys or expose both raw and normalized counts explicitly.
9. **Do not claim external validation.** Remove “validated” from risk classes, features, and methodology unless an external validation artifact exists.

### P1 — Before user-facing deployment

1. Add invalid-value flags to Dataset 3 API/UI responses and disclose >100 values.
2. Decide and document an outlier policy for Severe Anemia and Obstetric Complications.
3. Justify K=3 and the feature set with stability analysis, ARI/NMI, bootstrap, and multiple seeds.
4. Replace raw-median cluster ranking with standardized/weighted logic or clearly label it as a heuristic.
5. Display medians consistently with ranking, or show mean and median side by side.
6. Replace hardcoded frontend thresholds with sourced/configurable rules.
7. Make cluster ID→risk label mapping data-driven.
8. Fix Disha coverage key, high-priority list, and historical/current wording.
9. Add grouped/temporal validation and sensitivity tests to the test suite.
10. Reconcile README and in-app wording with the audit findings.

### P2 — Hardening and maintainability

1. Add response models and explicit exception handling to unified/recent routes.
2. Remove hardcoded sensitivity values from `risk_analysis_service.py`.
3. Fix source mapping byte metadata.
4. Move imputation inside the train/test pipeline and compare within-source vs pooled imputation.
5. Make the saved Logistic Regression model self-contained or document the required external scaler.
6. Add CI checks for artifact schemas, row counts, duplicate keys, and claim wording.
7. Add a provenance panel in the UI that distinguishes historical risk from recent evidence.
8. Add unit tests for normalized state/district identity across all endpoints.

---

## 12. Readiness Verdicts

| Readiness question | Verdict | Reason |
|---|---|---|
| Is the repository structurally complete? | **PASS WITH LIMITATIONS** | Core data/model/DSS/API/UI artifacts exist and reconcile. README/provenance metadata need correction. |
| Is Dataset 3 reproducible? | **PASS WITH LIMITATIONS** | Acquisition and 161-file build are documented; 2025-26 missing, 2024-25 partial, definitions changed. |
| Is the unified dataset correct? | **PASS WITH LIMITATIONS** | Row union is exact; identity is not normalized at the API layer. |
| Is the ML pipeline traceable? | **PASS WITH LIMITATIONS** | Scripts and outputs are traceable; evaluation is circular and not grouped. |
| Are the risk classes clinically validated? | **NOT VALIDATED** | K-Means-derived labels; no external outcome; silhouette weak; Severe Anemia unresolved. |
| Are the supervised metrics evidence of predictive performance? | **NOT VALIDATED** | Same-feature label reproduction; 100% unit overlap between train and test. |
| Is the DSS safe for planning interpretation? | **NEEDS CORRECTION** | Persistence semantics and planning-focus logic can mislead. |
| Is the frontend suitable for user-facing claims? | **NEEDS CORRECTION** | Historical/current mixing, SHAP direction, hardcoded thresholds, and “validated” wording. |
| Is Disha suitable for grounded Q&A? | **NEEDS CORRECTION** | Good grounding architecture; several deterministic paths overclaim or return historical records. |
| Is the project ready for a paper submission? | **NOT VALIDATED** | No manuscript found; validity claims are not supported by current evaluation. |
| Is the project ready for operational decision support? | **NEEDS CORRECTION** | Not until P0/P1 corrections are implemented and validated. |

**Overall:** **NEEDS CORRECTION.** The project is a working analytical prototype with strong provenance. It is not yet a validated risk model or a safe current-status decision-support tool.

---

## 13. Evidence and Reproduction Notes

Read-only checks used in this audit included:

- Artifact row/key counts from `outputs/risk_classification/district_year_risk_clusters.csv`, `outputs/decision_support/*`, and `data/unified/unified_mr_cdss_data.csv`.
- Exact train/test reconstruction using the same split (`test_size=0.2`, `random_state=42`, `stratify=y`), followed by normalized State–District overlap analysis.
- SHAP sign counts from `outputs/explainability/shap_values_test.csv`.
- Dataset 3 missingness/range/count checks from `data/recent_hmis/dataset3/*`.
- Filesystem byte counts for the 161 selected Dataset 3 files.
- Static review of backend routes/services/schemas and frontend pages/components.
- No full test suite was run because some tests can overwrite or delete generated outputs.

Key reproducible facts:

- `6,293 + 2,112 + 3,306 = 11,711`.
- Historical risk: 2,614 High / 1,345 Medium / 4,446 Low.
- Latest unit risk: 91 High / 493 Medium / 123 Low.
- Persistent labels: 441 High / 220 Medium / 46 Low / 0 Insufficient History.
- Train/test: 6,724 / 1,681 rows; 654 overlapping units; 1,681/1,681 test rows in a training unit.
- SHAP top-3 negatives: 2,833/5,043.
- Dataset 3: 3,306 rows; 812 normalized units; 36 states; 161 source files; 43,346,349 actual bytes.
- Source manifest: 487 entries; 419 downloaded/SHA-verified; 68 failed; 118,808,935 downloaded bytes.

---

## 14. Audit Limitations

- This audit did not run the full test suite, start the API, build the frontend, or retrain models.
- It did not independently re-download HMIS files or re-verify every source hash; it relied on the documented SHA verification and prior audit results, while independently checking counts, mappings, and filesystem sizes.
- It did not access an external clinical dataset, so external validity cannot be assessed.
- It did not assess manuscript consistency because no manuscript was found.
- Severity/priority assignments reflect research and decision-support risk, not formal clinical risk classification.
- No source, data, model, metric, DSS output, configuration, test, documentation, or existing report was changed by this audit. The only created file is this report.
