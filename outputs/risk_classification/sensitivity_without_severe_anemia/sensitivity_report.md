# Sensitivity Analysis Report: Clustering Without Severe_Anemia_Pct

**Date**: 2026-09-12
**Purpose**: Test whether Severe_Anemia_Pct is a necessary feature for meaningful clustering, given the unresolved D1/D2 measurement discrepancy (D1 median 3.6% vs D2 median 51.5%).

---

## Experimental Design

| Aspect | Primary (6-Feature) | Sensitivity (5-Feature) |
|--------|---------------------|------------------------|
| Features | All 6 validated features | Excludes Severe_Anemia_Pct |
| K | 3 | 3 |
| random_state | 42 | 42 |
| n_init | 10 | 10 |
| Scaling | StandardScaler | StandardScaler |

---

## Cluster Sizes Comparison

| Cluster | 6F Size | 6F Risk | 5F Size | 5F Risk | Size Change |
|---------|---------|---------|---------|---------|-------------|
| Cluster 0 | 4,446 | Low Risk | 3,747 | Low Risk | -700 (-15.7%) |
| Cluster 1 | 1,345 | Medium Risk | 961 | High Risk | -384 (-28.5%) |
| Cluster 2 | 2,614 | High Risk | 3,697 | Medium Risk | +1,083 (+41.4%) |

---

## Clustering Metrics Comparison

| Metric | 6-Feature | 5-Feature | Better |
|--------|-----------|-----------|--------|
| Silhouette Score | 0.238081 | 0.231495 | 6F (slightly) |
| Davies-Bouldin Index | 1.473643 | 1.442950 | 5F (slightly) |
| Calinski-Harabasz Index | 2276.145 | 2661.670 | 5F |

**Note**: No single metric decisively favors either model. Silhouette marginally favors 6F; DBI and CHI marginally favor 5F. All differences are small.

---

## Median Profiles Comparison

### 6-Feature Model (includes Severe_Anemia_Pct)

| Feature | Cluster 0 (Low Risk) | Cluster 1 (Medium Risk) | Cluster 2 (High Risk) |
|---------|---------------------|------------------------|-----------------------|
| ANC_First_Trimester_Pct | 67.7 | **81.7** | 39.7 |
| TT2_Booster_Pct | 89.2 | **90.3** | 75.5 |
| Severe_Anemia_Pct | 3.6 | **67.6** | 4.9 |
| Institutional_Delivery_Pct | 69.8 | **74.6** | 42.3 |
| PNC_48h_Pct | 69.7 | 68.8 | 57.1 |
| Obstetric_Complications_Pct | 5.8 | 5.7 | 3.2 |

### 5-Feature Model (excludes Severe_Anemia_Pct)

| Feature | Cluster 0 (Low Risk) | Cluster 1 (High Risk) | Cluster 2 (Medium Risk) |
|---------|---------------------|----------------------|------------------------|
| ANC_First_Trimester_Pct | 78.3 | 36.6 | 52.1 |
| TT2_Booster_Pct | 90.7 | 46.8 | 86.6 |
| Institutional_Delivery_Pct | 77.5 | 35.1 | 54.9 |
| PNC_48h_Pct | 75.4 | 66.9 | 64.0 |
| Obstetric_Complications_Pct | 7.9 | 5.1 | 3.5 |

---

## D1/D2 Distribution per Cluster

### 6-Feature Model
| Cluster | D1 | D2 | D1% | D2% |
|---------|----|----|-----|-----|
| Cluster 0 (Low) | 3,931 | 515 | 88.4% | 11.6% |
| Cluster 1 (Medium) | 89 | 1,256 | 6.6% | 93.4% |
| Cluster 2 (High) | 2,273 | 341 | 87.0% | 13.0% |

### 5-Feature Model
| Cluster | D1 | D2 | D1% | D2% |
|---------|----|----|-----|-----|
| Cluster 0 (Low) | 2,395 | 1,352 | 63.9% | 36.1% |
| Cluster 1 (High) | 778 | 183 | 81.0% | 19.0% |
| Cluster 2 (Medium) | 3,120 | 577 | 84.4% | 15.6% |

---

## Silhouette Score per Cluster

