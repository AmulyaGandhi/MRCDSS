# Machine Learning Pipeline Audit Report — MRCDSS

**Date:** 2026-11-12  
**Scope:** K-Means risk clustering, five-feature sensitivity analysis, supervised classification of derived labels, evaluation methodology, and research-validity interpretation.  
**Mode:** Inspect only. No existing file, dataset, model, metric, cluster label, or frontend file was modified. This report is the only artifact created.  
**Tests run:** No test that regenerates or overwrites existing outputs was executed. Verification used read-only file inspection and independent in-memory recomputation.

---

## 1. Executive Summary

The six-feature K-Means pipeline and the four supervised classifiers are structurally consistent:

- The six selected features are **exactly** the features used by K-Means.
- The supervised models use the same six features that generated the K-Means labels.
- StandardScaler, K-Means parameters, random seed, and split parameters are reproducible.
- Independently recomputed cluster labels and metrics match the saved outputs exactly.
- All four model metrics in `outputs/classification/model_comparison.csv` match independent recomputation to the stored precision.
- Logistic Regression is selected by the code using the highest macro F1-score; its saved confusion matrix matches the report.
- No report or UI text was found that presents these metrics as clinical prediction accuracy. The classification report and UI explicitly label the risk classes as derived, not clinical ground truth.

Three **High-severity research-validity risks** remain:

1. **Circular feature-target evaluation:** The labels are deterministically derived from the same six features used as model inputs. Near-perfect supervised performance is expected and measures reproduction of the clustering rule, not predictive or clinical validity.
2. **Era/source confounding is not evaluated in the supervised analysis:** Clustering artifacts document the D1/D2 composition, but classification evaluation uses a random split stratified only by risk class. It reports no era-stratified metrics, no temporal holdout, and no group-wise validation. An audit diagnostic shows the six features predict source era with Random Forest ROC-AUC ≈ 0.99.
3. **Severe Anemia comparability remains unresolved:** `Severe_Anemia_Pct` is retained in the primary six-feature model, dominates the Medium Risk cluster, and removing it changes risk-class assignment for more than half the records. This carries forward the prior High-severity finding.

Additional medium-severity concerns include an unnormalised, unweighted cluster-ranking heuristic; over-generous interpretation of clustering separation metrics; limited sensitivity design; double scaling in the Logistic Regression path; pre-split imputation leakage; and test-set model selection without temporal or grouped validation.

---

## 2. Inspection Scope and Evidence

### Files inspected

**Clustering**

- `src/clustering/risk_clustering.py`
- `src/clustering/sensitivity.py`
- `outputs/risk_classification/district_year_risk_clusters.csv`
- `outputs/risk_classification/cluster_profiles.csv`
- `outputs/risk_classification/cluster_centroids.csv`
- `outputs/risk_classification/clustering_metrics.txt`
- `outputs/risk_classification/risk_classification_report.md`
- `outputs/risk_classification/sensitivity_without_severe_anemia/*`

**Feature selection**

- `src/feature_selection/select_features.py`
- `src/feature_selection/final_features.py`
- `outputs/selected_features/maternal_model_features.csv`
- `outputs/selected_features/final_model_features.csv`
- `outputs/selected_features/harmonization_validation_report.md`

**Classification**

- `src/classification/train_models.py`
- `src/classification/evaluate_models.py`
- `models/logistic_regression.pkl`
- `models/logistic_regression_scaler.pkl`
- `models/decision_tree.pkl`
- `models/random_forest.pkl`
- `models/xgboost.pkl`
- `models/training_results.pkl`
- `outputs/classification/model_comparison.csv`
- `outputs/classification/best_model_metrics.json`
- `outputs/classification/classification_report.md`

**Tests and presentation**

- `tests/test_clustering.py`
- `tests/test_sensitivity.py`
- `tests/test_classification.py`
- `frontend/src/pages/RiskAnalysis.tsx`
- `frontend/src/api/riskAnalysis.ts`
- `backend/services/risk_analysis_service.py`

### Verification approach

- Read code to identify exact feature lists, parameters, seeds, split logic, label logic, and evaluation logic.
- Recomputed K-Means labels and metrics in memory without writing outputs.
- Recomputed all four classifiers' test metrics from the saved model artefacts using the same split.
- Compared those values with the saved CSV, JSON, and markdown reports.
- Ran additional **in-memory audit diagnostics** for source predictability, cross-era generalisation, adjusted Rand index, and risk-class agreement. These diagnostics are not existing project outputs and did not modify any file.

---

## 3. Feature-Set Verification

### 3.1 The six selected features are exactly the K-Means inputs

`src/feature_selection/final_features.py` defines:

```text
ANC_First_Trimester_Pct
TT2_Booster_Pct
Severe_Anemia_Pct
Institutional_Delivery_Pct
PNC_48h_Pct
Obstetric_Complications_Pct
```

`src/clustering/risk_clustering.py` defines the same six features in `FEATURES`, and `standardize()` calls `scaler.fit_transform(df[FEATURES])`. K-Means receives only those six standardized columns.

**Verified:** exact list match, exact order match, six features only. The clustering output contains the four keys, the six features, `cluster_id`, and `risk_class`.

### 3.2 Supervised models use the same features that generated the labels

`src/classification/train_models.py` and `src/classification/evaluate_models.py` both define the same six-feature list. The target is `risk_class`, which is produced by the K-Means pipeline.

The feature-target relationship is therefore:

```text
six features -> K-Means -> cluster_id -> risk_class
six features -> supervised classifier -> risk_class
```

No keys, `source_dataset`, `Year`, `cluster_id`, or other identifiers are used as model features. `tests/test_classification.py::TestDataSplit::test_no_target_leakage` verifies that these columns are absent from the feature list.

