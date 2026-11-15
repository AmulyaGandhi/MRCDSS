# Decision Support System Pipeline Audit Report — MRCDSS

**Date:** 2026-11-12  
**Scope:** Decision-support output generation, 707-unit priority summary, planning-focus rules, DSS outputs, backend API serving, frontend presentation, and recent-HMIS separation.  
**Mode:** Inspect only. No existing file, dataset, risk label, model, metric, DSS output, backend file, or frontend file was modified. This report is the only artifact created.  
**Tests run:** No test that regenerates or overwrites existing outputs was executed. Verification used read-only file inspection, in-memory recomputation, direct service-function calls, and read-only merges of existing CSVs.

---

## 1. Executive Summary

The DSS pipeline is **numerically internally consistent**:

- All **8,405** historical district-year records are present, with no missing DSS fields and no duplicate `State + District + Year + source_dataset` keys.
- The **707 State–District units** are enumerated exactly once in the priority summary.
- Risk class to priority mapping is exact: **0 mismatches** across 8,405 records.
- All six planning rules are present and all planning-focus strings match `FEATURE_PLANNING_MAP`.
- Saved DSS outputs, the saved DSS report, and the main backend service counts agree.
- Recent HMIS records remain separate: **3,306** recent rows, **0** assigned risk classes, and **0** DSS priority levels.
- The saved DSS report and `About`/`Methodology` pages correctly state that risk classes are derived and that the system is for public-health planning, not clinical diagnosis.

However, the DSS **interpretation and presentation are not consistently supported by the underlying evidence**. Five High-severity issues remain:

1. **“Persistent” priority overstates consistency.** A unit needs only **two** High-risk years to be labeled Persistent High Priority. Result: **441/707** units are Persistent High, while only **91/707** are High Risk in their latest year. Among the 441 Persistent High units, **247** have a High-risk proportion below 50%, **351** are not High Risk in their latest year, and **86** have exactly two High-risk years.
2. **Planning focus is model attribution, not a district needs assessment.** The DSS selects the top three features by **absolute SHAP value** and maps them to generic “strengthen/improve” actions. It does not use SHAP direction, indicator thresholds, indicator gaps, or recent HMIS values. As a result, **26.91%** of top-1 planning focuses are on the extreme opposite side of the global median, and **15.15%** of records have all three top focus features on the favorable side of the median.
3. **The frontend invents direction and thresholds.** `DistrictDetails.tsx` hardcodes all top contributing factors as `direction: 'positive'` and displays “Increases risk,” although the DSS CSV contains no signed SHAP value. It also applies hardcoded indicator interpretations such as “Within acceptable range,” “Above target,” and “Elevated - intervention needed” that are not part of the saved DSS outputs.
4. **Historical records are presented as current priorities.** The Overview page requests the first eight `High Priority` records from the record-level endpoint and labels them “Districts currently flagged.” Because the CSV is ordered from older years first, those rows are **2016** records. Three of the first eight are no longer High Risk in 2019. Planning-filter counts also label record-level results as “districts.”
5. **Planning focus is strongly era/source-confounded.** Severe Anemia is the top-1 focus for **74.7% of D2 rows** but only **4.4% of D1 rows**. The Medium Risk class, which is almost entirely D2, has Severe Anemia as top-1 in **1,342/1,345** records. The resulting planning focus can reflect data era rather than current district need.

The DSS should therefore be described as a **model-attribution and rule-based historical planning aid**, not as a validated current district-needs ranking. Its counts and mappings are correct; its **persistence semantics, focus logic, and UI claims are not**.

---

## 2. Inspection Scope and Evidence

### 2.1 Files inspected

**DSS generation and outputs**

- `src/decision_support/planning_rules.py`
- `src/decision_support/decision_engine.py`
- `outputs/decision_support/district_decision_support.csv`
- `outputs/decision_support/district_priority_summary.csv`
- `outputs/decision_support/planning_rules.csv`
- `outputs/decision_support/decision_support_report.md`

**Source model and explanation inputs**

- `outputs/risk_classification/district_year_risk_clusters.csv`
- `outputs/explainability/shap_values_test.csv`
- `outputs/explainability/feature_importance.csv`
- `outputs/explainability/explainability_report.md`
- `src/explainability/shap_analysis.py`
- `models/logistic_regression.pkl`
- `models/logistic_regression_scaler.pkl`

**Backend serving**

- `backend/config.py`
- `backend/schemas/__init__.py`
- `backend/services/planning_service.py`
- `backend/services/districts_service.py`
- `backend/services/overview_service.py`
- `backend/services/unified_service.py`
- `backend/services/recent_hmis_service.py`
- `backend/services/assistant_service.py`
- `backend/services/methodology_service.py`
- `backend/api/routes/planning_priorities.py`
- `backend/api/routes/districts.py`

**Frontend presentation**

- `frontend/src/pages/Planning.tsx`
- `frontend/src/pages/Overview.tsx`
- `frontend/src/pages/DistrictExplorer.tsx`
- `frontend/src/pages/DistrictDetails.tsx`
- `frontend/src/pages/Methodology.tsx`
- `frontend/src/pages/About.tsx`
- `frontend/src/pages/RecentHmis.tsx`
- `frontend/src/components/DistrictInfoPanel.tsx`
- `frontend/src/components/DistrictRiskMap.tsx`
- `frontend/src/components/ContributingFactors.tsx`
- `frontend/src/components/HealthIndicators.tsx`
- `frontend/src/api/planning.ts`
- `frontend/src/api/districts.ts`
- `frontend/src/api/unified.ts`

**Data and tests**

- `data/unified/unified_mr_cdss_data.csv`
- `data/recent_hmis/dataset3/dataset3_recent_hmis.csv`
- `tests/test_decision_support.py`
- `tests/assistant/test_assistant_api.py`
- `tests/unified/test_unified_dataset.py`

### 2.2 Verification approach

- Read the DSS generation code and traced the exact computation of risk-to-priority mapping, top contributing features, priority summary, and persistent labels.
- Recomputed all DSS counts and persistence categories in memory from the saved CSVs.
- Merged the DSS CSV with the risk-cluster CSV in memory to audit planning focus against actual indicator values. No file was written.
- Called the backend service functions directly rather than starting a server. This verified the API-returned values without changing outputs.
- Compared the saved DSS report with the saved CSVs and with the backend service responses.
- Checked historical/recent HMIS separation and state/district key normalization.
- Did not run `pytest`, because several tests can rewrite generated outputs. No output-regenerating script was run.

