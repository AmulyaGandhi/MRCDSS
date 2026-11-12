# Dataset 3 District Coverage / Churn Audit

**Generated:** 2026-09-21T17:07:49+00:00 UTC  

**Status:** MAPPING-PROPOSAL ONLY - no merges applied, no source files modified.

## A. Original MRCDSS reference (dataset1.csv + dataset2.csv)

- **707** unique (State, District) units across **36** states (normalised spelling).
- Units defined by `norm()` = lowercase, `&`->`and`, drop non [a-z0-9]; `Bara Banki`==`Barabanki`, `Kushi Nagar`==`Kushinagar`, `Coochbehar`==`Cooch Behar`, etc.
- Histories: dataset1 = FY2008-2009..2016-2017, dataset2 = FY2017-2018..2019-2020; a unit enters the reference if present in any historical year.
- The reference is itself heterogeneous (AP uses the 26-district scheme for 2008-2013 and the 13-district scheme for 2014-2019; post-2016 districts such as MP `Niwari` and the 2016 Manipur units are absent). These gaps explain part of the 105.

## B. Dataset 3 footprint (FY2020-2021 .. 2024-2025)

| Fiscal year | States | Units | Matched reference | Ref missing | New units |
|---|---|---:|---:|---:|---:|
| 2020-2021 | 36 | 782 | 707 | 0 | 75 |
| 2021-2022 | 36 | 782 | 707 | 0 | 75 |
| 2022-2023 | 36 | 791 | 687 | 20 | 104 |
| 2023-2024 | 36 | 783 | 707 | 0 | 76 |
| 2024-2025 | 17 | 168 | 142 | 565 | 26 |

- Overall: **812** unique units in Dataset 3 vs **707** in reference; **707** matched, **105** unmatched new units, **0** reference units absent from Dataset 3.
- 2024-2025 is partial (UpTo_Mar files for 17 states only), so its data is not comparable; all 707 reference units are nevertheless represented across the DS3 window.

## C. The 105 unmatched units - classification

| Candidate_Type | Count | Meaning |
|---|---:|---|
| FORMAT_VARIANT | 13 | spelling/punctuation variant of a reference unit (same territory) |
| ALIAS_CANDIDATE | 7 | renamed/transliterated variant of a reference unit (same territory) |
| POSSIBLE_REORGANIZATION | 77 | new district or district created within/around the DS3 window (or absent from the MRCDSS reference) |
| POSSIBLE_SPLIT | 1 | a reference unit split into two units in current HMIS |
| UNCERTAIN | 7 | cannot be resolved from internal data - external verification required |

### Per-state counts of unmatched units

| State | Units (names) |
|---|---|
| Andhra Pradesh (14) | Anakapalli, Annamayya, Bapatla, Dr. B.R. Ambedkar Konaseema, Kakinada, Markapuram, Nandyal, Ntr, Palnadu, Parvathipuram Manyam, Polavaram, Sri Sathya Sai, Tirupati, Y.S.R. Kadapa |
| Arunachal Pradesh (7) | Bichom, Kamle, Keyi Panyor, Leparada, Lower Siang, Pakke Kessang, Shi Yomi |
| Assam (9) | Bajali, Biswanath, Charaideo, Hojai, Majuli, South Salmara Mancachar, Sribhumi, Tamulpur, West Karbi Anglong |
| Chhattisgarh (6) | Gaurela Pendra Marwahi, Khairagarh Chhuikhadan Gandai, Manendragarh Chirmiri Bharatpur Mcb, Mohla Manpur Ambagarh Chouki, Sakti, Sarangarh Bilaigarh |
| Delhi (3) | Central North, Old Delhi, Outer North |
| Goa (1) | Kushavati |
| Gujarat (4) | Ahmedabad, Dahod, Dangs, Vav-Tharad |
| Haryana (1) | Charkhi Dadri |
| Himachal Pradesh (1) | Lahaul And Spiti |
| Karnataka (5) | Bengaluru South, Chamarajanagar, Davanagere, Vijayanagar, Vijayanagara |
| Madhya Pradesh (1) | Niwari |
| Maharashtra (2) | Ahilyanagar, Mumbai Suburban |
| Manipur (7) | Jiribam, Kakching, Kamjong, Kangpokpi, Noney, Pherzawl, Tengnoupal |
| Meghalaya (1) | Eastern West Khasi Hills |
| Mizoram (3) | Hnahthial, Khawzawl, Saitual |
| Nagaland (5) | Chumoukedima, Niuland, Noklak, Shamator, Tseminyu |
| Odisha (4) | Angul, Balasore, Jajpur, Keonjhar |
| Puducherry (1) | Puducherry |
| Punjab (1) | Malerkotla |
| Rajasthan (17) | Anupgarh, Balotra, Beawar, Deeg, Didwana-Kuchaman, Dudu, Gangapurcity, Jaipur (Gramin), Jodhpur (Gramin), Kekri, Khairthal-Tijara, Kotputli-Behror, Neem Ka Thana, Phalodi, Salumbar, Sanchore, Shahpura |
| Sikkim (2) | Pakyong, Soreng |
| Tamil Nadu (9) | Chengalpattu, Kallakurichi, Kancheepuram, Mayiladuthurai, Ranipet, Tenkasi, Thoothukkudi, Tirupathur, Viluppuram |
| Uttarakhand (1) | Udham Singh Nagar |

