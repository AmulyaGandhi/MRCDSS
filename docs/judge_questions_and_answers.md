# MRCDSS — Judge Questions and Answers

Technically accurate questions and answers for academic evaluation. Every answer is grounded in the actual implementation and artifacts; nothing here is a claimed clinical validation or external predictive result.

## Contents

1. [System purpose and intended use](#1-system-purpose-and-intended-use)
2. [Data and features](#2-data-and-features)
3. [Risk derivation and clustering](#3-risk-derivation-and-clustering)
4. [Supervised models and evaluation](#4-supervised-models-and-evaluation)
5. [SHAP and explainability](#5-shap-and-explainability)
6. [Decision Support System (DSS)](#6-decision-support-system-dss)
7. [Recent HMIS (Dataset 3)](#7-recent-hmis-dataset-3)
8. [Unified dataset and identity](#8-unified-dataset-and-identity)
9. [Disha assistant](#9-disha-assistant)
10. [Methodological limitations and integrity](#10-methodological-limitations-and-integrity)

---

## 1. System purpose and intended use

**Q1. What is MRCDSS intended for?**
A: District-level public-health planning support. It helps planning teams explore historical maternal-health risk patterns, identify priority areas, and inform resource-allocation discussions. It is explicitly **not** a clinical diagnosis or treatment system and does not provide patient-level advice.

**Q2. Who are the intended users?**
A: Public-health planning teams at state and district levels, health program managers and policymakers, maternal-health researchers and analysts, and government officials responsible for health-resource allocation.

**Q3. Is MRCDSS a clinically validated predictive tool?**
A: No. The risk classes are derived analytical groups from K-Means clustering; there is no external clinical validation, and the supervised metrics reproduce derived labels on seen units rather than measure clinical predictive accuracy.

---

## 2. Data and features

**Q4. Which six features does the primary model use, and why are they fixed?**
A: ANC First Trimester, TT2 / Booster, Severe Anemia, Institutional Delivery, PNC within 48h, and Obstetric Complications. They are present and comparably defined in Datasets 1 and 2 and are used identically across clustering, classification, SHAP, DSS, and the dashboard, so the six-feature primary model is preserved end-to-end.

**Q5. Why were IFA and SBA Home Delivery excluded?**
A: IFA uses different tablet targets/coverage definitions across Datasets 1 and 2, and SBA Home Delivery denominator definitions were not sufficiently comparable; both were excluded due to cross-dataset harmonization uncertainty.

**Q6. How many historical records and state-district units are there?**
A: 8,405 district-year records (Dataset 1: 6,293; Dataset 2: 2,112) spanning 2008–2019 across 707 state-district units in 36 states.

**Q7. Were raw datasets modified?**
A: No. `dataset1.csv` (6,293 rows) and `dataset2.csv` (2,112 rows) and the raw HMIS files under `data/recent_hmis/raw/` are read-only and are hash-checked by tests.

---

## 3. Risk derivation and clustering

**Q8. How were the risk classes derived?**
A: K-Means clustering (K=3, `random_state=42`, `n_init=10`) on StandardScaler-normalized values of the six features. Cluster IDs were ranked by risk to produce Low / Medium / High classes. Cluster sizes: Low 4,446; Medium 1,345; High 2,614.

**Q9. Why K=3?**
A: K=3 was fixed for the Low/Medium/High three-class design rather than selected through a full K-selection diagnostic (no elbow, gap statistic, or stability analysis is reported). This is a disclosed limitation.

**Q10. How well separated are the clusters?**
A: Weak-to-moderate. Silhouette 0.238081, Davies-Bouldin 1.473643, Calinski-Harabasz 2276.14. A silhouette near 0.24 is below the usual ~0.25 heuristic for meaningful structure, so the three groups are analytical, not clinically distinct.

**Q11. Are the cluster labels stable?**
A: No. A sensitivity analysis excluding Severe Anemia changes the risk class of 4,568 of 8,405 records (54.35%) and shrinks High Risk from 2,614 to 961. Labels are materially sensitive to feature choice.

**Q12. Does the risk ranking use standardized features?**
A: No. The ranking is an additive raw-median heuristic, so unstandardized protective features can dominate. This is a disclosed heuristic limitation.

---

## 4. Supervised models and evaluation

**Q13. Which models were evaluated and which was selected?**
A: Logistic Regression, Decision Tree, Random Forest, and XGBoost. Logistic Regression was selected by macro-F1: accuracy 0.995836, macro-F1 0.994984, macro ROC-AUC 0.999961.

**Q14. Are these metrics evidence of predictive performance?**
A: No. The target labels are derived from the same six features the classifiers use (feature-target circularity). The split is record-level, not grouped by unit or held out by time: 6,724 train / 1,681 test rows, and all 1,681 test records belong to a State–District unit also present in training (654 overlapping units). The scores measure reproduction of K-Means-derived labels on seen units, not external or clinical accuracy.

**Q15. Is there grouped or temporal validation?**
A: No. `grouped_or_temporal_validation_completed` is false in the API evaluation design, and this is disclosed in the UI and methodology.

**Q16. What does "label-reproduction" mean here?**
A: The classifiers are trained to predict labels that were themselves computed from the same input features, so high accuracy is expected and does not indicate the model predicts an independent real-world outcome.

---

## 5. SHAP and explainability

**Q17. What does SHAP show in MRCDSS?**
A: How much each feature contributed to the Logistic Regression model's classification. The saved global test-set explanation targets the High Risk class: positive values push toward High Risk, negative values push away. Mean absolute SHAP ranking (test set): ANC First Trimester 4.7267, Institutional Delivery 4.5189, TT2 / Booster 3.0415, PNC 48h 2.2933, Severe Anemia 2.2747, Obstetric Complications 0.6331.

**Q18. Is SHAP direction shown for an individual district?**
A: No. Signed district-specific SHAP direction is not stored for individual records; the UI states "Contribution direction unavailable" and "Attribution does not establish causality."

**Q19. Does SHAP imply causation?**
A: No. SHAP indicates model attribution/contribution, not causation. This is stated in the SYSTEM_PROMPT given to Disha, on the District Details page, in Risk Analysis, and in methodology.

---

## 6. Decision Support System (DSS)

**Q20. What does "repeated High Priority" mean?**
A: A unit-level historical pattern label: a State–District unit is flagged when at least two of its historical district-year records share the same priority level. It does not require consecutive years and is **not** the unit's latest or current priority. Counts: repeated High 441, repeated Medium 220, repeated Low 46, insufficient history 0 (out of 707 units).

**Q21. How does repeated High (441) compare with latest High (91)?**
A: They are different measures. 441 units ever showed repeated High priority across 2008–2019, whereas only 91 units were High Risk at their latest historical assessment year (2008–2019). 351 of the 441 repeated-High units are not latest High, so planners must not treat "repeated" as current status.

**Q22. Is planning focus a verified needs assessment?**
A: No. Planning focus is model-attributed (mapped from absolute SHAP top contributors via transparent rules) and is public-health planning guidance, not a verified district needs assessment or medical recommendation.

**Q23. Are there clinical thresholds on the indicator charts?**
A: No. Indicator values are shown as observed percentages with "no clinical threshold applied." The UI does not apply the hardcoded 15/25/50/30-style thresholds flagged in prior audits.

---

## 7. Recent HMIS (Dataset 3)

**Q24. What does Dataset 3 add, and was it used to retrain the model?**
A: District-level Recent HMIS indicator evidence for 2020–2025 (3,306 records, 812 units, 36 states). It was **not** used to retrain or re-classify the historical model and carries no risk class; it is contextual evidence only.

**Q25. Is Dataset 3 a complete 2020–2025 panel?**
A: No. 2020–21 through 2023–24 cover 36 states each; 2024–25 is partial (17 states, 168 records); 2025–26 is excluded (anonymous downloads returned HTTP 500).

**Q26. How is missingness and invalid data handled in Dataset 3?**
A: No imputation. ANC First Trimester 3,148 valid / 158 missing; TT2 / Booster 3,148 / 158; Severe Anemia 3,138 / 168; Obstetric Complications 2,219 / 1,087 (structural NaNs from 2023–24 onward after the aggregate item disappeared). Invalid (>100 or otherwise out-of-range) values are retained and flagged, never clipped: TT2 368 flags (max 185.93), Severe Anemia 5 flags (max 354.55), Obstetric 11 flags (max 762.43). Total flagged cells: 1,955.

**Q27. Are indicators comparable across the recent period?**
A: Partially. Severe Anemia Hb threshold changed from <7 g/dl to ≤7 g/dl from 2023–24; Institutional Delivery and PNC within 48h are not comparable and were excluded; Obstetric Complications is available only through 2022–23. TT2 / Booster values can legitimately exceed 100 due to overlapping TT2/booster components.

---

## 8. Unified dataset and identity

**Q28. How many observations are in the unified dataset and how is identity normalized?**
A: 11,711 observations (8,405 historical + 3,306 recent). State/district spellings are normalized (case, punctuation, "&/and"-insensitive) at the API boundary: 39 raw state strings collapse to 36 normalized states, and 850 raw State–District entries collapse to 812 normalized units (38 duplicate normalized entries reconciled). Raw aliases are preserved for provenance.

**Q29. Do recent HMIS records carry a risk class?**
A: No. Historical records retain their original derived risk class; recent records have null risk/priority/DSS fields and are not assigned any risk class.

---

## 9. Disha assistant

**Q30. How does Disha answer questions?**
A: Retrieval-grounded. It maps a question to a topic, retrieves evidence from MRCDSS services, and answers deterministically. A local Ollama model is optional and only rephrases; if unavailable, every MRCDSS question is still answered from the evidence. Disha writes no data and trains no model.

**Q31. Does Disha claim the model is validated?**
A: No. "Validated" overclaims were removed. Disha describes risk classes as derived analytical groups, states SHAP is attribution not causation, and says there is no external clinical validation.

**Q32. What happens if you ask Disha something outside MRCDSS (e.g. "Is the moon made of cheese?")?**
A: It returns `grounded: false` with "That information is not available in the current MRCDSS evidence." It does not invent an answer.

**Q33. Does recent HMIS change a district's risk classification in Disha?**
A: No. Disha explicitly states recent HMIS was never used to assign or change a historical risk class.

---

## 10. Methodological limitations and integrity

**Q34. What are the main limitations a judge should weigh?**
A: (1) Derived, not clinical, risk labels. (2) Feature-target circularity: labels and classifiers share the same six features. (3) Train/test unit overlap: 100% of test records belong to units also in training. (4) No grouped/temporal validation; no external validation. (5) Weak cluster separation (silhouette ≈ 0.238); K fixed. (6) Label sensitivity: dropping Severe Anemia changes 54.35% of classes; Severe Anemia has cross-dataset harmonization uncertainty (D1 median 3.6% vs D2 median 51.5%). (7) SHAP is attribution, not causation; signed per-district direction is not stored. (8) Recent HMIS is partial (2024–25: 17 states; 2025–26 excluded) and contextual only.

**Q35. Is the project honest about these limitations?**
A: Yes. Limitations are disclosed in About → Limitations, Risk Analysis → Methodological Caveats, Methodology caveats, the Disha SYSTEM_PROMPT, the methodology service "Important Notes," and the audit/completion reports. Nothing is presented as externally validated.

**Q36. Can MRCDSS be used to allocate real health resources today?**
A: No. It is a research prototype. The disclosed circularity, overlap, weak separation, and absence of external validation mean it must not be used for operational decisions or as evidence of predictive performance.