| Cluster | 6F Mean Silhouette | 5F Mean Silhouette |
|---------|-------------------|-------------------|
| Cluster 0 | 0.3088 | 0.2481 |
| Cluster 1 | 0.2528 | 0.1535 |
| Cluster 2 | 0.1102 | 0.2349 |

The 6F model has one well-separated cluster (C0) and one poorly separated (C2). The 5F model has more balanced separation across all three clusters.

---

## Interpretability Assessment

### 6-Feature Model
- **Cluster 0 (Low Risk)**: Moderate-to-high protective indicators, very low risk indicators. **Interpretable.**
- **Cluster 1 (Medium Risk)**: Highest protective indicators but extreme Severe Anemia (67.6%). Driven by Severe_Anemia_Pct. 93.4% D2. **Partially interpretable** — the anemia anomaly may reflect D2 measurement differences, not true risk.
- **Cluster 2 (High Risk)**: Lowest protective indicators across all four (ANC=39.7, TT2=75.5, ID=42.3, PNC=57.1). Risk indicators also low (SA=4.9, OC=3.2). **Somewhat confusing** — labeled "High Risk" due to low care, but low complications.

### 5-Feature Model
- **Cluster 0 (Low Risk)**: Highest protective indicators (ANC=78.3, TT2=90.7, ID=77.5, PNC=75.4). Low risk indicators (OC=7.9). **Clear and interpretable.**
- **Cluster 1 (High Risk)**: Lowest protective indicators across ALL four (ANC=36.6, TT2=46.8, ID=35.1, PNC=66.9). **Very clear "high risk" profile** — represents districts-years with weakest maternal healthcare access.
- **Cluster 2 (Medium Risk)**: Moderate protective indicators (ANC=52.1, TT2=86.6, ID=54.9, PNC=64.0). Low risk indicators (OC=3.5). **Interpretable as intermediate.**

---

## Key Findings

1. **5F eliminates the D2-dominated cluster**: In 6F, Cluster 1 was 93.4% D2. In 5F, no cluster has extreme D1/D2 dominance. This suggests Severe_Anemia_Pct was a primary driver of source-based separation.

2. **5F has clearer High Risk profile**: The 5F High Risk cluster (n=961) shows uniformly low protective indicators, making it unambiguously "least access to care." The 6F High Risk cluster was confounded by low risk indicators (Severe Anemia=4.9, OC=3.2).

3. **6F has slightly better overall silhouette**: 0.238 vs 0.231, but the difference is negligible.

4. **5F has more balanced per-cluster separation**: 5F silhouette ranges 0.15-0.25, while 6F ranges 0.11-0.31. The 5F model avoids the poorly separated C2 (0.11) seen in 6F.

5. **Risk class labels shifted**: Despite using the same ranking methodology, the 5F model assigned different risk classes to different clusters, confirming that Severe_Anemia_Pct influences cluster composition and therefore risk labeling.

6. **Neither model is clearly superior on metrics**: The metric differences are small and mixed (Silhouette slightly favors 6F, DBI and CHI favor 5F).

---

## Recommendation

**PRIMARY = 6-Feature Model**

**Rationale**:
- **Clinical completeness**: Severe_Anemia_Pct is a validated maternal-health indicator with established clinical relevance. Excluding it loses a clinically important dimension even if it introduces D1/D2 measurement noise.
- **Feature selection was already validated**: The harmonization validation report documented the Severe_Anemia_Pct discrepancy but did not recommend exclusion — it was classified as UNCERTAIN, not NO.
- **Sensitivity analysis is exploratory**: This 5-feature model serves as a diagnostic tool, not a replacement. Its value is in revealing that Severe_Anemia_Pct contributes to source-driven separation, not in proving the feature should be removed.
- **Metric differences are marginal**: No metric decisively favors the 5-feature model. The 5F model's clearer High Risk profile comes at the cost of losing anemia information.
- **Next step**: The appropriate action for the Severe_Anemia_Pct discrepancy is to investigate and resolve the D1/D2 measurement difference, not to remove the feature.

**The 5-feature model is recommended as a secondary/robustness check**, not a replacement. Future iterations should resolve the Severe_Anemia_Pct measurement discrepancy before finalizing the feature set for supervised modeling.