---

## 3. DSS Data Flow and Contract

### 3.1 Actual pipeline

```text
8,405 historical district-year records
  -> six maternal-health indicators
  -> K-Means-derived risk_class
  -> Logistic Regression classifier
  -> absolute SHAP values for the predicted class
  -> top 3 features by absolute SHAP
  -> generic planning-focus rule for each feature
  -> risk_class -> priority_level
  -> 8,405-row decision-support CSV
  -> 707-row State-District priority summary
```

The DSS uses:

- **Input:** `outputs/risk_classification/district_year_risk_clusters.csv`
- **Model:** `models/logistic_regression.pkl`
- **Scaler:** `models/logistic_regression_scaler.pkl`
- **Output:** `outputs/decision_support/district_decision_support.csv`
- **Summary:** `outputs/decision_support/district_priority_summary.csv`
- **Rules:** `outputs/decision_support/planning_rules.csv`
- **Report:** `outputs/decision_support/decision_support_report.md`

### 3.2 Priority mapping

`RISK_TO_PRIORITY` in `src/decision_support/planning_rules.py` is:

```text
High Risk   -> High Priority
Medium Risk -> Medium Priority
Low Risk    -> Low Priority
```

**Verified:** every one of the 8,405 records follows this mapping. Mismatch count: **0**.

This is a direct relabeling, not an independent severity or needs score. A High Priority label therefore inherits all limitations of the K-Means-derived High Risk class.

### 3.3 Planning rules

`FEATURE_PLANNING_MAP` contains exactly one generic focus per feature:

| Feature | Planning focus |
|---|---|
| `ANC_First_Trimester_Pct` | Strengthen early ANC registration and outreach |
| `TT2_Booster_Pct` | Strengthen antenatal TT/booster coverage |
| `Severe_Anemia_Pct` | Prioritize anemia screening, prevention and program coverage |
| `Institutional_Delivery_Pct` | Improve institutional-delivery access and service capacity |
| `PNC_48h_Pct` | Strengthen postnatal follow-up within 48 hours |
| `Obstetric_Complications_Pct` | Strengthen referral and emergency obstetric service planning |

**Verified:** all six rules are present in `planning_rules.csv`; all `planning_focus_*` values in the DSS CSV map exactly to these rules. Mismatch count across all three focus positions: **0**. There are no missing or empty focus strings.

The rules are generic and invariant. The same action is emitted regardless of whether the district is at 10% or 99% coverage. This is the central reason the focus output is not a needs assessment.

### 3.4 SHAP contract and model assumptions

`decision_engine.py`:

- Loads the saved Logistic Regression pipeline and extracts `named_steps["classifier"]`.
- Applies the external saved scaler to the six features.
- Computes SHAP with a 100-row background from the scaled data.
- Selects top three features by **absolute** SHAP value.
- Uses a hardcoded class-index map:

```text
High Risk -> 0
Low Risk  -> 1
Medium Risk -> 2
```

The current model classes are exactly `['High Risk', 'Low Risk', 'Medium Risk']`, so the hardcoded index map matches the current artifact. The model is also hardcoded to Logistic Regression, which matches the current saved best model. These are implementation fragilities, not current numeric errors.

The saved Logistic Regression pipeline contains a near-identity internal scaler because training applied a separate scaler before fitting the pipeline. The DSS uses the **external** scaler with the extracted classifier, which matches the training path. The current DSS SHAP path is therefore coherent, but it depends on the double-scaling artifact documented in the ML audit. `SHAP_PATH` is defined in `planning_rules.py` but is not used by the DSS engine; the engine recomputes SHAP for all records.

### 3.5 Saved DSS report consistency

The saved report correctly states:

- 8,405 records and 8,405 unique district-years.
- 2,614 High Priority, 1,345 Medium Priority, 4,446 Low Priority.
- 707 total districts.
- 441 Persistent High, 220 Persistent Medium, 46 Persistent Low, 0 Insufficient History.
- The system is a public-health planning DSS, not clinical diagnosis/treatment.
- Risk labels are K-Means-derived.
- SHAP is not causal.

**Verified:** the report’s numeric counts and top-feature counts match the saved CSVs. The report also correctly notes “Persistence ≠ severity.” The report does **not** disclose that Persistent High requires only two High years, that most Persistent High units are not currently High, or that planning focus ignores indicator direction.

---

## 4. Record-Level Reconciliation

### 4.1 Record counts and keys

| Check | Result |
|---|---:|
| DSS rows | 8,405 |
| Unique `State + District` units | 707 |
| States/UTs | 36 |
| Years | 2008–2019 |
| D1 rows | 6,293 |
| D2 rows | 2,112 |
| Duplicate `State + District + Year + source_dataset` | 0 |
| Duplicate `State + District + Year` ignoring source | 0 |
| Missing DSS fields | 0 |
| Missing top features | 0 |
| Missing planning focus strings | 0 |

**Verdict:** PASS. The record-level DSS output is complete and internally consistent.

### 4.2 Risk and priority distributions

| Priority / risk class | Records | Share of 8,405 |
|---|---:|---:|
| High Priority / High Risk | 2,614 | 31.10% |
| Medium Priority / Medium Risk | 1,345 | 16.00% |
| Low Priority / Low Risk | 4,446 | 52.90% |

These are **district-year record counts**, not 707-unit counts. The distinction is important because the frontend often labels them as districts.

### 4.3 Three different priority distributions

| Basis | High | Medium | Low | Total |
|---|---:|---:|---:|---:|
| Record-level DSS rows | 2,614 (31.1%) | 1,345 (16.0%) | 4,446 (52.9%) | 8,405 |
| Latest year per State–District unit | 91 (12.9%) | 493 (69.7%) | 123 (17.4%) | 707 |
| “Persistent” summary | 441 (62.4%) | 220 (31.1%) | 46 (6.5%) | 707 |

This table is the core reconciliation the UI currently omits. The three distributions answer different questions:

- **Record-level:** how many historical district-years received each priority.
- **Latest unit-level:** what each district-state unit’s most recent historical observation was.
- **Persistent summary:** how many units have met the current “at least two years in a class” rule.