**Verified:** the supervised models use exactly the same six features as K-Means. This also confirms the structural circularity discussed in §8 and §10.

---

## 4. StandardScaler, K-Means Parameters, Seed, and Reproducibility

### 4.1 StandardScaler

`src/clustering/risk_clustering.py:49-52`:

```python
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df[FEATURES])
```

- Default configuration: mean centering and unit-variance scaling.
- Fitted on all 8,405 historical rows.
- No missing values remain in `final_model_features.csv`, so scaler behaviour is not affected by NaNs.
- Scaling is appropriate for K-Means because all six features are percentages but have different variances and ranges.

### 4.2 K-Means parameters

`src/clustering/risk_clustering.py:40-42, 55-58`:

| Parameter | Value | Notes |
|---|---|---|
| `n_clusters` | 3 | Fixed a priori, not selected by elbow/silhouette sweep |
| `random_state` | 42 | Reproducible |
| `n_init` | 10 | Multiple initialisations |
| `init` | default `k-means++` | Not explicitly set |
| `max_iter` | default 300 | Not explicitly set |
| `tol` | default 1e-4 | Not explicitly set |
| `algorithm` | default `lloyd` | Not explicitly set |

### 4.3 Reproducibility

Independent in-memory recomputation:

- Recreated `StandardScaler` and K-Means with `K=3`, `random_state=42`, `n_init=10`.
- Recomputed labels matched `district_year_risk_clusters.csv` exactly.
- Recomputed metrics matched `clustering_metrics.txt` exactly:
  - Silhouette: `0.238081`
  - Davies-Bouldin: `1.473643`
  - Calinski-Harabasz: `2276.144882`

**Verified:** the primary clustering is reproducible with the recorded seed and parameters.

### 4.4 Reproducibility caveat

The pipeline is reproducible for the same environment and same sklearn version. There is no recorded package version pin in the report and no cross-version reproducibility check. This is a low-severity reproducibility risk, not a current inconsistency.

### 4.5 Redundant K-Means refitting

`compute_centroids()` at `src/clustering/risk_clustering.py:75-94` refits K-Means twice, independently of the model that produced `labels`. With the same seed and data it returns the same centroids, and the saved centroid values are consistent with the saved clusters. However, the function ignores its passed `df` and does not reuse the already-fitted `km`.

**Impact:** no current metric discrepancy. It is a low-severity implementation fragility: centroid order and label alignment depend on the refit reproducing the same cluster ordering.

---

## 5. Cluster Profiles and Risk-Label Logic

### 5.1 Cluster profiles

Median profiles from `outputs/risk_classification/cluster_profiles.csv`:

| Cluster | Size | ANC | TT2 | Severe Anemia | Institutional Delivery | PNC 48h | Obstetric Complications |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | 4,446 | 67.70 | 89.20 | 3.60 | 69.80 | 69.70 | 5.80 |
| 1 | 1,345 | 81.70 | 90.30 | 67.60 | 74.60 | 68.80 | 5.70 |
| 2 | 2,614 | 39.70 | 75.45 | 4.90 | 42.30 | 57.10 | 3.20 |

### 5.2 Exact risk-label logic

`src/clustering/risk_clustering.py:22-32, 105-124`:

- Protective features: `ANC_First_Trimester_Pct`, `TT2_Booster_Pct`, `Institutional_Delivery_Pct`, `PNC_48h_Pct`.
- Risk features: `Severe_Anemia_Pct`, `Obstetric_Complications_Pct`.
- For each cluster:

```text
score = sum(median of risk features)
        - sum(median of protective features)
```

- Clusters are sorted by ascending score.
- Lowest score -> `Low Risk`; middle -> `Medium Risk`; highest -> `High Risk`.
- Every row in a cluster receives the cluster's risk class.

### 5.3 Computed risk scores

| Cluster | Protective sum | Risk-condition sum | Score | Assigned class |
|---|---:|---:|---:|---|
| 0 | 296.40 | 9.40 | -287.00 | Low Risk |
| 1 | 315.40 | 73.30 | -242.10 | Medium Risk |
| 2 | 214.55 | 8.10 | -206.45 | High Risk |

**Verified:** the saved `risk_class` assignments follow this exact rule.

### 5.4 Methodological concerns in the risk-label logic

1. **Raw medians are not normalised or weighted.** A one-point difference in ANC, TT2, institutional delivery, PNC, severe anemia, or obstetric complications counts equally in the score. The four protective features contribute a large sum (214–315) while the two risk-condition features contribute a smaller sum (8–73). The ranking is therefore dominated by protective coverage.
2. **Severe Anemia can flip the ranking.** Cluster 1 is pushed to Medium Risk almost entirely by its extreme Severe Anemia median (67.6), while its protective profile is the strongest of the three.
3. **The High Risk cluster has lower risk-condition indicators than the other clusters.** Cluster 2 has Severe Anemia 4.9 and Obstetric Complications 3.2, both lower than Cluster 0 (3.6 and 5.8) or Cluster 1 (67.6 and 5.7). It is labelled High Risk because of low protective care, not because of high measured risk conditions.
4. **The score has no clinical thresholds, no domain weights, and no uncertainty.** It is a heuristic ordering, not a validated risk score.
5. **Cluster-level labels are assigned uniformly.** There is no per-record probability, confidence, or uncertainty within a cluster.

**Interpretation:** the labels are best read as “lowest protective coverage,” “high severe-anemia burden with high protective coverage,” and “highest protective coverage.” The words Low/Medium/High Risk imply a clinical ordering that the underlying heuristic does not establish.

---

