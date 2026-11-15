# MRCDSS: A District-Level Maternal Health Risk Decision Support System
## Research Paper Draft (for internal review; not a submitted manuscript)

**Status:** Draft derived from actual project evidence. No external references are cited because none were verified as part of this project. All figures are computed from the repository artifacts (`outputs/`, `data/`) and the FastAPI service layer.

---

### Abstract

We present MRCDSS (Maternal Health Risk Decision Support System), a district-level decision-support prototype that derives maternal-health risk profiles from historical district-year indicators, replicates them with supervised models, explains them with SHAP, and maps them to planning priorities through a rule-based Decision Support System (DSS). The system uses a fixed six-feature set (ANC First Trimester, TT2 / Booster, Severe Anemia, Institutional Delivery, PNC within 48h, Obstetric Complications) across 8,405 historical district-year records (2008–2019; 707 state–district units; 36 states). Risk classes are derived using K-Means clustering (K=3) and replicated with Logistic Regression, Decision Tree, Random Forest, and XGBoost. A Recent HMIS extension (Dataset 3, 2020–2025; 3,306 records) provides contextual indicator evidence without retraining the historical model. We disclose structural limitations: feature–target circularity, train/test state–district overlap (100% of test units appear in training), weak cluster separation (silhouette 0.238), and no external clinical validation. The supervised metrics therefore measure label reproduction, not predictive performance.

---

### 1. Introduction

Maternal-health planning at the district level benefits from decision-support tools that synthesize routine health-management information into interpretable risk profiles. MRCDSS is a prototype built on district-level maternal-health records from NDAP/HMIS sources. Its outputs are intended to inform public-health planning discussions, not to diagnose patients or guide clinical care. This paper documents the system's construction, results, and limitations, with particular emphasis on the evaluation design and its constraints.

---

### 2. Data

#### 2.1 Historical modelling data (Datasets 1 and 2)

Two historical district-year sources were cleaned and harmonized into a shared six-feature space:
- Dataset 1: 6,293 records, 2008–2019
- Dataset 2: 2,112 records, 2008–2019
- Combined: 8,405 records; 707 state–district units; 36 states

Invalid percentage values (outside 0–100) were converted to null and median-imputed before modelling, so the final modelling table contains no missing feature values, not because the source data are complete. Two candidate features (IFA and SBA Home Delivery) were excluded due to cross-dataset harmonization uncertainty.

#### 2.2 Recent HMIS extension (Dataset 3)

Dataset 3 extends the system with 3,306 district-year records from 2020–2025 across 812 distinct state–district identifiers and 36 states. Annual coverage: 2020–21 (782 records, 36 states), 2021–22 (782, 36), 2022–23 (791, 36), 2023–24 (783, 36), and 2024–25 (168, 17 states; partial). The 2025–26 downloads returned HTTP 500 and were excluded. Four indicators are carried: ANC First Trimester, TT2 / Booster, Severe Anemia, and Obstetric Complications. Institutional Delivery and PNC within 48h are excluded as not comparable.

Missingness is not imputed in Dataset 3: ANC First Trimester 3,148 valid / 158 missing; TT2 / Booster 3,148 / 158; Severe Anemia 3,138 / 168; Obstetric Complications 2,219 valid / 1,087 missing (structural nulls from 2023–24 onward after the aggregate item disappeared). Out-of-range values are retained and flagged, never clipped: TT2 / Booster 368 flags (maximum 185.93), Severe Anemia 5 flags (maximum 354.55), Obstetric Complications 11 flags (maximum 762.43); 1,955 flagged cells in total.

#### 2.3 Comparability caveats

Severe Anemia uses a different hemoglobin threshold across periods (<7 g/dl through 2022–23, ≤7 g/dl from 2023–24). TT2 / Booster values can exceed 100 because TT2 and booster components may overlap. Because several indicators are not directly comparable across periods, Dataset 3 was not used to retrain the historical model.

---

### 3. Methods

#### 3.1 Feature set

Six final features were used consistently across clustering, classification, SHAP, DSS, and the dashboard:
`ANC_First_Trimester_Pct`, `TT2_Booster_Pct`, `Severe_Anemia_Pct`, `Institutional_Delivery_Pct`, `PNC_48h_Pct`, `Obstetric_Complications_Pct`.

Higher values indicate higher risk for Severe Anemia and Obstetric Complications; lower values indicate higher risk for the four service-coverage indicators (ANC, TT2, Institutional Delivery, PNC).

#### 3.2 Risk-profile derivation (unsupervised)

Records were standardized with StandardScaler and clustered with K-Means (K=3, `random_state=42`, `n_init=10`). Clusters were ranked by a raw-median risk heuristic to assign Low / Medium / High classes. Resulting cluster sizes: Low 4,446; Medium 1,345; High 2,614.

Cluster quality: silhouette 0.238081; Davies-Bouldin index 1.473643; Calinski-Harabasz index 2,276.14. K=3 was fixed for the three-class design rather than selected through a formal K-selection diagnostic.

#### 3.3 Supervised replication

Four supervised models (Logistic Regression, Decision Tree, Random Forest, XGBoost) were trained to reproduce the K-Means-derived risk classes using the same six features. A record-level, stratified 80/20 split (`random_state=42`) produced 6,724 training and 1,681 test records. Logistic Regression was selected by macro-F1.

#### 3.4 Explainability

SHAP values were computed on the Logistic Regression model's test set for the High Risk class. Global mean absolute SHAP: ANC First Trimester 4.7267; Institutional Delivery 4.5189; TT2 / Booster 3.0415; PNC 48h 2.2933; Severe Anemia 2.2747; Obstetric Complications 0.6331. Signed per-district SHAP direction is not stored; SHAP is treated as attribution, not causation.