The UI juxtaposes the 2,614 record count, the 441 persistent count, and the 707-unit total without explaining their different bases.

---

## 5. The 707-Unit Priority Summary

### 5.1 Summary counts

| Persistent category | Units | Share of 707 |
|---|---:|---:|
| Persistent High Priority | 441 | 62.38% |
| Persistent Medium Priority | 220 | 31.12% |
| Persistent Low Priority | 46 | 6.51% |
| Insufficient History | 0 | 0% |
| Total | 707 | 100% |

Latest observed risk class across the same 707 units:

| Latest risk class | Units | Share of 707 |
|---|---:|---:|
| High Risk | 91 | 12.87% |
| Medium Risk | 493 | 69.73% |
| Low Risk | 123 | 17.40% |

### 5.2 Exact persistence logic

In `src/decision_support/decision_engine.py:106-147`:

```text
group by State, District
years_observed = number of records in the group
high_years = count of High Risk
medium_years = count of Medium Risk
low_years = count of Low Risk

if years_observed >= 2 and high_years >= 2:
    Persistent High Priority
elif years_observed >= 2 and medium_years >= 2:
    Persistent Medium Priority
elif years_observed >= 2 and low_years >= 2:
    Persistent Low Priority
else:
    Insufficient History
```

The rule uses **any two years**, not a majority, not a consecutive run, not the latest status, and not a minimum proportion. It also does not require a minimum number of observed years beyond two.

### 5.3 Cross-tabulation with latest status

| Persistent category | Latest High | Latest Medium | Latest Low | Total |
|---|---:|---:|---:|---:|
| Persistent High | 90 | 271 | 80 | 441 |
| Persistent Medium | 0 | 209 | 11 | 220 |
| Persistent Low | 1 | 13 | 32 | 46 |

**Confirmed:** **351/441** Persistent High units are **not** High Risk in their latest observed year. **80** are latest Low Risk. Similarly, **11/220** Persistent Medium units are latest Low Risk, and **14/46** Persistent Low units are not latest Low Risk.

These outcomes are not defects in the arithmetic. They are the expected result of a rule that ignores latest status and majority share.

### 5.4 Proportion of years in the assigned category

| Persistent category | Units | Units with assigned-category proportion < 50% |
|---|---:|---:|
| Persistent High | 441 | 247 |
| Persistent Medium | 220 | 218 |
| Persistent Low | 46 | 0 |

Additional detail:

- **86/441** Persistent High units have exactly **2** High-risk years.
- **68** have 3 High-risk years; the remainder have 4–12.
- **59/220** Persistent Medium units have exactly 2 Medium-risk years.
- All 46 Persistent Low units have a Low-risk majority, but 14 are not latest Low Risk.

The label “persistent” is therefore not synonymous with “consistently high” or “currently high.” In many cases it means “at least two high years at some point in 2008–2019.”

### 5.5 Observed-history coverage

`years_observed` distribution across 707 units:

| Observed years | Units |
|---:|---:|
| 3 | 1 |
| 5 | 6 |
| 6 | 4 |
| 8 | 1 |
| 12 | 695 |

Twelve units have fewer than 12 years:

- Andhra Pradesh: Alluri Sitharama Raju (6), Eluru (6), Narayanpet (6)
- Arunachal Pradesh: Kra Daadi (5), Longding (8), Namsai (5), Siang (5)
- Haryana: Charki Dadri (3)
- West Bengal: Alipurduar (6), Jhargram (5), Kalimpong (5), Paschim Bardhaman (5)

**Charki Dadri** has only 3 observed years (`2 High / 1 Medium`) and is labeled **Persistent High Priority**. This shows that “Insufficient History = 0” does not mean every unit has adequate history; it means no unit failed the code’s very low two-year test. The frontend does not disclose short histories or show observed-year counts.

### 5.6 Examples from the saved DSS report

The saved report itself lists examples that illustrate the issue:

- **North And Middle Andaman:** `2 High / 1 Medium / 9 Low`, latest Medium → **Persistent High Priority**.
- **Chittoor (Andhra Pradesh):** `2 High / 1 Medium / 9 Low`, latest Low → **Persistent High Priority**.
- **South Andamans:** `1 High / 2 Medium / 9 Low`, latest Medium → **Persistent Medium Priority**.
- **Sri Potti Sriramulu Nellore:** `0 High / 3 Medium / 9 Low`, latest Low → **Persistent Medium Priority**.

### 5.7 Common contributing features

`common_contributing_features` is built by concatenating all top-1, top-2, and top-3 feature columns for a unit, counting appearances, and taking the top three. This:

- Counts appearances across all three positions without weighting position.
- Does not distinguish “top-1 driver” from “third-ranked feature.”
- Is not used consistently in the frontend, but is present in the saved summary.

This is a low-to-medium interpretability issue rather than a count error.

### 5.8 Verdict on “707 units handled correctly”

- **Enumeration:** PASS. Exactly 707 units, one summary row each, no duplicate keys, no missing units.
- **Arithmetic:** PASS. Year counts and proportions add up.
- **Persistence semantics:** FAIL. The label overstates consistency and currency.
- **Coverage disclosure:** FAIL. Short histories and “insufficient” thresholds are not surfaced.
- **Backend exposure:** PARTIAL. `planning_service.py` exposes only high/medium/low persistent counts; if `Insufficient History` were nonzero, it would be omitted from `persistent_priority_info`.

---

## 6. Planning Focus and SHAP Attribution

### 6.1 How focus is selected

For each record, the DSS:

1. Computes SHAP values for the predicted class.
2. Takes the **absolute value** of each feature’s SHAP.
3. Sorts descending.
4. Keeps the top three features.
5. Maps each feature to a fixed planning-focus sentence.

There is no use of:

- SHAP sign.
- Feature value versus a target.
- Feature value versus a benchmark or median.
- Direction of the indicator.
- Recent HMIS evidence.
- District-specific program context.

The absolute-value choice is appropriate for “model influence,” but not for “indicator deficit.” A large positive and a large negative SHAP both become the same action.

### 6.2 Top-1 feature distribution