## 6. Clustering Evaluation Metrics and Correct Interpretation

### 6.1 Saved metrics

Primary six-feature model (`outputs/risk_classification/clustering_metrics.txt`):

| Metric | Value |
|---|---:|
| Silhouette Score | 0.238081 |
| Davies-Bouldin Index | 1.473643 |
| Calinski-Harabasz Index | 2276.144882 |

Five-feature sensitivity model:

| Metric | Value |
|---|---:|
| Silhouette Score | 0.231495 |
| Davies-Bouldin Index | 1.442950 |
| Calinski-Harabasz Index | 2661.670470 |

### 6.2 Correct interpretation

- **Silhouette 0.238** indicates weak cluster separation. A value below approximately 0.25 is commonly interpreted as no substantial structure; it does not validate three clinically distinct groups. The report’s wording “moderate cluster separation … acceptable for K=3” overstates the evidence.
- **Davies-Bouldin 1.474** has no universal threshold. It is only interpretable relative to alternative clusterings on the same feature space. Lower is better, but a single value is not evidence of a meaningful risk taxonomy.
- **Calinski-Harabasz 2276** is scale- and dimensionality-dependent. The sensitivity report uses it to compare five-feature and six-feature solutions, but CHI values across different feature spaces are not directly comparable as a model-selection criterion.
- **All three metrics are computed on the same data used to fit K-Means.** They measure geometric compactness/separation and are optimistic for structure discovery. There is no held-out clustering evaluation, bootstrap confidence interval, or stability analysis.
- **K=3 was fixed a priori.** There is no elbow, silhouette sweep, gap statistic, or documented domain justification for three clusters.
- **Metrics do not assess clinical meaningfulness.** They cannot establish that Low/Medium/High Risk corresponds to a clinically or programmatically meaningful ordering.

**Severity:** Medium. The metrics are arithmetically correct but their interpretation in the report is stronger than warranted.

---

## 7. Five-Feature Sensitivity Analysis

### 7.1 Design

`src/clustering/sensitivity.py`:

- Input: `outputs/selected_features/final_model_features.csv`
- Primary: six features.
- Sensitivity: removes `Severe_Anemia_Pct`, leaving five features.
- Same `StandardScaler`.
- Same `K=3`, `random_state=42`, `n_init=10`.
- Same additive median-score ranking, using the four protective features plus `Obstetric_Complications_Pct`.
- Outputs: `outputs/risk_classification/sensitivity_without_severe_anemia/`.

**Verified:** recomputed sensitivity labels and metrics match the saved outputs exactly.

### 7.2 Metric comparison

| Metric | Six-feature | Five-feature | Direction |
|---|---:|---:|---|
| Silhouette | 0.238081 | 0.231495 | 6F slightly higher |
| Davies-Bouldin | 1.473643 | 1.442950 | 5F slightly lower |
| Calinski-Harabasz | 2276.144882 | 2661.670470 | 5F higher |

The differences are small and mixed. CHI should not be treated as decisive across different feature spaces.

### 7.3 Cluster and risk-class changes

| Model | Cluster 0 | Cluster 1 | Cluster 2 | Risk-class totals |
|---|---:|---:|---:|---|
| Six-feature | 4,446 Low | 1,345 Medium | 2,614 High | Low 4,446 / Medium 1,345 / High 2,614 |
| Five-feature | 3,747 Low | 961 High | 3,697 Medium | Low 3,747 / Medium 3,697 / High 961 |

Removing one feature reduces the High Risk group from 2,614 (31.1%) to 961 (11.4%) and expands Medium Risk from 1,345 (16.0%) to 3,697 (44.0%).

### 7.4 Additional audit diagnostics

These values were computed in memory for this audit; they are not in the saved sensitivity report.

| Diagnostic | Value |
|---|---:|
| Adjusted Rand Index, cluster assignments | 0.214199 |
| Normalised Mutual Information, cluster assignments | 0.317757 |
| Raw cluster-ID agreement | 52.14% |
| Risk-class agreement | **45.65%** |

Risk-class transition table, six-feature (rows) to five-feature (columns):

| Six-feature class | Five-feature High | Five-feature Low | Five-feature Medium |
|---|---:|---:|---:|
| High Risk | 923 | 0 | 1,691 |
| Low Risk | 16 | 2,669 | 1,761 |
| Medium Risk | 22 | 1,078 | 245 |

More than half of all district-year records change risk class when one feature is removed.

### 7.5 D1/D2 composition

| Model / cluster | D1 | D2 | D2 share |
|---|---:|---:|---:|
| Six-feature Cluster 0 / Low | 3,931 | 515 | 11.6% |
| Six-feature Cluster 1 / Medium | 89 | 1,256 | **93.4%** |
| Six-feature Cluster 2 / High | 2,273 | 341 | 13.0% |
| Five-feature Cluster 0 / Low | 2,395 | 1,352 | 36.1% |
| Five-feature Cluster 1 / High | 778 | 183 | 19.0% |
| Five-feature Cluster 2 / Medium | 3,120 | 577 | 15.6% |

The five-feature solution reduces the extreme source concentration, but Cluster 0 remains 36.1% D2 versus 25.1% D2 overall. It does not “eliminate” era structure; it reduces one extreme form of it.

### 7.6 Sensitivity interpretation

- Severe Anemia is a major driver of source-based separation. Removing it substantially changes cluster composition and risk labels.
- The sensitivity report’s conclusion that the five-feature profile is “clearer” is qualitative. The metric evidence is mixed and not decisive.
- The report’s recommendation to keep the six-feature model rests partly on the argument that Severe Anemia is “validated” and was classified “UNCERTAIN, not NO.” This is a **research judgment**, not a statistical result. “UNCERTAIN” should not be treated as validation.
- The sensitivity analysis is a single leave-one-feature-out experiment at fixed K=3. It does not test alternative K, repeated seeds, bootstrap stability, alternative ranking weights, or external validation.
- The saved sensitivity report does not report ARI, NMI, or unit-level risk-class agreement. The audit finds that 54.35% of records change risk class, which is material and should be reported.