#### 3.5 Decision Support System

A rule-based DSS maps each unit's risk class and SHAP contributing factors into a priority level (High / Medium / Low) and planning-focus areas. A separate "repeated priority" unit-level label flags units with at least two historical district-year records at the same priority level; it is not current or latest status.

#### 3.6 Unified layer

Historical and Recent HMIS rows are united (11,711 observations). State/district identity is normalized at the API boundary (case, punctuation, "&/and"-insensitive): 39 raw state strings collapse to 36 normalized states; 850 raw State–District entries collapse to 812 normalized units (38 duplicate normalized entries reconciled). Raw spelling aliases are retained for provenance.

---

### 4. Results

#### 4.1 Risk classes

Derived risk-class distribution over 8,405 historical district-year records: Low Risk 4,446 (52.9%), Medium Risk 1,345 (16.0%), High Risk 2,614 (31.1%).

Projected latest historical observation per unit (707 units): High Risk 91; Medium Risk 493; Low Risk 123.

Repeated-priority unit labels: repeated High 441; repeated Medium 220; repeated Low 46; insufficient history 0.

#### 4.2 Supervised model comparison

| Model | Accuracy | Macro-F1 | Macro ROC-AUC |
|-------|----------|----------|---------------|
| Logistic Regression | 0.995836 | 0.994984 | 0.999961 |
| Decision Tree | 0.941701 | 0.945073 | 0.956868 |
| Random Forest | 0.964902 | 0.967214 | 0.997936 |
| XGBoost | 0.969661 | 0.969256 | 0.998681 |

Logistic Regression was selected by macro-F1.

#### 4.3 Evaluation design (disclosed limitations)

- Labels derive from the same six features used for classification (feature–target circularity).
- The split is record-level: every test record belongs to a State–District unit also present in training (654 of 654 test units overlap; 100% of test records).
- No grouped or temporal validation was performed; no external clinical validation exists.
- Consequently, accuracy/F1/ROC-AUC measure reproduction of derived labels on seen units, not external predictive performance.

#### 4.4 Sensitivity (excluding Severe Anemia)

Silhouette falls slightly from 0.238081 to 0.231495. High Risk shrinks from 2,614 to 961, and 4,568 of 8,405 records (54.35%) change risk class. The near-similar silhouette values do not demonstrate label robustness; Severe Anemia has cross-dataset harmonization uncertainty (Dataset 1 median 3.6% vs Dataset 2 median 51.5%).

---

### 5. Discussion

The system is internally consistent and traceable: raw counts reconcile (6,293 + 2,112 + 3,306 = 11,711), source hashes are verified, and artifacts are reproducible. However, the results should be interpreted with caution:

1. The risk classes are derived analytical groups, not clinical diagnoses or ground truth.
2. Supervised metrics are label-reproduction metrics on overlapping train/test units; they cannot support predictive or clinical claims.
3. Cluster separation is weak (silhouette ≈ 0.238), K is fixed, and labels are sensitive to feature choice (54.35% class change when Severe Anemia is dropped).
4. Recent HMIS is contextual evidence only and was not used to retrain or re-classify.

The DSS planning focus is model-attributed guidance, not a verified needs assessment, and SHAP direction is not stored per district. No clinical thresholds are applied to indicator values.

---

### 6. Conclusion

MRCDSS demonstrates a reproducible, transparent pipeline for district-level maternal-health risk profiling and planning prioritization. Its value is as a planning-support and exploratory-analytics prototype. The disclosed evaluation limitations—circularity, unit overlap, weak cluster separation, and absence of external validation—mean the outputs must not be used for clinical decisions, resource-allocation commitments, or as evidence of predictive performance. Future work would require grouped/temporal validation, an independent outcome, external validation, and a justified K selection before any stronger claims could be made.

---

### Evidence summary

| Item | Value | Source |
|------|-------|--------|
| Historical records | 8,405 | outputs/risk_classification/district_year_risk_clusters.csv |
| State–district units (historical) | 707 | outputs/decision_support/district_priority_summary.csv |
| States | 36 | outputs/decision_support/district_priority_summary.csv |
| Years | 2008–2019 | clustering CSV |
| Six features | fixed | src/feature_selection/final_features.py |
| Clustering | K-Means K=3, random_state=42, n_init=10 | src/clustering/risk_clustering.py |
| Silhouette / DBI / CHI | 0.238081 / 1.473643 / 2276.14 | outputs/risk_classification/clustering_metrics.txt |
| Selected model | Logistic Regression (macro-F1) | outputs/classification/best_model_metrics.json |
| LR accuracy / F1 / ROC-AUC | 0.995836 / 0.994984 / 0.999961 | outputs/classification/model_comparison.csv |
| Train / test rows | 6,724 / 1,681 | src/classification/train_models.py |
| Test units overlapping train | 654 / 654 | backend/services/risk_analysis_service.py |
| SHAP records | 1,681 | outputs/explainability/shap_values_test.csv |
| Sensitivity (excl. Severe Anemia) | silhouette 0.231495; High Risk 2,614→961; 54.35% class change | outputs/risk_classification/sensitivity_without_severe_anemia/ |
| Dataset 3 records | 3,306 | data/recent_hmis/dataset3/dataset3_recent_hmis.csv |
| Dataset 3 units / states | 812 / 36 | backend/services/recent_hmis_service.py |
| Dataset 3 years | 2020–21 … 2024–25 (partial) | same |
| Unified observations | 11,711 | data/unified/unified_mr_cdss_data.csv |
| Normalized states / units | 36 / 812 | backend/services/unified_service.py |