| Top-1 feature | Records | Share of 8,405 |
|---|---:|---:|
| Institutional Delivery | 2,446 | 29.10% |
| Severe Anemia | 1,853 | 22.05% |
| ANC First Trimester | 1,799 | 21.40% |
| TT2 Booster | 1,553 | 18.48% |
| PNC 48h | 750 | 8.92% |
| Obstetric Complications | 4 | 0.05% |

### 6.3 Top-1 focus is largely determined by risk class

| Risk class | Records | Institutional | Severe Anemia | ANC | TT2 | PNC | Obstetric |
|---|---:|---:|---:|---:|---:|---:|---:|
| High Risk | 2,614 | 730 | 22 | 1,210 | 519 | 133 | 0 |
| Medium Risk | 1,345 | 2 | 1,342 | 1 | 0 | 0 | 0 |
| Low Risk | 4,446 | 1,714 | 489 | 588 | 1,034 | 617 | 4 |

This is a strong signal that the focus output is mostly a restatement of the risk class:

- **1,342/1,345 Medium Risk records** have Severe Anemia as top-1.
- **1,714/4,446 Low Risk records** have Institutional Delivery as top-1.
- **1,210/2,614 High Risk records** have ANC as top-1.

The DSS is therefore not producing a district-specific focus pattern; it is producing a class-level pattern with some variation.

### 6.4 Alignment with underlying indicator values

Global medians used only as an audit reference:

| Feature | Global median | 25th percentile | 75th percentile |
|---|---:|---:|---:|
| ANC First Trimester | 61.6 | 46.2 | 77.6 |
| TT2 Booster | 86.7 | 79.3 | 92.6 |
| Severe Anemia | 5.2 | 2.3 | 23.1 |
| Institutional Delivery | 63.6 | 48.1 | 77.5 |
| PNC 48h | 68.8 | 54.8 | 81.2 |
| Obstetric Complications | 5.1 | 1.8 | 11.3 |

For protective features, “adverse” below is defined as below the global median. For risk features, “adverse” is above the global median. “Extreme opposite” means protective at or above the 75th percentile, or risk at or below the 25th percentile.

| Measure | Records | Share of 8,405 |
|---|---:|---:|
| Top-1 feature on the adverse side of the global median | 5,763 | 68.57% |
| Top-1 feature on the extreme opposite side | 2,262 | 26.91% |
| All three top features on the favorable side | 1,273 | 15.15% |
| All three top features on the adverse side | 2,172 | 25.84% |

The first measure shows that many focus areas are directionally plausible. The second and third show that a substantial minority are not: the system recommends strengthening or improving an indicator that is already favorable, often extremely favorable.

### 6.5 Feature-specific evidence

**Institutional Delivery** is the top-1 focus for 2,446 records:

- 1,047 (42.8%) have Institutional Delivery ≥ 80%.
- 351 (14.3%) have ≥ 90%.
- All 351 of the ≥ 90% records are Low Risk.
- 118 (4.8%) have ≥ 95%.

**TT2 Booster** top-1: 647/1,553 (41.7%) are ≥ 90%; 358 (23.1%) are ≥ 95%.

**PNC 48h** top-1: 323/750 (43.1%) are ≥ 80%; 224 (29.9%) are ≥ 90%.

**Severe Anemia** top-1: 1,102/1,853 (59.5%) are ≥ 50%; only 42 are < 15%.

**ANC** top-1: 205/1,799 (11.4%) are ≥ 80%; 1,459 (81.1%) are < 50%.

**Obstetric Complications** is top-1 only 4 times, all Low Risk, all D1, with values 52.7–70.6. It is too rare to support an obstetric-complications focus estimate.

### 6.6 Concrete examples

**Chittoor, Andhra Pradesh, 2016 — Low Risk / Low Priority**

- ANC 81.8%, TT2 86.6%, Severe Anemia 7.8%, Institutional Delivery 90.4%, PNC 99.0%, Obstetric 10.9%.
- Top features: Institutional Delivery, PNC, ANC.
- Planning focus 1: **“Improve institutional-delivery access and service capacity.”**
- The district is already at 90.4% institutional delivery and 99.0% PNC.

**Chittoor, Andhra Pradesh, 2019 — Low Risk / Low Priority**

- ANC 87.7%, TT2 99.7%, Severe Anemia 26.6%, Institutional Delivery 93.4%, PNC 96.4%, Obstetric 8.6%.
- Top features: Institutional Delivery, Severe Anemia, TT2.
- Planning focus 1 is still **“Improve institutional-delivery access and service capacity.”**

**Anjaw, Arunachal Pradesh, 2019 — High Risk / High Priority**

- ANC 24.2%, TT2 61.6%, Severe Anemia 51.5%, Institutional Delivery 25.4%, PNC 58.3%, Obstetric 0%.
- Top features: ANC, Institutional Delivery, TT2.
- Planning focus 1: **“Strengthen early ANC registration and outreach.”**

The Anjaw example is directionally sensible because the underlying values are adverse. The Chittoor examples show why model influence alone is insufficient for planning: the top feature can be a high-coverage protective indicator.

### 6.7 Era/source confounding in planning focus

Top-1 focus by source:

| Feature | D1 count | D1 share | D2 count | D2 share |
|---|---:|---:|---:|---:|
| ANC | 1,636 | 26.0% | 163 | 7.7% |
| Institutional Delivery | 2,230 | 35.4% | 216 | 10.2% |
| PNC | 722 | 11.5% | 28 | 1.3% |
| Severe Anemia | 275 | 4.4% | 1,578 | 74.7% |
| TT2 | 1,426 | 22.7% | 127 | 6.0% |
| Obstetric | 4 | 0.06% | 0 | 0% |

Severe Anemia dominates D2 planning focus. The Medium Risk class is almost entirely D2 and almost entirely Severe-Anemia-focused. This carries the prior High-severity era/source confounding finding directly into the DSS focus recommendations. The DSS report does not disclose that the focus distribution differs by source era.

### 6.8 Verdict on planning focus

- **Mechanical rule mapping:** PASS.
- **Use of model attribution:** PASS for “model influence.”
- **Use of signed direction:** FAIL. Signed SHAP is discarded.
- **Use of indicator gaps/targets:** FAIL. No thresholds or targets are used.
- **Use of recent HMIS context:** FAIL by design; recent values are not used to generate focus.
- **Consistency with underlying values:** PARTIAL. 68.57% of top-1 focuses are adverse-side, but 26.91% are extreme-opposite and 15.15% have all top features favorable.
- **As a district-specific needs assessment:** FAIL. The focus is largely determined by risk class and model attribution.