**Severity:** Medium for the sensitivity design and reporting; High when linked to the unresolved Severe Anemia comparability issue.

---

## 8. Supervised Models, Splitting, Leakage, and Evaluation Methodology

### 8.1 Models and hyperparameters

`src/classification/train_models.py`:

| Model | Configuration |
|---|---|
| Logistic Regression | Pipeline with `StandardScaler` + `LogisticRegression(max_iter=1000, random_state=42)`; defaults otherwise |
| Decision Tree | `DecisionTreeClassifier(random_state=42)`; defaults otherwise |
| Random Forest | `RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)`; defaults otherwise |
| XGBoost | `XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, n_jobs=-1, eval_metric="mlogloss")` |

No hyperparameter search or cross-validation is performed. The four models are evaluated with default or lightly specified settings.

### 8.2 Split and stratification

`src/classification/train_models.py:65-69` and `src/classification/evaluate_models.py:36-43`:

- 80/20 holdout split.
- `random_state=42`.
- `stratify=y` by risk class.
- Training: 6,724 rows.
- Test: 1,681 rows.

Class distributions:

| Class | Train | Test |
|---|---:|---:|
| Low Risk | 3,557 (52.9%) | 889 (52.9%) |
| High Risk | 2,091 (31.1%) | 523 (31.1%) |
| Medium Risk | 1,076 (16.0%) | 269 (16.0%) |

**Verified:** the split is correctly stratified by risk class.

### 8.3 Preprocessing leakage

- **StandardScaler:** fitted on `X_train` only and applied to `X_test`. No scaling leakage.
- **Median imputation:** performed earlier in `src/preprocessing/preprocess.py`, before the train/test split, using the full historical dataset. Test-row feature values therefore influenced the medians used to impute training rows. This is a mild but real preprocessing leakage.
- **K-Means labels:** generated on all 8,405 rows before the supervised split. This is not conventional train/test leakage because every row has a deterministic label, but it creates the structural feature-target circularity described below.
- The classification test suite checks the scaler mean/scale against training-only fitting but does not test pre-split imputation leakage. Its `test_no_target_leakage` checks only column exclusion, not circular label construction.

### 8.4 Structural feature-target circularity

The supervised target `risk_class` is a deterministic function of the six features:

```text
risk_class = rank(KMeans(StandardScaler(six features)))
```

A classifier trained on the same six features is therefore learning to reproduce a partitioning rule defined on those features. Near-perfect accuracy is expected and does **not** demonstrate:

- clinical predictive validity;
- generalisation to unseen populations;
- causal relationships;
- performance on independent maternal-health outcomes.

This circularity is documented in `outputs/classification/classification_report.md` as “feature-target leakage potential,” which is accurate. The evaluation design remains circular regardless of the caveat.

### 8.5 Evaluation methodology limitations

- Single 80/20 holdout, no cross-validation.
- No validation set for model selection; the best model is selected on the same test set used for reporting, producing optimistic selection.
- No temporal holdout. The random split mixes 2008–2019 district-years across train and test, so the same districts and adjacent years can appear in both sets.
- No grouped split by district or state.
- No era-stratified metrics.
- No confidence intervals, bootstrap, calibration, or statistical comparison of models.
- No external validation.
- XGBoost evaluation fits a new `LabelEncoder` on the test labels rather than reusing the training encoder. With the current stratified split the class order is identical and no numeric discrepancy occurs, but the saved model does not carry its label mapping. This is fragile.

**Severity:** Medium for general evaluation design; High for the combination of circularity and missing era/temporal validation.

---

## 9. Metric Verification Against Saved Outputs

### 9.1 All four model metrics

Saved values in `outputs/classification/model_comparison.csv` and independently recomputed values matched exactly to the stored six decimals:

| Model | Accuracy | Macro Precision | Macro Recall | Macro F1 | ROC-AUC (macro OVR) |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 0.995836 | 0.995720 | 0.994258 | 0.994984 | 0.999961 |
| Decision Tree | 0.941701 | 0.943001 | 0.947280 | 0.945073 | 0.956868 |
| Random Forest | 0.964902 | 0.965047 | 0.969512 | 0.967214 | 0.997936 |
| XGBoost | 0.969661 | 0.968013 | 0.970521 | 0.969256 | 0.998681 |

`outputs/classification/classification_report.md` matches these values at four-decimal display precision. `models/training_results.pkl` contains the same metrics and confusion matrices as the saved CSV/JSON.

**Verified:** all four model metrics match their saved CSV outputs.

### 9.2 Logistic Regression selection

`src/classification/evaluate_models.py:135-142` selects the model with the highest `f1_macro`.

| Model | Macro F1 |
|---|---:|
| Logistic Regression | 0.994984 |
| Decision Tree | 0.945073 |
| Random Forest | 0.967214 |
| XGBoost | 0.969256 |

**Verified:** Logistic Regression is selected by highest macro F1. It also has the highest accuracy, so the selected model is the same under either criterion.

The saved report correctly states “Highest macro F1-score.” The frontend text says “Selected based on highest accuracy” (`frontend/src/pages/RiskAnalysis.tsx:207`). This is a wording mismatch, not a model-selection discrepancy, because Logistic Regression is highest on both metrics.

Selection is performed on the test set, with no separate validation set. The reported test metrics are therefore selection-optimistic.

