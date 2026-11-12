# Dataset 3 — Recent-HMIS Analytical Dataset

Standalone district-year analytical dataset of recent-HMIS maternal-health indicators, reconstructed from
National Health Systems Resource Centre (NHSRC) HMIS **cumulative annual** raw files.

## Purpose

Provide a clean, traceable, district × fiscal-year panel of reconstructed HMIS indicators for recent years
(2020-21 .. 2024-25) that can support future analytical work WITHOUT touching the historic MRCDSS pipeline
(`dataset1.csv`, `dataset2.csv`, preprocessing, models, XAI, DSS, frontend, backend all remain unchanged).

## Source

- Raw files: `data/recent_hmis/raw/` (downloaded from the HMIS portal `getFiles`/`downloadfiles` API;
  419 files SHA-256 verified).
- Provenance per file: `source_file_mapping.csv` (fiscal year, state, filename, cumulative month, server
  path, local path, SHA-256, districts parsed).
- Item mapping and definitions: `data/recent_hmis/inspection/` (`inspection_report.md`,
  `harmonization_matrix.csv`, `maternal_indicator_mapping.csv`, `item_dictionary.csv`).

## Years

- Full annual panel (all 36 states): 2020-2021, 2021-2022, 2022-2023, 2023-2024.
- 2024-2025: partial panel. Only the 17 states with an **UpTo_Mar** cumulative file acquired are included
  (Andaman & Nicobar, Arunachal Pradesh, Chandigarh, Delhi, Goa, Ladakh, Lakshadweep, Manipur, Meghalaya,
  Mizoram, Nagaland, Puducherry, Sikkim, Telangana, Dadra & Nagar Haveli and Daman and Diu, Tripura,
  Uttarakhand). The other 19 states have only partial cumulative months (Apr..Feb) in the acquisition;
  those files are kept untouched in `raw/` and are documented as available-but-excluded.
- 2025-26: not included (portal files return HTTP 500 on anonymous download; no authentication attempted).

## Annual UpTo_Mar selection

Dataset 3 uses exactly one annual file per State-Year: the **UpTo_Mar** cumulative file (the fiscal-year
total). Partial cumulative months are never used. FY 2020-21 uses the merged "The Dadra and Nagar Haveli
and Daman and Diu" file; the legacy pre-merger "Dadra & Nagar Haveli" and "Daman & Diu" files are excluded.

## District values

Each observation uses the district **Total** sub-column. Inspection verified `Total == Public + Private ==
Urban + Rural` and `State total == sum of district totals` with zero mismatches. Public/Private/Urban/Rural
are never used as district values.

## Dataset 3 structure

One row = State + District + Fiscal Year.

| Column | Meaning |
|---|---|
| State | HMIS state name from the raw file |
| District | District name from the raw file's Total column |
| Year | Fiscal year, e.g. `2020-2021` (matches the HMIS annual folder); not calendar years |
| source_dataset | `recent_hmis_annual_up_to_mar` |
| ANC_First_Trimester_Pct | Reconstructed `1.1.1 / 1.1 × 100` |
| TT2_Booster_Pct | Reconstructed `(1.2.2 + 1.2.3) / 1.1 × 100` |
| Severe_Anemia_Pct | Reconstructed `1.4.3 / 1.4.2 × 100` (recent-HMIS indicator only) |
| Obstetric_Complications_Pct | Reconstructed `5.1 / (2.1.1.a + 2.1.1.b + 2.2) × 100`, 2020-21 .. 2022-23 only |

Raw counts never appear in the primary CSV; they are retained in `indicator_counts.csv`.

## Reconstructed features

- **ANC_First_Trimester_Pct** — `1.1.1` (ANC registered within 1st trimester) / `1.1` (NEW PW ANC
  registered) × 100. Stable 2020-21 .. 2024-25 (1.1 gains the word "NEW" in labels from 2023-24; concept
  unchanged). Valid for 3,148/3,306 rows.
- **TT2_Booster_Pct** — `(1.2.2 TT2/Td2 + 1.2.3 TT/Td Booster) / 1.1 × 100`. New-schema labels use Td
  terminology. Valid for 3,148/3,306 rows.
- **Severe_Anemia_Pct** — `1.4.3 / 1.4.2 × 100`. Valid for 3,138/3,306 rows.
- **Obstetric_Complications_Pct** — `5.1 / (2.1.1.a + 2.1.1.b + 2.2) × 100` for 2020-2021 .. 2022-2023;
  NaN from 2023-2024 (aggregate item removed). Valid for 2,219/3,306 rows.