---

## 7. Backend API and Frontend Presentation

### 7.1 API-level verification

| Surface | Observed behavior | Verdict |
|---|---|---|
| `GET /api/planning-priorities` | Returns record-level priority distribution 2,614/1,345/4,446; persistent 441/220/46; feature counts as top-3 appearances | Numeric PASS; labels misleading |
| `GET /api/districts` | Returns 8,405 record-level rows; `High` filter returns 2,614 records; first records are 2016 | Numeric PASS; historical/current ambiguity |
| `GET /api/districts/latest` | 707 latest records; 91 High / 493 Medium / 123 Low | PASS |
| `GET /api/overview` | 8,405 total records, 707 units, 36 states, 2008–2019; record-level priority distribution | Numeric PASS |
| `GET /api/districts/{state}/{district}` | Full historical series plus six indicators and DSS focus fields | PASS |
| `GET /api/unified/overview` | 11,711 rows, 812 normalized units, but `n_states = 39` | FAIL on state count |
| `GET /api/unified/districts` | 850 raw-key entries; only 812 unique normalized units; 38 duplicate normalized keys | FAIL on unit enumeration |
| `GET /api/recent-hmis/overview` | 3,306 rows, 812 units, 36 states | PASS |
| Assistant grounded answers | Uses unified state count, record-level high-name list, and “validated historical” wording | PARTIAL |

### 7.2 Planning page

`frontend/src/pages/Planning.tsx` has several unsupported or mislabeled claims:

- The priority cards show **2,614 / 1,345 / 4,446**, which are district-year record counts, but the page context does not label them as record-level.
- The page says `“Current planning priorities are derived from the validated MRCDSS decision support system”`. The risk classes are derived, not externally validated.
- It says `“Persistent priority reflects consistent priority status across assessment periods.”` This is not what the rule measures.
- The persistent section says `“Districts maintaining priority status across multiple assessment periods.”` The any-two-year rule does not establish maintenance.
- The feature table heading says `“Number of districts where each indicator contributes to the planning focus.”` The values are top-3 **record appearances**, not districts.
- The column is literally `“Districts Affected”`, but the values exceed 707.
- The result count is shown as `“2,614 districts”` after a High filter, although the rows are district-year records.

Feature table values:

| Feature | Top-3 appearances | Distinct State–District units with ≥1 appearance |
|---|---:|---:|
| ANC | 6,195 | 707 |
| Institutional Delivery | 6,142 | 706 |
| TT2 | 5,408 | 706 |
| PNC | 3,829 | 683 |
| Severe Anemia | 3,355 | 697 |
| Obstetric | 286 | 191 |

The distinct-unit counts are the only values that can legitimately be called “districts affected.” The current 6,195 etc. are record appearances and are impossible as district counts. Because each feature appears somewhere for nearly every unit, the “districts affected” table has little discriminating value even when relabeled correctly.

### 7.3 Overview page

`frontend/src/pages/Overview.tsx`:

- Calls `getDistricts({ priority: 'High', page: 1, per_page: 8 })`.
- Labels the table `“Districts currently flagged at the highest planning priority.”`
- The returned rows are the first eight High Priority records in CSV order, all **2016**.
- The table column is `“Latest Year”`, which makes the rows appear current.
- Of the first eight, three are not High Risk in their latest year: Changlang and East Siang are latest Medium, Lohit is latest Low.
- The map itself correctly uses `/api/districts/latest` and therefore shows latest historical risk. The table and map use different bases.
- The page says the map shows the `“validated MRCDSS district risk classification.”` This conflicts with the derived-label constraint.

The result is a direct inconsistency: the map is latest-based, while the “attention needed” table is record-based and starts in 2016.

### 7.4 District details page

`frontend/src/pages/DistrictDetails.tsx` correctly selects the latest historical record for the detail header and displays the full historical timeline. It also renders recent HMIS evidence separately. That separation is good.

The page does not correctly represent DSS evidence:

- `contributingFactors` hardcodes every feature as:

```text
direction: 'positive'
```

- The UI then renders `“Increases risk”` for all three.
- The DSS CSV does not contain signed SHAP values, so the frontend cannot know direction from the served data.
- The explainability report itself has the same direction bug: for a Low Risk example with high protective values, it labels all three as “increases risk” because it treats a positive class-specific SHAP as risk-increasing.
- `getInterpretationForIndicator` applies hardcoded thresholds:
  - Severe Anemia / Obstetric: `≤15` acceptable, `≤25` moderate, `>25` elevated/intervention needed.
  - Protective: `≥50` above target, `≥30` moderate, `<30` below target.
- These thresholds are not in the saved DSS outputs, not sourced from a guideline in the repository, and are not documented on the page.
- The page uses phrases such as `“Within acceptable range,” “Above target,”` and `“Elevated - intervention needed”` without a stated evidentiary basis.
- High Risk displays `“Requires Attention”`; this is acceptable if clearly historical, but the page does not prominently state that the assessment is from 2008–2019 and not a current clinical assessment.

`DistrictInfoPanel.tsx` also labels the latest historical record `“Current MRCDSS Assessment”` while displaying a latest year of 2019. The adjacent year helps, but “current” is not accurate for a historical model.

### 7.5 Recent HMIS and unified API consistency

Data separation is preserved, but the unified API has key-normalization defects:

- `get_unified_overview()` computes `n_states` from raw `State` values.
- The unified file contains three state-name variants across eras:
  - `Andaman And Nicobar Islands` vs `Andaman & Nicobar Islands`
  - `Jammu And Kashmir` vs `Jammu and Kashmir`
  - `The Dadra And Nagar Haveli And Daman And Diu` vs `The Dadra and Nagar Haveli and Daman and Diu`
- Result: unified `n_states = 39`, while historical and recent each have 36. The recent overview correctly returns 36.
- `get_unified_districts()` groups by raw `State, District` instead of normalized keys.
- Result: **850** API entries for **812** normalized units, with **38** duplicate normalized keys. Examples include Andaman districts split into historical-only and recent-only entries, and multiple Chhattisgarh district punctuation variants.
- The frontend `Overview.tsx` joins historical map records to recent records by exact `state` and `district` strings. The three state variants can therefore suppress the recent-evidence panel for those states even when recent data exist. The unified district-detail endpoint normalizes keys and does not have this particular failure.

