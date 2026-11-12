# Risk Classification Report

**Date**: 2026-09-12
**Method**: K-Means clustering (K=3, random_state=42, n_init=10) on StandardScaler-normalized features
**Input**: `outputs/selected_features/final_model_features.csv`

---

## Final Feature List (6 features)

| Feature | Risk Direction |
|---------|---------------|
| ANC_First_Trimester_Pct | Higher = better (protective) |
| TT2_Booster_Pct | Higher = better (protective) |
| Severe_Anemia_Pct | Higher = worse (risk) |
| Institutional_Delivery_Pct | Higher = better (protective) |
| PNC_48h_Pct | Higher = better (protective) |
| Obstetric_Complications_Pct | Higher = worse (risk) |

---

## Cluster Sizes

| Cluster | Size | Risk Class |
|---------|------|------------|
| Cluster 0 | 4,446 | Low Risk |
| Cluster 1 | 1,345 | Medium Risk |
| Cluster 2 | 2,614 | High Risk |

---

## Cluster Profiles (median values)

| Feature | Cluster 0 (Low Risk) | Cluster 1 (Medium Risk) | Cluster 2 (High Risk) |
|---------|---------------------|------------------------|-----------------------|
| ANC_First_Trimester_Pct | 67.70 | 81.70 | 39.70 |
| TT2_Booster_Pct | 89.20 | 90.30 | 75.45 |
| Severe_Anemia_Pct | 3.60 | 67.60 | 4.90 |
| Institutional_Delivery_Pct | 69.80 | 74.60 | 42.30 |
| PNC_48h_Pct | 69.70 | 68.80 | 57.10 |
| Obstetric_Complications_Pct | 5.80 | 5.70 | 3.20 |

---

## Cluster Ranking: Low → Medium → High

**Cluster 0 → Low Risk**: Best overall profile. Moderate-to-high protective indicators (ANC=67.7, TT2=89.2, Inst Del=69.8, PNC=69.7) with very low risk indicators (Severe Anemia=3.6, Obs Comp=5.8). Represents districts-years with adequate maternal healthcare coverage.

**Cluster 1 → Medium Risk**: Highest protective indicators (ANC=81.7, TT2=90.3, Inst Del=74.6) but extremely high Severe Anemia (67.6%). This cluster is dominated by D2 (1,256/1,345 = 93.4%). The severe anemia rate is the dominant differentiating factor. Represents districts-years with good service coverage but severe anemia burden.

**Cluster 2 → High Risk**: Lowest protective indicators across all four protective features (ANC=39.7, TT2=75.5, Inst Del=42.3, PNC=57.1). Represents districts-years with the weakest maternal healthcare access. Risk indicators (Severe Anemia=4.9, Obs Comp=3.2) are also low, but the lack of protective care is the primary risk driver. Dominated by D1 (2,273/2,614 = 86.9%).

**Ranking rationale**: The ranking uses the multidimensional profile where the dominant differentiator across clusters is the protective indicator scores (ANC, TT2, Institutional Delivery, PNC). Cluster 2 has substantially lower protective care across all four indicators, making it the highest-risk group despite low risk-indicator values. Cluster 1 has the highest protective indicators but the extreme severe anemia (67.6%) prevents it from being Low Risk. Cluster 0 has consistently moderate-to-high protective indicators with low risk indicators.

---

## Clustering Metrics

| Metric | Value |
|--------|-------|
| K | 3 |
| random_state | 42 |
| n_init | 10 |
| Silhouette Score | 0.238081 |
| Davies-Bouldin Index | 1.473643 |
| Calinski-Harabasz Index | 2276.144882 |

**Interpretation**:
- Silhouette Score (0.24): Moderate cluster separation. Not strong but acceptable for K=3 on this data.
- Davies-Bouldin Index (1.47): Moderate intra-cluster compactness vs inter-cluster separation. Lower is better.
- Calinski-Harabasz Index (2276): High variance ratio between/within clusters, suggesting meaningful separation.

---

## Methodological Concerns

1. **Severe_Anemia_Pct drives Cluster 1**: The extremely high anemia median (67.6%) in Cluster 1 is the primary differentiator from Cluster 0. Given the known D1/D2 discrepancy in anemia measurement (D1 median 3.6% vs D2 median 51.5%), this cluster assignment may reflect data-source differences rather than true risk variation.

2. **D1/D2 composition bias**: Cluster 1 is 93.4% D2, Cluster 2 is 86.9% D1. The clustering partially separates by data source rather than purely by risk profile. This is a confounding factor.

3. **Risk indicators underweight**: The two risk indicators (Severe Anemia, Obstetric Complications) have much lower absolute values than the four protective indicators, causing the scoring formula to be dominated by protective indicators. Cluster 2 is labeled "High Risk" primarily due to low protective care, not high risk conditions.

4. **Silhouette Score 0.24**: Indicates moderate but not strong cluster separation. The three clusters may not represent maximally distinct groups.

---

## D1/D2 Distribution per Cluster

| Cluster | D1 rows | D2 rows | Total |
|---------|---------|---------|-------|
| Cluster 0 (Low Risk) | 3,931 | 515 | 4,446 |
| Cluster 1 (Medium Risk) | 89 | 1,256 | 1,345 |
| Cluster 2 (High Risk) | 2,273 | 341 | 2,614 |

---

## Output Files

| File | Description |
|------|-------------|
| `outputs/risk_classification/district_year_risk_clusters.csv` | Main output: 8,405 rows with 12 columns including cluster_id and risk_class |
| `outputs/risk_classification/cluster_profiles.csv` | Per-cluster mean and median for all 6 features |
| `outputs/risk_classification/cluster_centroids.csv` | Cluster centroids in standardized and original feature space |
| `outputs/risk_classification/clustering_metrics.txt` | Silhouette, DBI, CHI scores and cluster sizes |
| `outputs/risk_classification/risk_classification_report.md` | This report |

---

## Validation Summary

| Check | Result |
|-------|--------|
| 8,405 rows | ✓ |
| No duplicate State+District+Year+source_dataset | ✓ |
| Exactly 3 clusters | ✓ |
| Every row has exactly one cluster | ✓ |
| No missing cluster assignments | ✓ |
| Risk classes are Low/Medium/High only | ✓ |
| No feature values altered | ✓ |
| source_dataset preserved | ✓ |

**Note**: No supervised ML, risk scores, normalization, or clinical diagnoses were created. The risk classes are derived categories based on unsupervised clustering patterns.