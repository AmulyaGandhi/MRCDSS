# Dataset 3 — Excluded Features and Excluded Source Files

## A. Features deliberately NOT constructed (by inspection decision)

### 1. Institutional_Delivery_Pct — excluded
The legacy MRCDSS feature used a published percentage **"Institutional Deliveries (To Total ANC
Registrations) (%)"** — i.e. denominator = ANC registrations (`2.2 / 1.1`). The newer HMIS delivery
schema exposes a different delivery structure (explicit total-reportable-deliveries item `2.3` from
2023-24 only, home + institutional composition), so:

- An ANC-registration-denominated value would be **non-comparable** across years and can exceed 100% by
  construction (long-standing issue already seen and cleaned in the legacy pipeline).
- A reported-deliveries-denominated value would be a **different feature** than the legacy one, and the
  two regimes cannot be reconciled from the raw files.

No Institutional_Delivery_Pct column appears in `dataset3_recent_hmis.csv`.

### 2. PNC_48h_Pct — excluded
The inspection found no comparable within-48-hour PNC indicator across the required years:

- `6.1` records first postpartum check-up within 48 h **of home delivery only**;
- `6.2` records 48 h - 14 d check-ups (institutional scope in the new schema);
- `2.2.1` relates to discharge/stay timing, not PNC, and its wording **inverts** across eraa
  ("discharged within 48 hours" 2020-23 vs "stayed 48 hours or more" 2023-24+).

There is no within-48 h institutional PNC item in any year. Fabricating the feature (e.g. using `6.1`
alone) would misrepresent coverage, so no PNC_48h_Pct column appears in Dataset 3.

### 3. Severe_Anemia_Pct — present but NOT harmonized
Included for reference only as a recent-HMIS indicator. The definition changed across the schema
(threshold `<7` -> `<=7`; `Hb<11` relabelled to `7.1-10.9 g/dl`). It is **not** claimed to equal the
legacy Dataset 1/2 feature and carries an explicit definition-change flag in the metadata/feature
definitions. Values were not modified to compensate.

### 4. Obstetric_Complications_Pct — omitted from 2023-24 onward
The aggregate item `5.1` exists for 2020-21 .. 2022-23 only. From 2023-24 the schema replaced it with HRP
intrapartum/antepartum event items (`1.9.1`/`1.9.2`), which are facility-based event counts that omit APH
and "other" complications and are not an attended-cases measure. Per instructions, Dataset 3 leaves the
column NaN for 2023-24 and 2024-25 and does **not** substitute HRP components.

## B. Source files excluded from the annual panel (kept untouched in `raw/`)

### 1. FY 2020-21 legacy pre-merger UT files
- `Dadra & Nagar Haveli` (L-Dadra & Nagar Haveli_UpTo_Mar.xlsx)
- `Daman & Diu` (L-Daman & Diu_UpTo_Mar.xlsx)

Superseded by the merged "The Dadra and Nagar Haveli and Daman and Diu" annual file (the only form present
in 2021-22 .. 2024-25). Using the legacy pair would double-represent one UT.

### 2. FY 2024-25 partial cumulative-month files (available-but-excluded)
The portal provides monthly cumulative files for 2024-25. Only the annual **UpTo_Mar** file is the fiscal
year total. The following months were downloaded (per state coverage) but are **not** used in the annual
panel: Apr (36), May (36), Jun (36), Jul (36), Aug (36), Sep (36), Oct (8), Nov (10), Dec (8), Jan (6),
Feb (8). 19 of 36 states have NO 2024-25 UpTo_Mar file in the acquisition; those states are absent from
Dataset 3's 2024-2025 panel (17 states included).

### 3. FY 2025-26 — not included
All 68 listed files returned HTTP 500 on anonymous download and are not present in the acquired `raw/`
collection. No retry or authentication was attempted during Dataset 3 construction; 2025-26 is simply
outside the dataset.

## C. Multiple-numerator-count columns policy
No raw HMIS sub-columns (Public/Private/Urban/Rural) are used for district values. Every observation is
the district **Total**. Raw counts never enter `dataset3_recent_hmis.csv`; they are preserved for
auditing in `indicator_counts.csv`.