### 7.6 Assistant and methodology wording

- `backend/services/assistant_service.py:570` and `:834-836` use `“validated historical MRCDSS risk classification”` language.
- `frontend/src/pages/Planning.tsx:147` uses `“validated MRCDSS decision support system.”`
- `frontend/src/pages/Overview.tsx:237` uses `“validated MRCDSS district risk classification.”`
- `backend/services/methodology_service.py:27` says `“six validated maternal-health indicators.”`
- The assistant’s aggregate path reports the unified state count from `/api/unified/overview`, so it can report 39 states even though there are 36.
- The assistant’s “High-priority districts include …” path uses `get_districts(priority="High")`, which is record-level and begins in 2016, not latest or persistent.
- `backend/services/methodology_service.py:52` says Logistic Regression was selected based on accuracy, F1, and ROC-AUC; the ML audit found the code selects by highest macro F1. This is inherited from the ML audit and is not caused by the DSS.

The About page and the saved DSS report are better: they explicitly describe derived labels, non-causality, and planning-not-clinical use. The concern is inconsistent wording across the application.

---

## 8. Recent HMIS Separation

### 8.1 Data separation

| Check | Result |
|---|---:|
| Historical MRCDSS rows | 8,405 |
| D1 rows | 6,293 |
| D2 rows | 2,112 |
| Recent HMIS rows | 3,306 |
| Unified total | 11,711 |
| Historical rows with risk class | 8,405 / 8,405 |
| Historical rows with priority | 8,405 / 8,405 |
| Recent rows with risk class | 0 / 3,306 |
| Recent rows with priority | 0 / 3,306 |
| Historical years | 2008–2019 |
| Recent years | 2020–2025 |
| Historical normalized units | 707 |
| Recent normalized units | 812 |
| Union normalized units | 812 |

**Verdict:** PASS. Recent HMIS data is kept separate and is not assigned risk or DSS priority.

### 8.2 Service separation

`recent_hmis_service.py` and `unified_service.py` read prepared CSVs and do not write files, retrain models, or recompute indicators at request time. The Recent HMIS page explicitly states that Dataset 3 was not used to retrain or externally validate the existing classifier.

**Verdict:** PASS for separation and read-only serving.

### 8.3 Separation caveats

- The recent HMIS extension has only 4 of the 6 DSS indicators; Institutional Delivery and PNC are not comparable.
- Severe Anemia changed definition from `<7 g/dl` to `≤7 g/dl` in 2023–24.
- 2024–25 is partial: 17 states, 168 records.
- The unified API state/district key defects described in §7.5 should be fixed before claiming exact unified counts.
- Recent HMIS values should not be used to revise historical DSS priority without a documented model/label update, which has not occurred.

---

## 9. Problems and Severity

### 9.1 High-severity findings

| ID | Problem | Evidence | Affected files |
|---|---|---|---|
| H-01 | “Persistent” priority is an any-two-year label, not consistency or current status | 441 Persistent High vs 91 latest High; 247/441 High proportion < 50%; 351/441 latest not High; 86 have exactly 2 High years; Charki Dadri 2H/1M in 3 years is Persistent High | `src/decision_support/decision_engine.py:106-147`, `outputs/decision_support/district_priority_summary.csv`, `outputs/decision_support/decision_support_report.md`, `frontend/src/pages/Planning.tsx:176` |
| H-02 | Planning focus uses absolute SHAP plus generic rules, not indicator gaps | 26.91% top-1 extreme-opposite; 15.15% all three top features favorable; Institutional top-1 with 90%+ coverage in 351 records; Chittoor 2016 focus “improve institutional delivery” at 90.4% | `src/decision_support/decision_engine.py:69-71`, `src/decision_support/planning_rules.py`, `outputs/decision_support/district_decision_support.csv` |
| H-03 | UI hardcodes all SHAP contributors as “increases risk” and applies unsupported indicator thresholds | `direction: 'positive'` for all three factors; hardcoded 15/25/30/50 thresholds; no signed SHAP in DSS CSV | `frontend/src/pages/DistrictDetails.tsx:19-28,60-62`; `frontend/src/components/ContributingFactors.tsx`; `src/explainability/shap_analysis.py:302` |
| H-04 | Historical record-level priorities are presented as current district priorities | Overview “currently flagged” table uses first eight 2016 High records; 3/8 are not latest High; Planning high filter shows 2,614 record-years as “districts” | `frontend/src/pages/Overview.tsx:122,283`; `frontend/src/pages/Planning.tsx:264`; `backend/services/districts_service.py:22-77` |
| H-05 | Planning focus is strongly era/source-confounded | Severe Anemia top-1 in 1,578/2,112 D2 rows (74.7%) vs 275/6,293 D1 rows (4.4%); 1,342/1,345 Medium Risk records are Severe-Anemia-top-1; Medium class is overwhelmingly D2 | `outputs/decision_support/district_decision_support.csv`, `outputs/risk_classification/district_year_risk_clusters.csv`, prior ML audit H-02 |

#### H-01 — Persistence detail

The report and frontend use language such as “maintaining priority status” and “consistent priority status.” The actual rule is:

```text
if High years >= 2: Persistent High
```

No majority, recency, consecutive-year, or minimum-coverage requirement is applied. The result is a summary distribution that looks far more severe than the latest observation: **62% Persistent High** versus **13% latest High**. This is likely to mislead planners if the persistent card is read as a current burden estimate.

#### H-02 — Planning-focus detail

The top-1 focus is largely class-determined:

- Medium Risk: 1,342/1,345 Severe Anemia.
- Low Risk: 1,714/4,446 Institutional Delivery.
- High Risk: 1,210/2,614 ANC.

The system does not compare values to targets. It cannot distinguish “improve low institutional delivery” from “maintain already-high institutional delivery.” This is not a district-specific needs assessment.

#### H-03 — Direction/threshold detail

