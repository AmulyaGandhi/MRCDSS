# HMIS Harmonization Audit - Inspection Report (Dataset 3 preparation)

Status: INSPECTION ONLY. No dataset was built; no pipeline/model/XAI/DSS/frontend/backend file was modified.

## A. Purpose & scope
Audit the six MRCDSS features carried through `dataset1.csv` (FY 2008-2016) and `dataset2.csv` (FY 2017-2019)
against the freshly acquired cumulative HMIS raw releases (FY 2020-21 .. 2024-25) to decide whether each feature can
be reconstructed from the raw files and whether definitions are stable across years. This is the prerequisite step
for any future 'Dataset 3 (2020-21 .. 2024-25)' build.

## B. Files available & years covered
Source manifest: `data/recent_hmis/raw/_manifest.json` (487 cumulative files listed). Download status:
- OK (SHA-256 verified): 419 files - FY 2020-21 (38), 2021-22 (36), 2022-23 (36), 2023-24 (36), 2024-25 (273)
- FAILED (HTTP 500, all): 68 files - FY 2025-26 (every file). 2025-26 files are listed by the anonymous `getFiles`
  API but cannot be downloaded anonymously (client-side network tracing showed a 2024-25 file succeeding moments
  before a 2025-26 file failed, repeatedly - not rate limiting). 2025-26 is excluded from this audit.
Verified downloaded bytes: 118,808,935.
Inspection used the 10 representative files below (structure, item dictionary, blanks/negatives, and reconstruction
statistics were computed on all of them).

## C. Raw workbook structure & parsing
- All files are single-sheet XLSX ("Data Item Wise Report"). Title, 'Provisional Figures for <FY> and Month - ...',
  'Status As On: <ts>', and a 'Total [(A+B) or (C+D)]' definition note occupy rows 0-3.
- Column layout: every state/district occupies 5 columns - Total [(A+B) or (C+D)], Public [A], Private [B],
  Urban [C], Rural [D]. District names start at column index 4; the first group (group 0) is the state itself.
- Data rows: module begins in column A only on section-start rows; column B holds the item code (apostrophe-prefixed
  string), column C the label, then the 5 columns per group (all 36 states -> 109 columns in UP files).
- Parsing caveat (verified): these workbooks have no usable XML <dimension>; `openpyxl.read_only=True` reports a
  1x1 cell range. All inspection loads use `read_only=False, data_only=True` (UP 2022-23 = 548 x 384).
- Internal consistency verified on multiple files & rows: for every item, Total == Public + Private == Urban + Rural
  and state total == sum of district totals (diff 0.0 on 1.1 ANC for UP 2022-23, UP 2024-25, Telangana 2021-22).

### Structure of the 10 sampled files
| FY | State | Groups | Districts | Rows | Cols | Item rows | Unique items | Duplicate-code rows | Blank cells | Negative cells |
|---|-------|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| 2020-21 | Uttar Pradesh | 76 | 75 | 548 | 384 | 540 | 372 | 168 | 5086 | 119 |
| 2020-21 | Telangana | 34 | 33 | 548 | 174 | 540 | 372 | 168 | 2886 | 59 |
| 2020-21 | Ladakh | 3 | 2 | 548 | 19 | 540 | 372 | 168 | 106 | 0 |
| 2021-22 | Telangana | 34 | 33 | 548 | 174 | 540 | 372 | 168 | 2435 | 46 |
| 2021-22 | Chandigarh | 2 | 1 | 548 | 14 | 540 | 372 | 168 | 54 | 0 |
| 2022-23 | Goa | 4 | 3 | 548 | 24 | 540 | 372 | 168 | 790 | 0 |
| 2022-23 | Uttar Pradesh | 76 | 75 | 548 | 384 | 540 | 372 | 168 | 6505 | 148 |
| 2023-24 | Tripura | 9 | 8 | 706 | 49 | 698 | 594 | 104 | 114 | 0 |
| 2024-25 | Uttar Pradesh | 76 | 75 | 706 | 384 | 698 | 594 | 104 | 5477 | 26 |
| 2024-25 | Ladakh | 3 | 2 | 706 | 19 | 698 | 594 | 104 | 51 | 0 |