## Excluded features

- **Institutional_Delivery_Pct** — excluded (legacy denominator was ANC registrations; a different delivery
  structure exists in recent schemas; not comparable). See `excluded_features.md`.
- **PNC_48h_Pct** — excluded (no comparable within-48-hour institutional PNC indicator across the years).

Neither appears in `dataset3_recent_hmis.csv`.

## Caveat 1 — severe-anemia definition change

The paper definition changed across the schema: threshold `Hb < 7` (2020-23) to `Hb <= 7` (2023-24+) and
`Hb<11` was relabelled to `7.1-10.9 g/dl`. Dataset 3 presents Severe_Anemia_Pct **only as a recent-HMIS
indicator**. It is NOT claimed to be harmonized with the historic Dataset 1/2 feature and it carries an
explicit definition-change flag in `dataset3_metadata.json` and `feature_definitions.csv`. Values are not
adjusted to compensate.

## Caveat 2 — TT2/booster double-counting

The TT2_Booster numerator is the sum of TT2/Td2 and booster doses, which may double-count women given both.
This is preserved (numerator definition is not silently changed) and is the reason some values legitimately
exceed 100%.

## Caveat 3 — obstetric-complications schema break

HMIS removed the aggregate "obstetric complications attended" item `5.1` after 2022-23 and replaced it with
HRP intrapartum/antepartum event items. Dataset 3 therefore:

- provides Obstetric_Complications_Pct for 2020-2021, 2021-2022, 2022-2023;
- sets it NaN for 2023-2024 and 2024-2025;
- does NOT substitute HRP event-count components. The column is NOT continuously comparable 2020-2025.

## No imputation

No imputation, no zero-filling, no extrapolation and no inferred indicators. Every NaN means either
"underlying HMIS count blank/zero-denominator" or "structurally unavailable in that schema". Values <0 or
>100 are never clipped; they are listed in `percent_invalid_flags.csv`.

## No modification of original HMIS files

Raw XLSX files under `data/recent_hmis/raw/` are read-only inputs and were not altered. `dataset1.csv`,
`dataset2.csv`, all preprocessing / feature-selection / modelling / XAI / DSS outputs, backend and
frontend are untouched (verified by test suite against a pre-built SHA-256 baseline).

## No merging

Dataset 3 is standalone. It is not merged with Dataset 1/2 (the 8,405-row analytic set) and does not claim
direct comparability with historic MRCDSS features.

## Files

| File | Contents |
|---|---|
| `dataset3_recent_hmis.csv` | Primary analytical dataset (3,306 rows) |
| `dataset3_metadata.json` | Machine-readable metadata incl. caveats and validation rules |
| `feature_definitions.csv` | Per-feature formulas, HMIS items, availability, caveats |
| `coverage_by_year.csv` / `coverage_by_state.csv` | Coverage tables |
| `coverage_reference_missing_units.csv` / `coverage_new_units_not_in_707.csv` | Reference comparisons |
| `district_churn.csv` | Units appearing/disappearing between years |
| `indicator_counts.csv` | Raw numerator/denominator counts for every observation |
| `percent_invalid_flags.csv` | Flagged out-of-range / NaN-reason rows |
| `source_file_mapping.csv` | File-level provenance for all 161 used XLSX files |
| `data_quality_report.md` | Quality, missingness, invalid-value and coverage detail |
| `excluded_features.md` | Why Institutional / PNC features and partial/legacy files are excluded |
| `dataset3_build_report.md` | End-to-end build report (A-S) |
| `_lib/` | Build + report generators (openpyxl/pandas, stdlib) |
| `_protected_files_baseline.json` | SHA-256 snapshot proving other MRCDSS files were untouched |

## Reproduction

```
.venv/bin/python data/recent_hmis/dataset3/_lib/build_dataset3.py
.venv/bin/python data/recent_hmis/dataset3/_lib/build_reports.py
.venv/bin/python -m pytest tests/recent_hmis -q
```

## Requirements for use

`State + District + Year` is the unique observation key. District names repeat across states - never key on
District alone. NaN means unavailable; consult `percent_invalid_flags.csv` and `data_quality_report.md`
before any modelling interpretation of out-of-range values.