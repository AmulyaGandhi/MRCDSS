# Harmonization Validation Report

**Date**: 2026-09-12
**Input**: `outputs/selected_features/maternal_model_features.csv`
**Purpose**: Validate comparability of 8 features between D1 (2008–2016) and D2 (2017–2019)

---

## State Count Discrepancy

| Metric | Value |
|--------|-------|
| States in D1 | 36 |
| States in D2 | 36 |
| States in selected_features | 36 |
| States in preprocessed_output | 36 |
| States in data_quality_report (earlier) | 37 (unverifiable — all current outputs consistently show 36) |

**Explanation**: Both `dataset1.csv` and `dataset2.csv` contain exactly 36 states with identical names. The earlier reference to 37 states is not reproducible from current data. Both datasets share 35 states; D1 has 3 districts not in D2 (Narayanpet, Eluru, Alluri Sitharama Raju — all in Telangana/Andhra Pradesh, likely created after 2016); D2 has 1 district not in D1 (Charki Dadri, Haryana). District counts: D1=706, D2=704. **36 is the correct count.**

---

## Feature-by-Feature Validation

### 1. ANC_First_Trimester_Pct
| | D1 | D2 |
|---|---|---|
| **Source column** | `Registrations For ANC In The First Trimester (To Total Anc Registrations) (%) (UOM:%(Percentage)), Scaling Factor:1` | `Registrations For ANC In The First Trimester (To Total Anc Registrations) (%) (UOM:%(Percentage)), Scaling Factor:1` |
| **Definition** | % of ANC registrations in first trimester | % of ANC registrations in first trimester |
| **Denominator** | Total ANC Registrations | Total ANC Registrations |
| **UOM** | %(Percentage) | %(Percentage) |
| **Risk direction** | lower = higher risk | lower = higher risk |
| **Comparable** | **YES** | |
| **Reason** | Same definition, denominator, and UOM. Minor whitespace differences in column name only. D1 has 15 values outside [0,100] (max 365.3%) indicating data quality issues, but the concept is identical. |

### 2. TT2_Booster_Pct
| | D1 | D2 |
|---|---|---|
| **Source column** | `Pregnant Women Received The Second Dose Of Tetanus-Toxoid Vaccine (Tt2) Or Booster (To Total Anc Registrations) (%)` | `Pregnant Women Received Tetanus-Toxoid Vaccine (Tt2) Or Tetanus-Toxoid (Tt) Booster (To Total Anc Registrations) (%)` |
| **Definition** | 2nd dose of Tt2 or booster | Tt2 or Tt booster |
| **Denominator** | Total ANC Registrations | Total ANC Registrations |
| **UOM** | %(Percentage) | %(Percentage) |
| **Risk direction** | lower = higher risk | lower = higher risk |
| **Comparable** | **YES** | |
| **Reason** | Conceptually identical — Tt booster = Booster. D2 explicitly names Tt (tetanus toxoid) as alternative; D1 uses generic "Booster". Same denominator and UOM. Both have values outside [0,100] due to data quality (D1 max 979.8%, D2 max 241.3%), but definition matches. |

### 3. IFA_Pct
| | D1 | D2 |
|---|---|---|
| **Source column** | `Women Received 100 Ifa Tablets (To Total Anc Registrations) (%)` | `Women Received 180 Ifa Tablets (To Total Anc Registrations) (%)` |
| **Definition** | % of ANC registrants who received **100** IFA tablets | % of ANC registrants who received **180** IFA tablets |
| **Denominator** | Total ANC Registrations | Total ANC Registrations |
| **UOM** | %(Percentage) | %(Percentage) |
| **Risk direction** | lower = higher risk | lower = higher risk |
| **Comparable** | **NO** | |
| **Reason** | D1 uses 100-tablet regimen (older National Iron Plus Initiative), D2 uses 180-tablet regimen (newer National Iron Foundation). These are **different coverage targets** — a woman receiving 100 tablets in D1 would be "fully covered" under D1's definition but "under-covered" under D2's. The percentages measure fundamentally different things. Do NOT modify. |

### 4. Severe_Anemia_Pct
| | D1 | D2 |
|---|---|---|
| **Source column** | `Pregnant Women With Hemoglobin (Hb) Levels<7 (Severe Anemia) (To Women With Hemoglobin (Hb) Levels<11 (Moderate Anemia)) (UOM:%(Percentage))` | `Pregnant Women With Hemoglobin (Hb) Levels<7 (Severe Anemia) (To Women With Hemoglobin (Hb) Levels<11 (Moderate Anemia)) (%) (UOM:%(Percentage))` |
| **Definition** | % of moderately anemic women (Hb<11) who have severe anemia (Hb<7) | % of moderately anemic women (Hb<11) who have severe anemia (Hb<7) |
| **Denominator** | Women with Hb<11 (Moderate Anemia) | Women with Hb<11 (Moderate Anemia) |
| **UOM** | %(Percentage) | %(Percentage) |
| **Risk direction** | higher = higher risk | higher = higher risk |
| **Comparable** | **UNCERTAIN** | |
| **Reason** | Same denominator and definition in wording. However, D1 median=3.6% vs D2 median=51.5% (raw) / 52.95% (selected). D1 max=2087.6%, D2 max=665.8% — both have extreme outliers (59 D2 values >100%). **Not determinable from dataset** whether this reflects: (a) genuinely different anemia prevalence between periods, (b) different data collection/quality, (c) scaling/unit errors in source data. The wording is identical but the magnitude difference is implausible for the same metric. |