The DSS stores only feature names, not signed SHAP values. Therefore no downstream component can legitimately infer “increases risk” from the DSS CSV alone. `DistrictDetails.tsx` nevertheless hardcodes all three as positive. The explainability report also uses positive class-specific SHAP as “increases risk,” which is not correct for the Low Risk class.

The hardcoded indicator thresholds are not in the DSS report, rules CSV, or any linked guideline. They create additional unsupported clinical/planning guidance.

#### H-04 — Historical/current detail

The Overview attention table and Planning district table are record-level historical lists. The map and latest endpoint are latest-based. This means the same page can show a latest-based map and a 2016-based attention list.

#### H-05 — Era/source detail

The source imbalance is not a DSS arithmetic bug; it is inherited from the feature/label pipeline. But the DSS amplifies it by turning the top feature into a planning recommendation. A D2-driven Medium Risk record is almost always told to prioritize anemia screening, while D1-driven records are much more likely to receive ANC, TT2, or institutional-delivery focus. The report does not disclose that focus prevalence differs sharply by era.

### 9.2 Medium-severity findings

| ID | Problem | Evidence | Affected files |
|---|---|---|---|
| M-01 | Record-level and district-level counts are conflated | Priority cards 2,614/1,345/4,446 are records; latest units are 91/493/123; persistent are 441/220/46; feature “Districts Affected” values up to 6,195 | `frontend/src/pages/Planning.tsx:156-216,264`; `backend/services/planning_service.py:12-60` |
| M-02 | Insufficient-history category is not exposed and coverage is not surfaced | `persistent_priority_info` has only high/medium/low; no insufficient count; 12 units have <12 years; short histories not shown | `backend/services/planning_service.py:17-33`; `frontend/src/pages/Planning.tsx:176-194` |
| M-03 | Unified API state count and district list are not normalized consistently | `n_states=39` vs 36; `get_unified_districts()` returns 850 entries for 812 normalized units, 38 duplicate keys | `backend/services/unified_service.py:107-110,124-153` |
| M-04 | “Validated” language overstates evidence | “validated historical MRCDSS risk classification,” “validated MRCDSS decision support system,” “six validated indicators” | `backend/services/assistant_service.py:570,834-836`; `frontend/src/pages/Planning.tsx:147`; `frontend/src/pages/Overview.tsx:237`; `backend/services/methodology_service.py:27` |
| M-05 | “Common contributing features” is unweighted top-3 appearance counting | Top-1, top-2, top-3 all counted equally; no position weighting or proportion | `src/decision_support/decision_engine.py:127-134` |
| M-06 | DSS relies on hardcoded LR class/model assumptions and a double-scaling artifact | Hardcoded class index map; hardcoded LR; external scaler required because pipeline internal scaler is near identity | `src/decision_support/decision_engine.py:24-63`; `models/logistic_regression.pkl`; `models/logistic_regression_scaler.pkl` |
| M-07 | Signed SHAP and indicator values are not persisted with DSS output | DSS CSV has feature names and focus text only; direction cannot be audited from saved DSS output | `outputs/decision_support/district_decision_support.csv`; `src/decision_support/decision_engine.py:69-95` |
| M-08 | Recent-evidence panel joins by exact raw state/district strings | 3 state-name variants and 38 district variants can suppress matches | `frontend/src/pages/Overview.tsx:165-168`; `backend/services/recent_hmis_service.py:213-215` |

### 9.3 Low-severity findings

| ID | Problem | Affected files |
|---|---|---|
| L-01 | Obstetric Complications is top-1 only 4 times, all Low Risk/D1; feature-specific focus is not estimable | `outputs/decision_support/district_decision_support.csv` |
| L-02 | `SHAP_PATH` is defined but unused; DSS recomputes SHAP without writing a provenance link to the saved test SHAP file | `src/decision_support/planning_rules.py:31`; `src/decision_support/decision_engine.py` |
| L-03 | “Districts” is used for 707 State–District units, which include States/UTs and district-state identifiers | `outputs/decision_support/decision_support_report.md`; `frontend/src/pages/Planning.tsx` |
| L-04 | `get_districts()` relies on CSV order rather than an explicit sort | `backend/services/districts_service.py:54-77` |
| L-05 | Existing DSS tests verify mapping and file presence but not persistence semantics, district-vs-record labels, direction, or API count consistency | `tests/test_decision_support.py` |
| L-06 | The saved DSS report calls 707 “districts” and does not state the exact persistence threshold | `outputs/decision_support/decision_support_report.md` |

---

## 10. Recommended Corrections (Not Implemented)

These are recommendations only. No fixes were made.

### 10.1 Persistence and summary

1. Replace the any-two-year rule with a documented rule using at least one of:
   - majority of observed years;
   - latest status plus repeated prior evidence;
   - consecutive-period requirement;
   - a minimum observed-year threshold.
2. Rename “Persistent” if the rule remains permissive. “Repeatedly observed High Priority” is more accurate than “Persistent High Priority.”
3. Show `years_observed`, class-year counts, proportion, latest year, and latest class next to every persistent label.
4. Surface `Insufficient History` in the API and UI. Do not silently omit it.
5. Do not present Persistent High as current burden. Show latest High and Persistent High side by side with their different definitions.
6. Add a minimum-coverage warning for the 12 units with fewer than 12 observed years.

### 10.2 Planning focus

1. Persist signed SHAP values and the actual indicator value for each top feature.
2. Separate two outputs:
   - **Model influence:** top absolute SHAP features.
   - **Actionable gap:** features that are both influential and on the adverse side of a documented benchmark or target.
3. Only emit “strengthen/improve” for adverse features. For already-favorable features, use “maintain/monitor” or omit them from the action list.
4. Add indicator-specific targets or benchmarks with cited sources. Do not use hardcoded frontend thresholds.
5. Relabel the current focus as “model-attributed planning focus” rather than “evidence-based district need.”
6. Report planning-focus prevalence by source era and by risk class.
7. Keep recent HMIS values as context only until a documented validation/retraining decision is made.

### 10.3 API and frontend

1. Return and label record-level counts and unit-level counts separately.
2. Change “Districts Affected” to “Record appearances” or compute distinct State–District units.
3. Use `/api/districts/latest` for “current” tables; use record-level endpoints only for historical exploration.
4. Label the Overview attention table as historical and show the assessment year prominently.
5. Remove hardcoded `direction: 'positive'` and hardcoded indicator interpretations, or source them from a documented backend field.
6. Change “validated MRCDSS” to “derived MRCDSS” unless external validation is actually documented.
7. Change “Persistent priority reflects consistent priority status” to describe the exact rule.
8. Show the 707-unit, 8,405-record, latest, and persistent bases in one reconciliation panel.