### 9.3 Logistic Regression confusion matrix

Saved matrix (`outputs/classification/best_model_metrics.json`), with label order `High Risk`, `Low Risk`, `Medium Risk`:

| Actual \ Predicted | High Risk | Low Risk | Medium Risk |
|---|---:|---:|---:|
| High Risk | 521 | 2 | 0 |
| Low Risk | 1 | 887 | 1 |
| Medium Risk | 2 | 1 | 266 |

- Total test rows: 1,681.
- Correct: 521 + 887 + 266 = 1,674.
- Errors: 7.
- Accuracy: 1,674 / 1,681 = 0.995836.

**Verified:** the confusion matrix is internally consistent with accuracy and matches `classification_report.md`.

### 9.4 Per-class verification

Logistic Regression per-class metrics in `best_model_metrics.json` match the report:

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| High Risk | 0.994275 | 0.996176 | 0.995224 | 523 |
| Low Risk | 0.996629 | 0.997750 | 0.997189 | 889 |
| Medium Risk | 0.996255 | 0.988848 | 0.992537 | 269 |

### 9.5 Presentation issues in the metrics

- **ROC-AUC rounding:** the report and UI display `1.0000`, while the saved value is `0.999961`. With derived labels, showing a perfect `1.0000` can overstate certainty. It is a rounding artefact, not a metric error.
- **Confusion-matrix ordering:** the matrix is ordered `High`, `Low`, `Medium`, which is alphabetical, not risk order. Readers can misread it if they assume Low/Medium/High.
- **Frontend interpretation text:** `frontend/src/pages/RiskAnalysis.tsx:239-247` says “Of the 8,405 records classified as High Risk by the model, 521 were correctly predicted…” This is factually confused:
  - 8,405 is the total historical dataset, not the number of High Risk or test records.
  - 521 is the count of **actual** High Risk test records correctly predicted, not “records classified as High Risk by the model.”
  - The test set contains 1,681 records; actual High Risk support is 523.
- **Selected-model wording:** “Selected based on highest accuracy” conflicts with the code’s macro-F1 selection.

These are presentation/interpretation issues, not changes to the saved metrics.

---

## 10. Clinical-Accuracy Framing

### 10.1 Reports and UI caveats

No incorrect clinical-accuracy claim was found. The key artifacts explicitly disclaim clinical validity:

- `outputs/classification/classification_report.md:4`: “K-Means risk classes are DERIVED labels, not independent clinical ground truth.”
- `outputs/classification/classification_report.md:93`: metrics measure “consistency with unsupervised profiles, not clinical accuracy.”
- `outputs/classification/classification_report.md:97`: “Results should not be interpreted as clinical prediction accuracy.”
- `frontend/src/pages/RiskAnalysis.tsx:186-193`: “these results indicate how well the supervised models reproduce the derived risk profiles; they should not be interpreted as clinical prediction accuracy.”
- `frontend/src/pages/RiskAnalysis.tsx:231`: “High accuracy reflects consistency with derived profiles, not independent clinical validity.”
- Additional caveats appear in `frontend/src/pages/RiskAnalysis.tsx:381-405`, `frontend/src/pages/About.tsx`, and `frontend/src/components/Disclaimer.tsx`.

**Verdict:** classification metrics are **not** incorrectly presented as clinical prediction accuracy. The presentation is appropriately caveated.

### 10.2 Residual interpretation risk

Despite the caveats, the following can still encourage over-interpretation:

- Displaying four model accuracies near 0.94–0.996 and a ROC-AUC of 1.0000.
- Calling the output “Selected Model” and “Performance Metrics” without a repeated adjacent statement that the target is derived.
- The API field names `predicted_High_Risk`, `predicted_Low_Risk`, `predicted_Medium_Risk` use predictive language.
- The frontend confusion-matrix interpretation text is factually inaccurate in its denominator and actual/predicted wording.

These are presentation risks, not misrepresentation of the target as clinical ground truth.

---

## 11. Era/Source Confounding in Model Evaluation

### 11.1 What is already documented

The clustering report explicitly documents:

- Medium Risk cluster is 93.4% D2.
- High Risk cluster is 86.9% D1.
- Severe Anemia differs sharply between D1 and D2.
- D1/D2 composition bias is a confounding factor.

The sensitivity report also reports D1/D2 composition for both the six-feature and five-feature solutions.

### 11.2 What the supervised evaluation does not do

`outputs/classification/classification_report.md` discusses derived labels, class imbalance, feature-target leakage, and external validation, but it does **not** report:

- metrics by `source_dataset`;
- test-set composition by era;
- temporal holdout or within-era validation;
- group-wise or district-wise validation;
- source predictability from the six features;
- how much of the accuracy depends on era-specific feature patterns.

The split is stratified only by `risk_class`, not by `source_dataset` or year.

### 11.3 Additional audit diagnostics

These are in-memory audit analyses, not saved project outputs.

**Source predictability from the six features**

A classifier trained to distinguish D1 from D2 using only the six features:

| Model | Accuracy | Balanced accuracy | ROC-AUC | 5-fold CV ROC-AUC |
|---|---:|---:|---:|---:|
| Logistic Regression | 0.9102 | 0.8557 | 0.9537 | 0.9515 |
| Random Forest | 0.9560 | 0.9391 | 0.9867 | 0.9898 |

The six features strongly encode source era. This supports the concern that the feature space is era-confounded.

**Cross-era generalisation**

Train on one era, test on the other, using the same six features:

| Direction | Model | Accuracy | Balanced accuracy | Macro F1 |
|---|---|---:|---:|---:|
| D1 -> D2 | Logistic Regression | 0.9579 | 0.9695 | 0.9596 |
| D1 -> D2 | Random Forest | 0.9257 | 0.9461 | 0.9194 |
| D2 -> D1 | Logistic Regression | 0.9840 | 0.9676 | 0.9753 |
| D2 -> D1 | Random Forest | 0.9379 | 0.9310 | 0.9180 |

The random-split Random Forest accuracy is 0.9649, while cross-era accuracy is 0.9257/0.9379. The random split is optimistic relative to a stricter era holdout. Logistic Regression remains high in both directions because it is reproducing the deterministic label rule, not because clinical validity has been established.

**Per-source test performance, Logistic Regression**

| Source | Test rows | Accuracy | Macro F1 | Actual class distribution |
|---|---:|---:|---:|---|
| D1 | 1,251 | 0.9944 | 0.9579 | Low 783, High 450, Medium 18 |
| D2 | 430 | 1.0000 | 1.0000 | Medium 251, Low 106, High 73 |

The D1 Medium Risk test support is only 18 records, so its per-class metrics are unstable. D2 is perfectly reproduced.

### 11.4 Conclusion

Era/source confounding is **partially documented in clustering artifacts but not adequately evaluated in the supervised model**. The random split, absence of source-stratified metrics, and strong source predictability from the six features mean the reported accuracy cannot be interpreted as evidence of generalisable or clinical validity.

**Severity:** High, continuing the prior H-01 risk.

---

## 12. Problems and Severity

### 12.1 High-severity research-validity risks

| ID | Problem | Evidence | Affected files |
|---|---|---|---|
| H-01 | Structural feature-target circularity makes near-perfect supervised metrics expected and non-generalisable | Target is derived from the same six features; LR 0.9958, ROC-AUC 0.999961; report itself notes feature-target leakage | `src/clustering/risk_clustering.py`, `src/classification/train_models.py`, `outputs/classification/*`, `models/*` |
| H-02 | Era/source confounding is not evaluated in supervised metrics | No source-stratified metrics; random split only by risk class; six features predict source with RF CV AUC 0.9898; Medium cluster 93.4% D2 | `src/classification/train_models.py`, `src/classification/evaluate_models.py`, `outputs/classification/classification_report.md`, `outputs/risk_classification/risk_classification_report.md` |
| H-03 | Severe Anemia comparability remains unresolved while the feature drives cluster assignment | 6F Medium cluster is 93.4% D2 and has Severe Anemia median 67.6; removing the feature changes risk class for 54.35% of rows; harmonization report says UNCERTAIN | `outputs/selected_features/harmonization_validation_report.md`, `src/feature_selection/final_features.py`, `src/clustering/risk_clustering.py`, `outputs/risk_classification/*` |

#### H-01 details

**Confirmed:** The target `risk_class` is a deterministic rank of K-Means labels fitted on the same six features used by the classifiers. A classifier can therefore reproduce the labels without learning any independent outcome. The Logistic Regression test accuracy of 0.995836 and ROC-AUC of 0.999961 are consistent with this design.

**Methodological concern:** The degree to which the classifier learns a genuine maternal-health pattern rather than the clustering rule. The current evaluation cannot distinguish these.

**Impact:** The metrics measure consistency with the derived taxonomy, not clinical prediction, external validity, or causal effect. They should not be used to select interventions or claim predictive performance.

**Recommendations:** Treat these metrics as reproduction metrics only. Add explicit “derived-label reproduction” wording wherever accuracy is shown. Do not compare against clinical benchmarks. If predictive validity is desired, define an independent outcome and validate against it.

#### H-02 details

**Confirmed:** The classification report contains no source-stratified metrics and the split is not stratified by source or year. The six features predict D1 vs D2 with high accuracy/AUC. The Medium Risk class is overwhelmingly D2.

**Methodological concern:** The classifier may exploit era-specific indicator distributions to reproduce labels. The random split shares district-years and time periods across train and test, inflating performance relative to a temporal or external holdout.

**Impact:** Reported accuracy is not evidence that the model generalises across eras, districts, or future years. It also means model-derived priorities may reflect era rather than current need.

**Recommendations:** Report all metrics by `source_dataset` and year; use temporal holdout (train 2008–2016, test 2017–2019) and grouped CV by district/state; quantify source predictability and include it as a diagnostic; compare within-era clustering; externally validate against independent data. Do not add `source_dataset` as a primary feature to “fix” this without a documented design decision.

#### H-03 details

**Confirmed:** Severe Anemia remains in the primary six-feature model despite the harmonization report’s UNCERTAIN classification. The six-feature Medium cluster is 93.4% D2 and has a Severe Anemia median of 67.6. Removing the feature changes risk class for 54.35% of records.

**Methodological concern:** The feature may encode measurement differences between D1 and D2 rather than anemia burden. The sensitivity report’s recommendation to keep it relies partly on calling it “validated” and treating UNCERTAIN as insufficient reason to exclude it.

**Impact:** The Medium Risk taxonomy and any downstream DSS priority that depends on it may be an artefact of era-specific measurement.

**Recommendations:** Document the retention decision explicitly. Run the sensitivity analyses described in §13. Resolve or externally validate the D1/D2 measurement difference before using the feature for cross-era conclusions. Do not change the primary model or labels in this audit.

---

### 12.2 Medium-severity methodological and implementation concerns