## D. Name / alias cases (same territory, different string)

These are NOT new districts. The reference spelling and the recent-HMIS spelling cover the **same geographic unit**; the recent-HMIS spelling appears in a subset of DS3 years (2022-23 predominantly) while the reference spelling appears in the neighbouring years, and the per-state district count is unchanged.

| State | Reference_Spelling |
|---|---|
| Andhra Pradesh | Y.S.R. |
| Assam | Karimganj |
| Gujarat | Ahmadabad |
| Gujarat | Dohad |
| Gujarat | Dang |
| Haryana | Charki Dadri |
| Himachal Pradesh | Lahul And Spiti |
| Karnataka | Chamarajanagara |
| Karnataka | Davangere |
| Karnataka | Vijayanagar |
| Maharashtra | Ahmednagar |
| Odisha | Baleshwar |
| Odisha | Kendujhar |
| Odisha | Anugul |
| Odisha | Jajapur |
| Puducherry | Pondicherry |
| Tamil Nadu | Tuticorin |
| Tamil Nadu | Kanchipuram |
| Tamil Nadu | Villupuram |
| Uttarakhand | Udam Singh Nagar |

The following reference units matched their Dataset 3 counterpart only after normalisation (already in the 707, not in the 105): documented for transparency.

- 7 such unit(s): Chhattisgarh: Balrampur Ramanujganj; Uttar Pradesh: Barabanki; Uttar Pradesh: Kushi Nagar; Uttar Pradesh: Siddharth Nagar; Uttarakhand: Rudra Prayag; Uttarakhand: Uttar Kashi; West Bengal: Coochbehar

## E. What happened in the 2022-23 HMIS files

- 2022-23 lists **791** units, of which only **687** match the reference spelling set (20 reference units are spelled differently in 2022-23 and re-appear in their reference spelling in 2023-24).
- The 2022-23 files adopted variant spellings for several states (Haryana, Himachal, Gujarat, Odisha, Karnataka, TN, Maharashtra, Uttarakhand, AP, Assam, Puducherry) and additionally listed provisional/renaming units (Delhi 14 vs 11; `Bengaluru South` in place of `Ramanagara`; AP `Y.S.R. Kadapa`, `Markapuram`, `Polavaram`; Gujarat `Vav-Tharad`; Arunachal `Bichom`/`Keyi Panyor`).

### Reference units spelled differently / absent in 2022-23

| State | District |
|---|---|
| Andhra Pradesh | Y.S.R. |
| Assam | Karimganj |
| Gujarat | Ahmadabad |
| Gujarat | Dang |
| Gujarat | Dohad |
| Haryana | Charki Dadri |
| Himachal Pradesh | Lahul And Spiti |
| Karnataka | Chamarajanagara |
| Karnataka | Davangere |
| Karnataka | Ramanagara |
| Maharashtra | Ahmednagar |
| Odisha | Anugul |
| Odisha | Baleshwar |
| Odisha | Jajapur |
| Odisha | Kendujhar |
| Puducherry | Pondicherry |
| Tamil Nadu | Kanchipuram |
| Tamil Nadu | Tuticorin |
| Tamil Nadu | Villupuram |
| Uttarakhand | Udam Singh Nagar |

## F. Possible splits / merges

- **`Mumbai` (reference) -> `Mumbai` + `Mumbai Suburban` (DS3)**: POSSIBLE_SPLIT, name evidence only, external verification required. No reference unit was merged into another in Dataset 3; **no merge candidates** were found among the 105.

## G. Insufficient evidence / EXTERNAL_VERIFICATION_REQUIRED

**7** units cannot be resolved from internal data alone. They are single-year (2022-23-only) appearances or name-replacement anomalies that must be checked against external sources (notifications of district formation / HMIS release notes):