### 10.4 Unified/recent normalization

1. Normalize `State` before counting `n_states` in `get_unified_overview()`.
2. Group `get_unified_districts()` by normalized state/district keys.
3. Deduplicate normalized variants and preserve display names separately.
4. Use normalized joins in the Overview recent-evidence lookup.
5. Add API tests that assert 36 states and 812 normalized units across historical/recent/unified surfaces.

### 10.5 Tests and documentation

1. Add a test that every “districts affected” value is ≤ 707 if it is labeled as districts.
2. Add a test that persistent labels match the documented rule and expose the definition.
3. Add a test that no frontend direction is hardcoded to positive without a signed backend field.
4. Add a test that `High Priority` record counts and latest-unit counts are not displayed under the same label.
5. Add a test that unified state and unit counts agree with the normalized dataset.
6. Document the persistence rule, 707-unit definition, source-era caveat, and planning-focus limitations in the saved DSS report and UI.

---

## 11. Confirmed Findings vs Methodological Concerns

| Topic | Confirmed | Requires further investigation |
|---|---|---|
| Record count | 8,405 records, no missing fields, no duplicate keys | — |
| Unit count | 707 State–District units, one summary row each | Whether “district” is the right label for all units |
| Priority mapping | Exact direct mapping, 0 mismatches | Whether priority should remain a relabeling of risk |
| Planning rules | Six rules, exact focus mapping, 0 mismatches | Whether generic rules can support district-specific planning |
| Saved report numbers | Match saved CSVs | Report does not disclose persistence threshold |
| Persistence arithmetic | Counts and proportions add up | Whether any-two-year semantics are defensible |
| Persistence interpretation | 351/441 Persistent High are not latest High | Whether a majority/latest-based rule would change decisions |
| Planning focus mechanics | Top-3 absolute SHAP; exact rule mapping | Whether focus should use signed gaps and targets |
| Planning focus evidence | 26.91% extreme-opposite; 15.15% all top features favorable | Magnitude of misallocation if used operationally |
| Source confounding | Severe Anemia focus is 74.7% D2 vs 4.4% D1 | Whether focus is stable within era |
| API counts | Main DSS API counts match saved outputs | Record/unit labels and insufficient-history exposure |
| Unified API | 39 raw states vs 36; 850 raw units vs 812 normalized | Full normalization and downstream impact |
| Recent HMIS separation | 3,306 recent rows, 0 risk/priority, 2020–2025 | Comparability of recent indicators |
| Clinical framing | Saved DSS report and About page disclaim clinical use | Inconsistent “validated” wording elsewhere |

---

## 12. Concise Summary

- **Record-level DSS:** PASS numerically. 8,405 records, 707 units, 36 states/UTs, 2008–2019; no missing DSS fields; no duplicate keys.
- **Priority mapping:** PASS. High→High, Medium→Medium, Low→Low; 0 mismatches.
- **Planning rules:** PASS mechanically. Six rules, exact mapping, no missing focus.
- **Saved DSS report:** mostly consistent numerically and appropriately disclaims clinical use; fails to disclose the permissive persistence rule and directionless focus logic.
- **707-unit summary:** enumeration PASS, semantics FAIL. The summary is not a consistent or current priority ranking.
- **Persistent High:** 441 units, but only 91 latest High; 247/441 have a High minority; 351/441 are not latest High.
- **Insufficient History:** 0 under the current rule, but the rule is permissive and the category is not exposed by the API.
- **Planning focus:** top-3 absolute SHAP plus generic actions; not a district needs assessment. 26.91% of top-1 focuses are extreme-opposite; 15.15% have all three top features favorable.
- **Focus class pattern:** Medium Risk is 1,342/1,345 Severe Anemia; Low Risk is 1,714/4,446 Institutional Delivery; High Risk is 1,210/2,614 ANC.
- **Source confounding:** Severe Anemia focus is 74.7% of D2 rows versus 4.4% of D1 rows.
- **Frontend:** hardcoded “Increases risk” and hardcoded indicator thresholds are unsupported by saved DSS outputs.
- **Current/historical:** Overview’s “currently flagged” table uses 2016 record-level High rows; filtered record counts are labeled as districts.
- **Recent HMIS:** PASS for data separation and no risk assignment; unified API normalization still has 39-vs-36 state and 850-vs-812 unit defects.
- **No changes made:** no dataset, risk label, model, metric, DSS output, backend, or frontend file was modified. No output-regenerating test was run.

**Stop point:** This report is submitted for review. No fixes have been implemented.

---

## Appendix A — Read-Only Verification Performed

- Read the DSS generation code and traced the exact priority, top-feature, summary, and persistence logic.
- Recomputed all record counts, priority/risk counts, source counts, duplicate checks, and year coverage from the saved CSVs.
- Recomputed the 707-unit summary categories and cross-tabulated them against latest risk class.
- Recomputed high/medium/low year distributions, proportions, and short-history units.
- Merged the DSS CSV with `district_year_risk_clusters.csv` in memory to audit planning focus against actual indicator values.
- Computed top-1 feature counts by risk class and source.
- Computed adverse-side, extreme-opposite, and all-favorable focus shares using global medians as an audit reference.
- Called backend service functions directly for planning, districts, latest observations, overview, unified, and recent HMIS responses.
- Verified unified state and district normalization by comparing raw and normalized keys.
- Compared the saved DSS report with the saved CSVs.
- Did not modify any file other than creating this report.

## Appendix B — Reproduction Note

All diagnostics used `.venv/bin/python -B` and in-memory objects. No `pytest` suite was executed because several tests can rewrite or regenerate existing outputs. No model, dataset, risk label, cluster label, DSS output, backend file, or frontend file was changed.

**Relevant reproduction commands (read-only):**

```bash
.venv/bin/python -B -c "import pandas as pd; d=pd.read_csv('outputs/decision_support/district_decision_support.csv'); print(d.shape)"
wc -l reports/phase1_audit/dss_pipeline_audit_report.md
git status --short
```