### 5. Institutional_Delivery_Pct
| | D1 | D2 |
|---|---|---|
| **Source column** | `Institutional Deliveries (To Total Anc Registrations) (%) (UOM:%(Percentage)), Scaling Factor:1` | `Institutional Deliveries (To Total Anc Registrations) (%) (UOM:%(Percentage)), Scaling Factor:1` |
| **Definition** | % of ANC registrations resulting in institutional delivery | % of ANC registrations resulting in institutional delivery |
| **Denominator** | Total ANC Registrations | Total ANC Registrations |
| **UOM** | %(Percentage) | %(Percentage) |
| **Risk direction** | lower = higher risk | lower = higher risk |
| **Comparable** | **YES** | |
| **Reason** | Same definition, denominator, and UOM in both datasets. Data quality concerns: D1 has 179 values outside [0,100] (max 409%), D2 has 136 (max 163.1%). These likely reflect scaling errors in source data but the concept is the same. |

### 6. SBA_Home_Delivery_Pct
| | D1 | D2 |
|---|---|---|
| **Source column** | `Home Deliveries Attended By Skilled Birth Attendants (Sba) (To Total Reported Home Deliveries) (%)` | `Home Deliveries Attended By Skilled Birth Attendants (%)` |
| **Definition** | % of home deliveries attended by SBA | SBA attendance (%) — **denominator not specified** |
| **Denominator** | Total Reported Home Deliveries | **NOT SPECIFIED** |
| **UOM** | %(Percentage) | %(Percentage) |
| **Risk direction** | lower = higher risk | lower = higher risk |
| **Comparable** | **NO** | |
| **Reason** | D1 explicitly states denominator = "Total Reported Home Deliveries". D2 column simply says "(%)" with no denominator clause. Without knowing what D2 measures against, these are **not safely harmonizable**. D2 may use Total Reported Deliveries, Total Home Deliveries, or another base. Do NOT modify. |

### 7. PNC_48h_Pct
| | D1 | D2 |
|---|---|---|
| **Source column** | `Women Received Post Partum Check Up Within 48 Hours Of Delivery (To Total Reported Deliveries) (%)` | `Women Received Post Partum Check Up Within 48 Hours Of Delivery (To Total Reported Deliveries) (%)` |
| **Definition** | % of deliveries with PNC within 48 hours | % of deliveries with PNC within 48 hours |
| **Denominator** | Total Reported Deliveries | Total Reported Deliveries |
| **UOM** | %(Percentage) | %(Percentage) |
| **Risk direction** | lower = higher risk | lower = higher risk |
| **Comparable** | **YES** | |
| **Reason** | Same definition, denominator, and UOM. However, D2 has extreme outliers (max 9836.4%) suggesting severe data quality issues. D1 max=555.8%. Same concept but data needs cleaning before modelling. |

### 8. Obstetric_Complications_Pct
| | D1 | D2 |
|---|---|---|
| **Source column** | `Pregnant Women With Obstetric Complications (Who Were Attended To) (To Total Reported Deliveries) (%)` | `Pregnant Women With Obstetric Complications (Who Were Attended To) (To Total Reported Deliveries) (%)` |
| **Definition** | % of deliveries with obstetric complications | % of deliveries with obstetric complications |
| **Denominator** | Total Reported Deliveries | Total Reported Deliveries |
| **UOM** | %(Percentage) | %(Percentage) |
| **Risk direction** | higher = higher risk | higher = higher risk |
| **Comparable** | **YES** | |
| **Reason** | Same definition, denominator, and UOM. Reasonable value ranges (D1 max=129.6%, D2 max=121.1% — some outliers but plausible). Most comparable feature across datasets. |

---

## Summary

| Feature | Comparable | Primary Reason |
|---|---|---|
| ANC_First_Trimester_Pct | YES | Same definition, denominator, UOM |
| TT2_Booster_Pct | YES | Same concept; minor wording (Booster vs Tt Booster) |
| IFA_Pct | **NO** | Different tablet targets (100 vs 180) — different coverage concepts |
| Severe_Anemia_Pct | **UNCERTAIN** | Same wording but median 3.6% vs 51.5% — cause not determinable from dataset |
| Institutional_Delivery_Pct | YES | Same definition, denominator, UOM |
| SBA_Home_Delivery_Pct | **NO** | D1 denominator explicit; D2 denominator unspecified |
| PNC_48h_Pct | YES | Same definition, denominator, UOM |
| Obstetric_Complications_Pct | YES | Same definition, denominator, UOM |

**Not safely harmonizable**: IFA_Pct (different targets), SBA_Home_Delivery_Pct (unspecified denominator), Severe_Anemia_Pct (implausible median difference, cause unknown)

**Do not modify the selected dataset or preprocessing output.**