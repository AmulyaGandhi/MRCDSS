# SHAP Explainability Analysis

**Model**: Logistic Regression (best-performing supervised classifier)
**Purpose**: Explain why the model assigns each district-year to its derived risk class.

## Important Interpretation Notes

- Risk labels originate from **K-Means clustering** (derived, not clinical ground truth).
- SHAP explains the **Logistic Regression model's classification behavior**.
- This analysis shows which features **contributed to the model's classification**.
- This is **NOT** clinical causal inference. Features do not clinically cause risk.
- K-Means risk classes are the target; the supervised classifier reproduces these derived profiles.

## Global Feature Importance

Ranked by mean absolute SHAP value on the test set:

| Rank | Feature | Mean |SHAP| |
|------|---------|------------|
| 1 | ANC_First_Trimester_Pct | 4.726665 |
| 2 | Institutional_Delivery_Pct | 4.518858 |
| 3 | TT2_Booster_Pct | 3.041540 |
| 4 | PNC_48h_Pct | 2.293318 |
| 5 | Severe_Anemia_Pct | 2.274658 |
| 6 | Obstetric_Complications_Pct | 0.633055 |

## Class-Specific Interpretation

### Low Risk
(n=889 district-years)

Features most contributing to the model's classification for this class:

| Feature | Mean |SHAP| | Contribution Direction |
|---------|------------|------------------------|
| Institutional_Delivery_Pct | 3.9358 | protective |
| ANC_First_Trimester_Pct | 3.6778 | protective |
| TT2_Booster_Pct | 2.2481 | protective |

### Medium Risk
(n=269 district-years)

Features most contributing to the model's classification for this class:

| Feature | Mean |SHAP| | Contribution Direction |
|---------|------------|------------------------|
| Severe_Anemia_Pct | 6.0599 | risk |
| ANC_First_Trimester_Pct | 5.6705 | protective |
| Institutional_Delivery_Pct | 4.5321 | protective |

### High Risk
(n=523 district-years)

Features most contributing to the model's classification for this class:

| Feature | Mean |SHAP| | Contribution Direction |
|---------|------------|------------------------|
| ANC_First_Trimester_Pct | 6.0241 | protective |
| Institutional_Delivery_Pct | 5.5031 | protective |
| TT2_Booster_Pct | 4.5280 | protective |

## Representative District-Year Explanations

Local SHAP explanations for one example from each risk class:

### Low Risk
**Location**: Telangana, Warangal
**Year**: 2019

Top contributing features to the model's classification:

| Feature | Feature Value | SHAP Value | Direction |
|---------|--------------|------------|-----------|
| Institutional_Delivery_Pct | 92.00 | 3.7236 | increases risk |
| ANC_First_Trimester_Pct | 83.40 | 2.0392 | increases risk |
| TT2_Booster_Pct | 95.80 | 2.0157 | increases risk |

### Medium Risk
**Location**: Karnataka, Haveri
**Year**: 2018

Top contributing features to the model's classification:

| Feature | Feature Value | SHAP Value | Direction |
|---------|--------------|------------|-----------|
| ANC_First_Trimester_Pct | 93.00 | 6.2074 | increases risk |
| Severe_Anemia_Pct | 36.00 | 5.2292 | increases risk |
| Institutional_Delivery_Pct | 74.50 | 2.1054 | increases risk |

### High Risk
**Location**: West Bengal, Kolkata
**Year**: 2014

Top contributing features to the model's classification:

| Feature | Feature Value | SHAP Value | Direction |
|---------|--------------|------------|-----------|
| TT2_Booster_Pct | 32.40 | 13.8821 | increases risk |
| ANC_First_Trimester_Pct | 33.40 | 7.1367 | increases risk |
| PNC_48h_Pct | 79.50 | -1.8988 | decreases risk |

## Methodology Limitations

1. **Derived labels**: Risk classes originate from K-Means, not clinical assessment.
2. **Model explanation, not causal inference**: SHAP values indicate contribution to the model's classification, not clinical causation.
3. **Logistic Regression**: Linear model explanations may not capture non-linear relationships that tree-based models would find.
4. **Test set only**: Explanations are for the 20% held-out test set (1,681 district-years).
5. **Feature correlation**: SHAP may distribute importance among correlated features, affecting individual attribution.