## D. Item dictionary & schema versioning
- Old schema (2020-21 .. 2022-23): 540 item rows, decimal codes (1.1, 2.1.1.a); no explicit total-deliveries item 2.3.
- New schema (2023-24 .. 2024-25): item rows 698 but only 594 unique codes - the 104 extra rows are repeated-code,
  blank-label sub-rows for stock-balance rows in modules 17-20 (opening/closing balances). No indicator of maternal
  interest is duplicated. Code sets and labels are 100% identical between 2023-24 and 2024-25 (verified Tripura vs UP).
- Module 5 (Obstetric Complications aggregate 5.1) exists ONLY in the old schema; modules 1.9.x HRP items exist ONLY
  in the new schema.
- Item labels formally drift in the new schema: "pregnant women registered" -> "NEW Pregnant Women registered",
  "TT2/TT Booster" -> "Td2/Td Booster", severe-anaemia boundary "<7" -> "<=7 g/dl". Full old/new label pairs are in
  `item_dictionary.csv`.

## E. Six-feature mapping to exact HMIS items (see `maternal_indicator_mapping.csv`)
| Feature | Reconstructed formula | 2020-23 items | 2023-24+ items |
|---|------------------------|----------------|----------------|
| ANC_First_Trimester_Pct | 1.1.1 / 1.1 | 1.1.1, 1.1 | 1.1.1, 1.1 ('NEW' labels) |
| TT2_Booster_Pct | (1.2.2 + 1.2.3) / 1.1 | 1.2.2, 1.2.3, 1.1 | 1.2.2 (Td2), 1.2.3 (Td booster), 1.1 |
| Severe_Anemia_Pct | 1.4.3 / 1.4.2 | 1.4.3 (Hb<7), 1.4.2 (Hb<11) | 1.4.3 (Hb<=7), 1.4.2 (Hb<11 / 7.1-10.9 g/dl) |
| Institutional_Delivery_Pct | 2.2 / (total deliveries) | 2.2 / (2.1.1.a+2.1.1.b+2.2) - legacy published used 2.2/1.1 | 2.2 / 2.3 (explicit) or derived sum |
| PNC_48h_Pct | 6.1 (home-only) - NOT generalizable | 6.1 home 48h PNC; 2.2.1 inst discharged within 48h | 6.1 home 48h PNC; 2.2.1 inverted ('stayed 48h+') |
| Obstetric_Complications_Pct | 5.1 / total deliveries (2020-23) | 5.1 aggregate (APH/PPH/Sepsis/Eclampsia/others) | 1.9.1 total HRP intrapartum / 1.9.2 HRP antepartum (not comparable) |

## F. Harmonization matrix (definition changes across years)
See `harmonization_matrix.csv` (columns: Feature, Old Dataset Definition, HMIS per-year definitions, Comparable?,
Decision (YES/NO/UNCERTAIN), Reason/Evidence). Summary decisions:
- ANC_First_Trimester_Pct: DECISION **YES** (stable across all five years)
- TT2_Booster_Pct: DECISION **YES** (stable; caveat: TT2+Booster sum may double-count)
- Severe_Anemia_Pct: DECISION **UNCERTAIN** (threshold <7 -> <=7, denominator relabelled)
- Institutional_Delivery_Pct: DECISION **NO** (legacy denominator is ANC registrations, not reported deliveries;
  legacy values exceed 100% in several districts - same phenomenon already flagged in the legacy data pipeline)
- PNC_48h_Pct: DECISION **NO** (no within-48h institutional PNC item in any year; item set cannot reproduce feature)
- Obstetric_Complications_Pct: DECISION **NO** for 2023-24+ (5.1 removed; HRP items not an attended-cases measure);
  **YES** for 2020-21 .. 2022-23 (with proper denominator)

## G. Reconstruction checks (see `reconstruction_checks.csv`)
Ratios were recomputed from district Total columns for all 10 sample files. Representative results:
- 2022-23 UP (old schema, 75 districts): ANC 1st-tri median 78.5% (32.8-95.7); TT2+Booster median 82.6%; severe
  anaemia 1.4.3/1.4.2 median 6.5%; institutional 2.2/(home+inst) median 95.8%; PNC-48h 6.1/home+inst median 6.1%;
  obstet. comp. 5.1 median 4.1%. All plausible, none >100 for these constructions, no zero denominators.
