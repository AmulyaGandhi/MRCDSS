# Dataset 3 — Build Report

Standalone recent-HMIS analytical dataset. Constructed and validated by:
`data/recent_hmis/dataset3/_lib/build_dataset3.py` and `data/recent_hmis/dataset3/_lib/build_reports.py`.

## A. Dataset 3 purpose
A district × fiscal-year analytical panel of recent-HMIS maternal indicators reconstructed from the raw
annual cumulative HMIS files (FY 2020-21 .. 2024-25), fully standalone so that no part of the historic
MRCDSS pipeline (Dataset 1/2, preprocessing, feature selection, K-Means, supervised models, SHAP/XAI, DSS,
backend, frontend) had to be modified.

## B. Source files used
161 annual cumulative **UpTo_Mar** XLSX files selected from `data/recent_hmis/raw/_manifest.json` (status
`downloaded`, `cumulative_month = Mar`):
- 2020-2021: 36 states (merged "The Dadra and Nagar Haveli and Daman and Diu" file; legacy pre-merger
  Dadra & Nagar Haveli / Daman & Diu files excluded)
- 2021-2022: 36 states
- 2022-2023: 36 states
- 2023-2024: 36 states
- 2024-2025: 17 states (only those with an acquired UpTo_Mar file)
File-level provenance (server path, local path, SHA-256, month, districts parsed): `source_file_mapping.csv`.

## C. Years included
2020-2021, 2021-2022, 2022-2023, 2023-2024 (full), 2024-2025 (partial), as the HMIS fiscal-year folders
identify them. No calendar-year conversion.

## D. States/year coverage
- 2020-2021 .. 2023-2024: 36 states per year.
- 2024-2025: 17 states (Andaman & Nicobar Islands, Arunachal Pradesh, Chandigarh, Delhi, Goa, Ladakh,
  Lakshadweep, Manipur, Meghalaya, Mizoram, Nagaland, Puducherry, Sikkim, Telangana, The Dadra and Nagar
  Haveli and Daman and Diu, Tripura, Uttarakhand). The other 19 states have only partial cumulative months
  in the acquisition and are excluded from the annual panel.
- 2025-26: not included (HTTP 500 on anonymous download; not retried).
See `coverage_by_year.csv` and `coverage_by_state.csv`.

## E. Observations
3,306 State-District-Year rows (782 / 782 / 791 / 783 / 168 per year).

## F. Unique State-District units
812 (alias-normalised names; e.g. HMIS "Bara Banki" = "Barabanki"). 36 states overall.

## G. Feature definitions
| Feature | Formula | Items | Availability |
|---|---|---|---|
| ANC_First_Trimester_Pct | 1.1.1 / 1.1 × 100 | 1.1.1, 1.1 | all years |
| TT2_Booster_Pct | (1.2.2 + 1.2.3) / 1.1 × 100 | 1.2.2, 1.2.3, 1.1 | all years |
| Severe_Anemia_Pct | 1.4.3 / 1.4.2 × 100 | 1.4.3, 1.4.2 | all years |
| Obstetric_Complications_Pct | 5.1 / (2.1.1.a+2.1.1.b+2.2) × 100 | 5.1, 2.1.1.a, 2.1.1.b, 2.2 | 2020-21..2022-23 |

All percentages use district Total counts; never clipped; NaN for denominator == 0 or missing
counts. `feature_definitions.csv` holds formulas and caveats.

## H. Excluded features and why
- **Institutional_Delivery_Pct**: legacy definition used ANC registrations as denominator (2.2/1.1);
  recent schema has a different delivery structure; constructing it would cement a non-comparable feature.
- **PNC_48h_Pct**: no comparable within-48 h institutional PNC indicator across the years (6.1 home-only,
  6.2 is 48h-14d, 2.2.1 wording inverted across eras).
Full rationale: `excluded_features.md`. These columns do not exist in Dataset 3.

## I. Severe-anemia caveat
Threshold changed `<7` (2020-23) -> `<=7` (2023-24+) and `Hb<11` relabelled (`7.1-10.9 g/dl`). Dataset 3
presents Severe_Anemia_Pct only as a recent-HMIS indicator, flagged in metadata; values not adjusted.

## J. TT2/booster caveat
Numerator = TT2/Td2 + TT/Td Booster which may double-count women given both. Preserved as specified; this
legitimately yields values >100 (368 such rows, max 185.93).

## K. Obstetric-complications schema break
Aggregate item 5.1 was removed after 2022-23. Dataset 3 provides the column for 2020-21 .. 2022-23 only and
sets it NaN for 2023-24 and 2024-25 (783 + 168 structurally-missing rows). HRP components are not used as a
replacement, so the column is continuous only within 2020-23.