| ID | Problem | Evidence | Affected files |
|---|---|---|---|
| M-01 | Risk ranking uses unnormalised, unweighted raw medians | Score = sum(risk medians) − sum(protective medians); protective sums 214–315 vs risk sums 8–73; High cluster has lower risk-condition indicators | `src/clustering/risk_clustering.py:105-124` |
| M-02 | Clustering metrics are over-interpreted; K not justified; no stability analysis | Silhouette 0.238 described as “moderate/acceptable”; CHI compared across feature spaces; K=3 fixed; no bootstrap/ARI | `outputs/risk_classification/risk_classification_report.md`, `src/clustering/risk_clustering.py` |
| M-03 | Five-feature sensitivity is narrow and under-reports instability | Single leave-one-feature-out at K=3; no ARI/agreement in report; risk-class agreement 45.65%; recommendation is judgment-based | `src/clustering/sensitivity.py`, `outputs/risk_classification/sensitivity_without_severe_anemia/sensitivity_report.md` |
| M-04 | Logistic Regression uses double scaling and a non-self-contained saved model | Pipeline contains StandardScaler; training/evaluation also apply a separate saved scaler. Raw-feature prediction through the saved pipeline alone is invalid (audit test accuracy 0.1600) | `src/classification/train_models.py:36-41,115-121`, `src/classification/evaluate_models.py:61-64`, `models/logistic_regression.pkl`, `models/logistic_regression_scaler.pkl` |
| M-05 | Median imputation occurred before train/test split | Full-data imputation in preprocessing; test values influence training medians | `src/preprocessing/preprocess.py`, `outputs/preprocessed_output.csv` |
| M-06 | Random holdout and test-set model selection without temporal/group validation | Single 80/20 stratified split; no CV/validation set; best model selected on test; no confidence intervals | `src/classification/train_models.py`, `src/classification/evaluate_models.py` |
| M-07 | Displayed cluster profiles use means while ranking/report use medians | API returns `*_mean`; risk logic and report use `*_median`; e.g., Cluster 2 Severe Anemia mean 12.46 vs median 4.9 | `backend/services/risk_analysis_service.py`, `frontend/src/pages/RiskAnalysis.tsx`, `outputs/risk_classification/cluster_profiles.csv` |
| M-08 | XGBoost label encoder is fitted on test labels, not persisted from training | `evaluate_models.py:69-71` fits `LabelEncoder` on `y_test`; no saved encoder | `src/classification/evaluate_models.py`, `models/xgboost.pkl` |

---

### 12.3 Low-severity implementation and presentation issues

| ID | Problem | Affected files |
|---|---|---|
| L-01 | `compute_centroids()` refits K-Means twice independently of the label-producing model | `src/clustering/risk_clustering.py:75-94` |
| L-02 | UI says model is “Selected based on highest accuracy”; code selects highest macro F1 | `frontend/src/pages/RiskAnalysis.tsx:207`, `src/classification/evaluate_models.py:135-142` |
| L-03 | UI confusion-matrix interpretation incorrectly uses 8,405 as the High Risk denominator and conflates actual/predicted | `frontend/src/pages/RiskAnalysis.tsx:239-247` |
| L-04 | ROC-AUC displayed as 1.0000 rather than 0.999961 | `outputs/classification/classification_report.md`, `frontend/src/pages/RiskAnalysis.tsx` |
| L-05 | Backend hardcodes `sensitivity_high_risk_size: 961` and silhouette fallbacks instead of deriving them | `backend/services/risk_analysis_service.py:88-96` |
| L-06 | Cluster report says “No … risk scores, normalization … were created,” but StandardScaler and an additive risk score are used | `outputs/risk_classification/risk_classification_report.md:122` |
| L-07 | Frontend hardcodes `cluster_id` -> risk-class display mapping rather than using a risk field | `frontend/src/pages/RiskAnalysis.tsx:170-174` |
| L-08 | Unused static fallback `riskAnalysisData.ts` duplicates metrics with inconsistent field shapes | `frontend/src/data/riskAnalysisData.ts`, `frontend/src/types/riskAnalysis.ts` |

---

## 13. Recommended Sensitivity Analyses and Validation

These are recommendations. None were implemented, and the primary model, labels, metrics, and source data were not changed.

### 13.1 Clustering

1. **K selection:** sweep K = 2–8; report silhouette, Davies-Bouldin, CHI, and elbow/inertia; use gap statistic or silhouette-based selection with a documented criterion.
2. **Stability:** bootstrap resampling with adjusted Rand index; report mean ARI and confidence interval. Repeat K-Means with multiple seeds to confirm label stability.
3. **Within-era clustering:** fit separate K-Means models for D1 and D2; compare cluster profiles and risk ordering. This directly tests era confounding.
4. **Ranking sensitivity:** compare the current raw-median score with (a) standardized-centroid ranking, (b) equal-weighted standardized features, and (c) domain-weighted scores. Report risk-class movement.
5. **Feature-set sensitivity:** leave-one-feature-out for every feature, not only Severe Anemia; report ARI, risk-class agreement, and DSS priority movement.
6. **Outcome-anchored evaluation:** where independent maternal-health outcomes exist, test whether cluster membership is associated with them.

### 13.2 Reporting and validation

1. **Era-stratified metrics:** report accuracy, macro F1, per-class metrics, and confusion matrices separately for D1 and D2.
2. **Temporal validation:** train on 2008–2016 and test on 2017–2019; also test the reverse direction as a diagnostic.
3. **Grouped validation:** GroupKFold by district or state to avoid the same district appearing in train and test.
4. **Source-predictability diagnostic:** report how well the six features predict `source_dataset` (audit AUC was ~0.99 for Random Forest).
5. **Nested validation:** use a separate validation set or nested cross-validation for model selection; do not select on the test set used for reporting.
6. **Uncertainty:** bootstrap confidence intervals for all metrics; calibration curves for probabilistic models.
7. **External validation:** validate against independent district-level maternal-health outcomes or external datasets before making predictive claims.