- 2024-25 UP (new schema): ANC 1st-tri median 86.2%; TT2+Booster median 80.8%; severe 6.7%; institutional via 2.3
  median 98.2% but max 106.4% (2.2 > 2.3 in at least one district - data inconsistency); PNC 6.1 median 5.4%.
- 2023-24 Tripura (new schema, 8 districts): reconstructed values plausible; 5.1 absent; 1.9.1 == 1.9.1.a+.b+.c+.d in
  every district (sum self-consistent).

## H. Total-column & internal consistency checks
- Total == Public+Private == Urban+Rural with zero mismatches across inspected files/items.
- State total == sum of district totals (verified for 1.1 in UP 2022-23, UP 2024-25, Telangana 2021-22; diff 0.0).
- New-schema only: 2.3 (age-wise total deliveries) FAILS to equal sum(2.3.1..2.3.4) in 14/75 UP districts (2024-25 Apr)
  and fails to equal home+inst in others; 2.2 can exceed 2.3. Use 2.3 or the derived sum with care / validation.

## I. Data-quality findings
- Non-numeric cell values are exclusively EMPTY strings (suppression/absence); there are no '-', 'NA' or '<' markers
  anywhere in the sample. Blanks concentrate in small states (Goa: 1 district fully blank; Telangana: 1 district home
  delivery 2.1.1.a/2.1.1.b blank).
- Negative cell values exist only in vaccine/stock modules 17-20 (e.g. UP 2022-23: 148 negatives across stock rows;
  Ayodhya vaccine rows as large as -892,301). None of the six indicator items carry negatives.
- No decimal counts anywhere; all cells of interest are whole numbers.
- Files are explicitly marked 'Provisional Figures' (all days) and 'Status As On' is months later in some years
  (e.g. 2022-23 file 'Status As On: 01 Oct 2024'), indicating retroactive updating - cumulative provisional data.

## J. Published-percentage availability
A label scan of every sample file found exactly one item containing '%' or '(To Total)' per file: the stock item
'Glutaraldehyde 2%' (19.5). NO published percentage columns for any of the six indicators exist in the recent raw
files for any year 2020-21 .. 2024-25. Every indicator (and every denominator) must be RECONSTRUCTED from counts.

## K. Decisions & handling notes for a future Dataset 3 build
1. ANC_First_Trimester_Pct and TT2_Booster_Pct are safely reconstructable across all five years (denominator = 1.1).
2. Severe_Anemia_Pct is reconstructable but carries a small definitional drift (<7 -> <=7); document as approximate.
3. Institutional_Delivery_Pct must pick ONE denominator: (a) replicate legacy behaviour with ANC registrations (2.2/1.1,
   values can exceed 100 and are cleaned downstream like the legacy data), or (b) adopt %-of-total-reported-deliveries
   (2.2/(2.1.1.a+2.1.1.b+2.2) for 2020-23, 2.2/2.3 for 2023-24+). The two regimes are NOT comparable as-stated.
4. PNC_48h_Pct is NOT reconstructable as the feature was defined; at best the home-only 6.1 share is available.
5. Obstetric_Complications_Pct is reconstructable only for 2020-21 .. 2022-23 via 5.1; 2023-24+ has no comparable item.
6. Any rebuild must be gated on 2025-26 being unavailable anonymously; if 2025-26 is needed, an authenticated download
   path is required first.

## L. Artifact inventory & reproducibility
- `raw_structure_report.md`, `maternal_indicator_mapping.csv`, `harmonization_matrix.csv`, `reconstruction_checks.csv`,
  `item_dictionary.csv`, and this `inspection_report.md` - all under `data/recent_hmis/inspection/`.
- Reusable parsers: `data/recent_hmis/inspection/_lib/hmis_reader.py` (workbook loader / WorkSheet, DistrictGroup, Item)
  and `data/recent_hmis/inspection/_lib/reconstruct.py` (numeric coercion + per-district indicator computation).
- Generator: `data/recent_hmis/inspection/_lib/build_artifacts.py` re-creates every artifact (python, stdlib only,
  needs openpyxl in the environment venv). Raw files are read-only inputs; nothing outside inspection/ is written.
- Re-run: `.venv/bin/python data/recent_hmis/inspection/_lib/build_artifacts.py`