## L. Missingness
| Feature | Missing | % |
|---|---|---|
| ANC_First_Trimester_Pct | 158 | 4.8 |
| TT2_Booster_Pct | 158 | 4.8 |
| Severe_Anemia_Pct | 168 | 5.1 |
| Obstetric_Complications_Pct | 1,087 (951 structural) | 32.9 |

Missing cells are blank HMIS counts or structurally-absent items (never imputed). The 158 ANC/TT2-missing
rows are fully blank (data-less) district rows.

## M. Invalid-value counts
| Feature | <0 | >100 | Max |
|---|---|---|---|
| ANC_First_Trimester_Pct | 0 | 0 | 100.00 |
| TT2_Booster_Pct | 0 | 368 | 185.93 (legitimate double-count) |
| Severe_Anemia_Pct | 0 | 5 | 354.55 (impossible n>d; data anomaly) |
| Obstetric_Complications_Pct | 0 | 11 | 762.43 (UP-Ghazipur 2021-22 outlier; n=546,611) |

All flagged in `percent_invalid_flags.csv`; none modified.

## N. Duplicate checks
0 duplicate (State, District, Year) rows. No duplicate district names within any used file's indicator rows.

## O. Coverage differences from the 707-unit MRCDSS reference
- Reference: 36 states, 707 State-District units (from dataset1 + dataset2).
- 2020-21, 2021-22, 2023-24 each match all 707 reference units (100%).
- 2022-23 matches 687 (20 units temporarily renamed/reorganised; all return by 2023-24).
- 2024-25 matches 142 (partial 17-state panel; 565 reference units belong to the 19 absent states).
- Across all five years **0** reference units are missing. 105 "new" units exist that are not in the 707
  (districts created/renamed since 2019). Lists: `coverage_reference_missing_units.csv`,
  `coverage_new_units_not_in_707.csv`, `district_churn.csv`.

## P. Source/provenance summary
Every observation is traceable via (State, District, Year) to a single annual UpTo_Mar XLSX file; the file
is linked to its manifest record (server path, filename, SHA-256) in `source_file_mapping.csv`, and the raw
numerator/denominator HMIS counts used for every percentage are in `indicator_counts.csv`.

## Q. Test results
Test suite: `tests/recent_hmis/test_dataset3.py` (16 test items). Run:
`.venv/bin/python -m pytest tests/recent_hmis -q` -> **16 passed** (3 benign openpyxl style warnings).

| # | Requirement | Status |
|---|---|---|
| 1 | No duplicate State/District/Year rows | PASS |
| 2 | District Total used (verified against raw Total; differs from Urban) | PASS |
| 3 | Percent formulas correct (recomputed from raw counts on 3 files) | PASS |
| 4 | Zero denominators produce NaN | PASS |
| 5 | Missing numerators/denominators produce NaN (incl. structural) | PASS |
| 6 | Obstetric complications unavailable from 2023-24 onward | PASS |
| 7 | Institutional Delivery and PNC 48h absent as fabricated columns | PASS |
| 8 | Severe-anemia definition-change metadata present | PASS |
| 9 | TT2/booster double-count caveat present | PASS |
| 10 | Raw HMIS XLSX files unchanged (SHA-256 vs baseline) | PASS |
| 11 | dataset1.csv / dataset2.csv unchanged | PASS |
| 12 | Existing MRCDSS outputs unchanged (models, outputs, src, backend, frontend) | PASS |

## R. Limitations
- 2024-25 panel covers only 17 states (19 absent).
- 2025-26 absent (unavailable via anonymous API).
- Severe anemia is a recent-HMIS indicator only (definition changed); not harmonized with historic data.
- TT2/booster >100 reflects the preserved double-counting construction.
- Obstetric complications are unavailable 2023-24+ (schema break).
- All raw files are "Provisional" cumulative releases and several carry later "Status As On" dates.
- Out-of-range severe-anemia (n>d) and the Ghazipur 762% value are raw data anomalies left unmodified.

## S. Recommendation for the next modelling phase
- Keep Dataset 3 fully standalone; do not merge with Dataset 1/2 until the two Indicator-comparability
  caveats (severe-anemia threshold, TT2/booster double-counting, obstetric schema break) are resolved.
- If historic comparability is required, restrict to ANC_First_Trimester_Pct (and TT2_Booster_Pct with the
  caveat) across all five years, dropping 2024-25 rows for the 19 unavailable states (or treating 2024-25
  as a separate partial panel).
- Treat flags in `percent_invalid_flags.csv` as hard exclude-by-default candidates for modelling
  (especially KK-Kishtwar, AR-East Kameng severe-anemia rows and UP-Ghazipur 2021-22 obstetric row).
- Any model trained on Dataset 3 must use (State, District, Year) as keys and must not impute NaN.