| State | Recent_HMIS_District | Why_Uncertain |
|---|---|---|
| Andhra Pradesh | Markapuram | Single-year (2022-23) AP unit; not present before or after; classified as UNCERTAIN -> EXTERNAL_VERIFICATION_REQUIRED. Markapuram observed in DS3 years 2022-2023 |
| Andhra Pradesh | Polavaram | Single-year (2022-23) AP unit; not present before or after; classified as UNCERTAIN -> EXTERNAL_VERIFICATION_REQUIRED. Polavaram observed in DS3 years 2022-2023 |
| Delhi | Central North | 2022-23-only Delhi unit (14 districts listed that year vs 11 otherwise); not present in any other DS3 year -> EXTERNAL_VERIFICATION_REQUIRED. Central North observed in DS3 years 2022-2023 |
| Delhi | Old Delhi | 2022-23-only Delhi unit (14 districts listed that year vs 11 otherwise); not present in any other DS3 year -> EXTERNAL_VERIFICATION_REQUIRED. Old Delhi observed in DS3 years 2022-2023 |
| Delhi | Outer North | 2022-23-only Delhi unit (14 districts listed that year vs 11 otherwise); not present in any other DS3 year -> EXTERNAL_VERIFICATION_REQUIRED. Outer North observed in DS3 years 2022-2023 |
| Gujarat | Vav-Tharad | 2022-23-only Gujarat unit; absent from 2023-24 file; classified as UNCERTAIN -> EXTERNAL_VERIFICATION_REQUIRED. Vav-Tharad observed in DS3 years 2022-2023 |
| Karnataka | Bengaluru South | 2022-23-only Karnataka unit; Ramanagara (in reference) is omitted from the same file, suggesting an HMIS 2022-23 labelling anomaly rather than a real district -> EXTERNAL_VERIFICATION_REQUIRED. Bengaluru South observed in DS3 years 2022-2023 (first data 2022-2023) |

Additionally, **all** `POSSIBLE_REORGANIZATION` / `POSSIBLE_SPLIT` rows carry `External_Verification_Required=YES` (see `district_reorganization_cases.csv`); their parent districts and formation dates were NOT assumed from internal data.

## H. Exact examples (rows with real values)

Representative rows showing the churn patterns. `NaN` = unavailable (empty cell in the source annual file), not zero.

| State | District | 2020-21 | 2021-22 | 2022-23 | 2023-24 | 2024-25 | pattern |
|---|---|---|---|---|---|---|---|
| Andhra Pradesh | Anakapalli | NaN | NaN | ANC_First_Trimester_Pct:89.43 | ANC_First_Trimester_Pct:89.29 | NaN | new in 2022; data from 2022-23, rows before are all-NaN |
| Andhra Pradesh | Markapuram | NaN | NaN | NaN | NaN | NaN | 2022-23 only, then gone - uncertain |
| Assam | Sribhumi | NaN | NaN | ANC_First_Trimester_Pct:93.26 | NaN | NaN | 2022-23 only; reference Karimganj in the other years - alias |
| Sikkim | Pakyong | NaN | NaN | NaN | NaN | NaN | all-NaN rows throughout (created 2021) |
| Tamil Nadu | Thoothukkudi | NaN | NaN | ANC_First_Trimester_Pct:98.18 | NaN | NaN | 2022-23 only; reference Tuticorin otherwise - alias |
| Karnataka | Bengaluru South | NaN | NaN | ANC_First_Trimester_Pct:90.58 | NaN | NaN | 2022-23 only, replaced Ramanagara that year - uncertain |
| Rajasthan | Balotra | NaN | NaN | NaN | NaN | NaN | all-NaN rows every year (created 2023) |

## I. Data quality observation: retroactive naming in HMIS annual files

- Annual files list the *current* district list, so newly created districts also appear (empty / all-`NaN` rows) in years **before** their creation: e.g. Rajasthan's 2023 districts appear in every 2020-21..2023-24 file but carry no data; AP's 2022 districts carry data only from 2022-23; Sikkim's 2021 districts are all-`NaN` throughout.
- Recommendation: treat all-`NaN` rows for a new district **before its first data year** as effectively 'district not in existence', i.e. do not count them as observations.

## J. Recommendation on a harmonised panel

- **Keep Dataset 3 at native HMIS district boundaries.** No merging, renaming or re-spelling has been applied to the dataset by this audit (see `district_mapping_candidates.csv` for the **proposal**).
- A conservative harmonised panel is defensible **only** if the analyst applies the `FORMAT_VARIANT` / `ALIAS_CANDIDATE` crosswalk at query time (map `Charkhi Dadri`->`Charki Dadri`, `Ahilyanagar`->`Ahmednagar`, etc.).
- Genuine new districts (`POSSIBLE_REORGANIZATION`) must remain **separate rows**; they exist only in the recent-HMIS era and cannot be back-filled into the 2008-2019 reference.
- The reference-era-gap units (MP `Niwari`, Manipur 2016, TN 2019) are candidates for adding to the reference at a later maintenance step - but that is an out-of-scope reference rebuild, not a Dataset 3 change.