### 13.3 Implementation hardening

1. **Logistic Regression scaling:** choose one coherent preprocessing path. Either fit the Pipeline on raw features and remove the external scaler, or fit the external scaler and remove the internal Pipeline scaler. Save the exact preprocessing contract with the model.
2. **Imputation:** move median imputation inside the train/test pipeline so medians are learned from training folds only.
3. **XGBoost labels:** persist the training `LabelEncoder` and reuse it at inference.
4. **Centroids:** compute centroids from the same fitted K-Means object that produced the labels.
5. **Cluster profile display:** display medians consistently with the ranking logic or show both mean and median explicitly.
6. **Presentation:** correct the confusion-matrix interpretation denominator; state “selected by highest macro F1”; show ROC-AUC as 0.99996 or add a note; keep the derived-label caveat adjacent to every accuracy display.

---

## 14. Confirmed Findings vs Methodological Concerns

| Topic | Confirmed | Requires further investigation |
|---|---|---|
| Feature set | Six features match across final features, K-Means, training, and evaluation | — |
| Clustering configuration | K=3, seed 42, n_init 10, StandardScaler defaults | Sensitivity to K and seed stability |
| Clustering reproducibility | Labels and metrics reproduce exactly | Cross-version reproducibility |
| Cluster labels | Additive median-score ranking; exact scores verified | Clinical meaningfulness of the ordering |
| Clustering metrics | Values correct | Correct interpretation, stability, out-of-sample structure |
| Sensitivity analysis | Five-feature run reproduces exactly; labels change substantially | Alternative K, weights, feature sets, stability |
| Supervised features | Same six features as K-Means; no key/source features | — |
| Split | 80/20 stratified by risk class; sizes verified | Temporal/grouped validation |
| Scaling leakage | Scaler fitted on train only | — |
| Imputation leakage | Imputation performed before split | Magnitude of impact |
| Metrics | All four match saved CSV exactly | Generalisability beyond random split |
| LR selection | Highest macro F1 and highest accuracy | Selection bias from test-set choice |
| LR confusion matrix | Matches JSON and report; 7 errors | — |
| Clinical framing | Reports/UI explicitly disclaim clinical accuracy | Residual over-interpretation risk |
| Era confounding | Strong source predictability; Medium cluster 93.4% D2 | Full era-stratified and external validation |
| Severe Anemia | Retained; drives Medium cluster; removal changes 54.35% of labels | Resolution of D1/D2 measurement comparability |
| LR scaling | Double scaling; raw-feature prediction through pipeline alone fails | Correct remediation path |
| XGBoost encoder | Fitted on test labels; not persisted | Deployment impact |

---

## 15. Concise Summary

- **Feature consistency:** PASS. The six selected features are exactly the K-Means inputs, and the supervised models use the same six features that generated the labels.
- **Clustering configuration:** PASS. StandardScaler defaults, K=3, `random_state=42`, `n_init=10`; labels and metrics reproduce exactly.
- **Cluster labeling logic:** verified. The rule is an unnormalised additive median score; the High Risk cluster is high because of low protective coverage, not high measured risk conditions.
- **Clustering metrics:** arithmetically correct but over-interpreted. Silhouette 0.238 is weak; CHI is not comparable across feature spaces; K=3 is not justified; no stability analysis.
- **Five-feature sensitivity:** verified mechanically, but under-reported. Removing Severe Anemia changes risk class for 54.35% of records; the six-feature Medium cluster is 93.4% D2.
- **Supervised metrics:** all four match the saved CSV exactly. Logistic Regression is selected by highest macro F1 and has the saved confusion matrix `[[521,2,0],[1,887,1],[2,1,266]]`.
- **Clinical framing:** no incorrect clinical-prediction claim found; reports and UI explicitly caveat the derived labels. Some UI wording and confusion-matrix interpretation need correction.
- **High-severity risks:** circular feature-target evaluation, inadequate era/source evaluation of supervised models, and unresolved Severe Anemia comparability.
- **No changes made:** no model, metric, label, dataset, or frontend file was modified. No output-regenerating test was run.

**Stop point:** This report is submitted for review. No fixes have been implemented.

---

## Appendix A — Read-Only Verification Performed

- Recomputed primary K-Means labels from `final_model_features.csv` and confirmed exact equality with `district_year_risk_clusters.csv`.
- Recomputed Silhouette, Davies-Bouldin, and Calinski-Harabasz values and confirmed exact equality with `clustering_metrics.txt`.
- Recomputed five-feature sensitivity labels and metrics and confirmed exact equality with saved sensitivity outputs.
- Recomputed all four classifiers' test metrics from saved `.pkl` models, saved scalers, and the same 80/20 stratified split; confirmed exact equality with `model_comparison.csv`.
- Recomputed Logistic Regression confusion matrix and per-class metrics; confirmed equality with `best_model_metrics.json` and `classification_report.md`.
- Computed ARI, NMI, cluster agreement, and risk-class agreement between six-feature and five-feature solutions.
- Trained in-memory diagnostic classifiers to predict `source_dataset` from the six features; no files were saved.
- Trained in-memory diagnostic classifiers under D1->D2, D2->D1, and temporal holdout splits; no files were saved.
- Compared cluster-profile means (API/UI) with medians (ranking/report).

## Appendix B — Reproduction Note

All diagnostics used `.venv/bin/python -B` and in-memory objects only. No `pytest` suite was executed because `tests/test_preprocessing.py`, `tests/test_feature_selection.py`, `tests/test_final_features.py`, and `tests/test_clustering.py::TestPipelineIntegration` can rewrite or regenerate existing outputs. The audit did not modify datasets, models, metrics, cluster labels, or frontend files.

