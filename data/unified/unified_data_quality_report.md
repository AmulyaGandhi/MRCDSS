# Unified Data Quality Report

Unified MRCDSS + Recent HMIS analytical dataset (`unified_mr_cdss_data.csv`).

## 1. Provenance

- Historical records come from the harmonised analytical form of Dataset 1/2 used by the existing MRCDSS model (`outputs/risk_classification/district_year_risk_clusters.csv` + `outputs/decision_support/district_decision_support.csv`), preserving each original State-District-Year record.
- `SBA_Home_Delivery_Pct` for historical records is sourced from the raw Dataset 1/2 files (kept as a raw reference; it was excluded from model harmonization).
- Recent HMIS records come from `dataset3_recent_hmis.csv`; each retains `hmis_source_file` tracing it to its annual cumulative HMIS file.

## 2. Row counts

- Dataset 1: 6293
- Dataset 2: 2112
- Recent HMIS (Dataset 3): 3306
- Unified total: 11711 (expected 11711)
- Accidental duplicate (State, District, Year, source_dataset) records: 0

## 3. Time range

- Historical MRCDSS: 2008 .. 2019
- Recent HMIS: 2020-2021 .. 2024-2025
- 2024-25 is a partial year (17 states with complete UpTo_Mar files).

## 4. Feature availability

| Indicator | Historical (D1/D2) | Recent HMIS (D3) |
|---|---|---|
| ANC_First_Trimester_Pct | available | available (comparable) |
| TT2_Booster_Pct | available | available (comparable with caveat) |
| Severe_Anemia_Pct | available | available (definition changed) |
| Institutional_Delivery_Pct | available | NaN (not available) |
| SBA_Home_Delivery_Pct | raw reference (historical only) | NaN (not available) |
| PNC_48h_Pct | available | NaN (not available) |
| Obstetric_Complications_Pct | available | available through 2022-23; NaN from 2023-24 (schema change) |

No unavailable value was imputed; unavailable indicators are NaN (never 0).

## 5. Risk classification availability

- Every historical record retains its original MRCDSS risk class (High/Medium/Low) unchanged.
- No recent HMIS record carries a risk classification; `risk_classification_available` is false for the recent era.

## 6. Checks

- Source datasets verified byte-identical via the protected-file baseline (dataset1.csv, dataset2.csv, raw HMIS XLSX, dataset3_recent_hmis.csv).
- Unified row count = sum of era counts; no accidental deduplication across eras.
- Recent HMIS indicators present exactly as provided (ANC, TT2, Severe Anemia, Obstetric through 2022-23).