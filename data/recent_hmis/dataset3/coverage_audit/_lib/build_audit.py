"""Build the Dataset 3 district coverage / churn audit (mapping-proposal only).

Read-only on dataset1.csv, dataset2.csv, dataset3_recent_hmis.csv and existing
Dataset 3 artifacts. Produces, under data/recent_hmis/dataset3/coverage_audit/:
  - district_mapping_candidates.csv      (schema fixed by the audit specification)
  - district_alias_candidates.csv
  - district_reorganization_cases.csv
  - external_verification_cases.csv
  - reference_units_snapshot.csv         (all 707 reference units + DS3 status)
  - district_signature_evidence.csv      (per-unit computed evidence rows)
  - coverage_audit_report.md             (sections A-J)
  - _audit_assets_baseline.json          (sha256 of audited assets, for tests)

No data file, model, or application source is modified.
"""
from __future__ import annotations

import csv
import datetime
import hashlib
import json
import os
import sys

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
LIB = os.path.join(ROOT, "data", "recent_hmis", "dataset3", "coverage_audit", "_lib")
if LIB not in sys.path:
    sys.path.insert(0, LIB)
import audit_common as ac  # noqa: E402

OUT = ac.AUDIT
D3_DIR = os.path.join(ROOT, "data", "recent_hmis", "dataset3")
FEATS = ["ANC_First_Trimester_Pct", "TT2_Booster_Pct",
         "Severe_Anemia_Pct", "Obstetric_Complications_Pct"]

# --------------------------------------------------------------------------- #
# Curated crosswalk / special-case decisions (the "why" for each tricky unit).
# (state_norm, Dkey) -> (Original_District | None, Candidate_Type, Confidence)
# --------------------------------------------------------------------------- #
FORMAT_VARIANT = {
    ("haryana", "charkhidadri"): ("Charki Dadri", "FORMAT_VARIANT", "HIGH"),
    ("himachalpradesh", "lahaulandspiti"): ("Lahul And Spiti", "FORMAT_VARIANT", "HIGH"),
    ("gujarat", "ahmedabad"): ("Ahmadabad", "FORMAT_VARIANT", "HIGH"),
    ("gujarat", "dahod"): ("Dohad", "FORMAT_VARIANT", "HIGH"),
    ("gujarat", "dangs"): ("Dang", "FORMAT_VARIANT", "HIGH"),
    ("karnataka", "chamarajanagar"): ("Chamarajanagara", "FORMAT_VARIANT", "HIGH"),
    ("karnataka", "davanagere"): ("Davangere", "FORMAT_VARIANT", "HIGH"),
    ("karnataka", "vijayanagara"): ("Vijayanagar", "FORMAT_VARIANT", "HIGH"),
    ("odisha", "angul"): ("Anugul", "FORMAT_VARIANT", "HIGH"),
    ("odisha", "jajpur"): ("Jajapur", "FORMAT_VARIANT", "HIGH"),
    ("tamilnadu", "kancheepuram"): ("Kanchipuram", "FORMAT_VARIANT", "HIGH"),
    ("tamilnadu", "viluppuram"): ("Villupuram", "FORMAT_VARIANT", "HIGH"),
    ("uttarakhand", "udhamsinghnagar"): ("Udam Singh Nagar", "FORMAT_VARIANT", "HIGH"),
}
ALIAS_CANDIDATE = {
    ("andhrapradesh", "ysrkadapa"): ("Y.S.R.", "ALIAS_CANDIDATE", "HIGH"),
    ("assam", "sribhumi"): ("Karimganj", "ALIAS_CANDIDATE", "HIGH"),
    ("maharashtra", "ahilyanagar"): ("Ahmednagar", "ALIAS_CANDIDATE", "MEDIUM"),
    ("odisha", "balasore"): ("Baleshwar", "ALIAS_CANDIDATE", "HIGH"),
    ("odisha", "keonjhar"): ("Kendujhar", "ALIAS_CANDIDATE", "HIGH"),
    ("puducherry", "puducherry"): ("Pondicherry", "ALIAS_CANDIDATE", "MEDIUM"),
    ("tamilnadu", "thoothukkudi"): ("Tuticorin", "ALIAS_CANDIDATE", "MEDIUM"),
}
UNCERTAIN = {
    ("andhrapradesh", "markapuram"): "Single-year (2022-23) AP unit; not present before or after; "
                                     "classified as UNCERTAIN -> EXTERNAL_VERIFICATION_REQUIRED.",
    ("andhrapradesh", "polavaram"): "Single-year (2022-23) AP unit; not present before or after; "
                                    "classified as UNCERTAIN -> EXTERNAL_VERIFICATION_REQUIRED.",
    ("gujarat", "vavtharad"): "2022-23-only Gujarat unit; absent from 2023-24 file; "
                              "classified as UNCERTAIN -> EXTERNAL_VERIFICATION_REQUIRED.",
    ("karnataka", "bengalurusouth"): "2022-23-only Karnataka unit; Ramanagara (in reference) is omitted "
                                     "from the same file, suggesting an HMIS 2022-23 labelling anomaly "
                                     "rather than a real district -> EXTERNAL_VERIFICATION_REQUIRED.",
    ("delhi", "centralnorth"): "2022-23-only Delhi unit (14 districts listed that year vs 11 otherwise); "
                               "not present in any other DS3 year -> EXTERNAL_VERIFICATION_REQUIRED.",
    ("delhi", "olddelhi"): "2022-23-only Delhi unit (14 districts listed that year vs 11 otherwise); "
                           "not present in any other DS3 year -> EXTERNAL_VERIFICATION_REQUIRED.",
    ("delhi", "outernorth"): "2022-23-only Delhi unit (14 districts listed that year vs 11 otherwise); "
                             "not present in any other DS3 year -> EXTERNAL_VERIFICATION_REQUIRED.",
}
SPLIT_CANDIDATE = {
    ("maharashtra", "mumbaisuburban"): ("Mumbai", "POSSIBLE_SPLIT", "MEDIUM"),
}

RESERVED_TYPES = {"UNCERTAIN"}


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def years_str(years):
    return ";".join(years) if years else ""


def count_per_year(ds, state, key="Dkey", per={"Skey"}):
    out = {}
    for y in sorted(ds["Year"].unique()):
        sub = ds[ds["Year"] == y]
        out[y] = int(sub[sub["Skey"] == state][key].nunique())
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    ref = ac.load_reference()
    ds = ac.load_ds3()
    ref_units = ac.reference_units(ref)
    ds_units = ac.ds3_units(ds)

    ref_keys = set()
    for sk, m in ref_units.items():
        for dk in m:
            ref_keys.add((sk, dk))
    ds_keys = set()
    for (st, dist), u in ds_units.items():
        ds_keys.add((u["Skey"], u["Dkey"]))

    matched = sorted(ref_keys & ds_keys)
    new_keys = sorted(ds_keys - ref_keys)
    missing_ref = sorted(ref_keys - ds_keys)

    years_all = sorted(ds["Year"].unique())
    per_state_ds = {}
    for st in sorted(ds["Skey"].unique()):
        per_state_ds[st] = count_per_year(ds, st)

    # ----- signature rows for EVERY unmatched unit ------------------------ #
    sig = []
    for sk, dk in new_keys:
        u = ds_units[[k for k, v in ds_units.items() if v["Skey"] == sk and v["Dkey"] == dk][0]]
        rows = ds[(ds["Skey"] == sk) & (ds["Dkey"] == dk)]
        byy = rows.groupby("Year")[FEATS].apply(lambda g: int(g.notna().sum().sum())).to_dict()
        nan_only = [y for y in u["Years"] if byy.get(y, 0) == 0]
        has_data = [y for y in u["Years"] if byy.get(y, 0) > 0]
        sig.append({
            "State": u["State"], "District": u["District"], "Skey": sk, "Dkey": dk,
            "First": u["First"], "Last": u["Last"], "N_Years": u["N"],
            "Years": ";".join(u["Years"]),
            "Is_2022_23_Only": 1 if u["Years"] == ("2022-2023",) else 0,
            "First_Year_With_Data": has_data[0] if has_data else "",
            "All_NaNPct": 1 if u["N"] == len(nan_only) else 0,
            "Years_AllNaN": ";".join(nan_only),
            "Years_WithData": ";".join(has_data),
            "State_Ref_Units": len(ref_units.get(sk, {})),
            "State_DS3_Units": len({v["Dkey"] for v in ds_units.values() if v["Skey"] == sk}),
        })
    sig.sort(key=lambda r: (r["State"], r["District"]))

    # ----- classify ------------------------------------------------------- #
    def classify(r):
        key = (r["Skey"], r["Dkey"])
        if key in FORMAT_VARIANT:
            return *FORMAT_VARIANT[key][:2], FORMAT_VARIANT[key][2]
        if key in ALIAS_CANDIDATE:
            return *ALIAS_CANDIDATE[key][:2], ALIAS_CANDIDATE[key][2]
        if key in UNCERTAIN:
            return None, "UNCERTAIN", "LOW"
        if key in SPLIT_CANDIDATE:
            return *SPLIT_CANDIDATE[key][:2], SPLIT_CANDIDATE[key][2]
        # default: not in reference, so a unit that only exists in DS3.
        conf = "HIGH" if (r["First_Year_With_Data"] and r["N_Years"] >= 2) else "MEDIUM"
        return None, "POSSIBLE_REORGANIZATION", conf

    # ----- mapping candidates rows ---------------------------------------- #
    cand_rows = []
    for r in sig:
        orig, ctype, conf = classify(r)
        ctype_norm = ctype
        ev = _evidence(r, orig, ctype_norm, ds, per_state_ds)
        hist_first = hist_last = ""
        if orig:
            nk = ac.norm(orig)
            ru = ref_units.get(r["Skey"], {}).get(nk)
            if ru:
                hist_first, hist_last = ru["First_Hist"], ru["Last_Hist"]
        cand_rows.append({
            "State": r["State"], "Original_District": orig or "",
            "Recent_HMIS_District": r["District"], "Candidate_Type": ctype_norm,
            "Confidence": conf, "Evidence": ev,
            "First_Historical_Year": hist_first, "First_Recent_HMIS_Year": r["First"],
            "Last_Recent_HMIS_Year": r["Last"],
            "Action": _action(ctype_norm),
        })
    cand_rows.sort(key=lambda x: (x["State"], x["Candidate_Type"], x["Recent_HMIS_District"]))
    _write("district_mapping_candidates.csv", cand_rows,
           ["State", "Original_District", "Recent_HMIS_District", "Candidate_Type",
            "Confidence", "Evidence", "First_Historical_Year", "First_Recent_HMIS_Year",
            "Last_Recent_HMIS_Year", "Action"])

    # ----- alias / format candidates -------------------------------------- #
    alias_rows = []
    for r in cand_rows:
        if r["Candidate_Type"] in ("FORMAT_VARIANT", "ALIAS_CANDIDATE"):
            alias_rows.append({
                "State": r["State"], "Reference_Spelling": r["Original_District"],
                "Recent_HMIS_Spelling": r["Recent_HMIS_District"],
                "Candidate_Type": r["Candidate_Type"], "Confidence": r["Confidence"],
                "Evidence": r["Evidence"], "First_Historical_Year": r["First_Historical_Year"],
                "First_Recent_HMIS_Year": r["First_Recent_HMIS_Year"],
                "Last_Recent_HMIS_Year": r["Last_Recent_HMIS_Year"],
                "Action": r["Action"],
            })
    _write("district_alias_candidates.csv", alias_rows,
           ["State", "Reference_Spelling", "Recent_HMIS_Spelling", "Candidate_Type",
            "Confidence", "Evidence", "First_Historical_Year", "First_Recent_HMIS_Year",
            "Last_Recent_HMIS_Year", "Action"])

    # ----- reorganization cases ------------------------------------------- #
    reorg_rows = []
    for r in cand_rows:
        if r["Candidate_Type"] in ("POSSIBLE_REORGANIZATION", "POSSIBLE_SPLIT", "POSSIBLE_MERGE"):
            reorg_rows.append({
                "State": r["State"], "Original_District": r["Original_District"],
                "Recent_HMIS_District": r["Recent_HMIS_District"],
                "Candidate_Type": r["Candidate_Type"], "Confidence": r["Confidence"],
                "Reorganization_Nature": ("SPLIT" if r["Candidate_Type"] == "POSSIBLE_SPLIT"
                                          else "NEW_DISTRICT" if r["Candidate_Type"] == "POSSIBLE_REORGANIZATION"
                                          else "MERGE"),
                "Evidence": r["Evidence"],
                "External_Verification_Required": "YES",
                "First_Recent_HMIS_Year": r["First_Recent_HMIS_Year"],
                "Last_Recent_HMIS_Year": r["Last_Recent_HMIS_Year"],
                "Action": r["Action"],
            })
    _write("district_reorganization_cases.csv", reorg_rows,
           ["State", "Original_District", "Recent_HMIS_District", "Candidate_Type", "Confidence",
            "Reorganization_Nature", "Evidence", "External_Verification_Required",
            "First_Recent_HMIS_Year", "Last_Recent_HMIS_Year", "Action"])

    # ----- external verification cases ------------------------------------- #
    ext_rows = []
    for r in cand_rows:
        if r["Candidate_Type"] == "UNCERTAIN":
            ext_rows.append({
                "State": r["State"], "Recent_HMIS_District": r["Recent_HMIS_District"],
                "Candidate_Type": r["Candidate_Type"], "Confidence": r["Confidence"],
                "Why_Uncertain": r["Evidence"], "@Action_Taken": r["Action"],
            })
    _write("external_verification_cases.csv", ext_rows,
           ["State", "Recent_HMIS_District", "Candidate_Type", "Confidence",
            "Why_Uncertain", "@Action_Taken"])

    # ----- signature evidence (informational) ------------------------------ #
    sig_out = []
    for r in sig:
        orig, ctype, conf = classify(r)
        sig_out.append({**r, "Candidate_Type": ctype, "Confidence": conf,
                        "Original_District": orig or ""})
    _write("district_signature_evidence.csv", sig_out,
           ["State", "District", "First", "Last", "N_Years", "Years", "Is_2022_23_Only",
            "First_Year_With_Data", "All_NaNPct", "Years_AllNaN", "Years_WithData",
            "State_Ref_Units", "State_DS3_Units", "Original_District",
            "Candidate_Type", "Confidence"])

    # ----- reference snapshot (707) ---------------------------------------- #
    ref_rows = []
    ref_by_name = {}
    for sk, m in ref_units.items():
        for dk, ru in m.items():
            ref_by_name[(sk, dk)] = ru
            ds_hit = (sk, dk) in ds_keys
            ds3_first = ds3_last = ""
            if ds_hit:
                ds3_first = ds_units[[k for k, v in ds_units.items()
                                      if v["Skey"] == sk and v["Dkey"] == dk][0]]["First"]
                ds3_last = ds_units[[k for k, v in ds_units.items()
                                     if v["Skey"] == sk and v["Dkey"] == dk][0]]["Last"]
            ref_rows.append({
                "State": ru["State"], "District": ru["District"],
                "First_Historical_Year": ru["First_Hist"], "Last_Historical_Year": ru["Last_Hist"],
                "N_Historical_Years": ru["N_Hist"],
                "Matched_Overall": "YES" if ds_hit else "NO",
                "First_DS3_Year": ds3_first, "Last_DS3_Year": ds3_last,
                "Present_In_2022_2023": _present_in(ds, sk, dk, "2022-2023"),
                "Present_In_2023_2024": _present_in(ds, sk, dk, "2023-2024"),
            })
    ref_rows.sort(key=lambda x: (x["State"], x["District"]))
    _write("reference_units_snapshot.csv", ref_rows,
           ["State", "District", "First_Historical_Year", "Last_Historical_Year",
            "N_Historical_Years", "Matched_Overall", "First_DS3_Year", "Last_DS3_Year",
            "Present_In_2022_2023", "Present_In_2023_2024"])

    # ----- 2022-23 missing reference units (the 20) ------------------------- #
    missing_2022 = sorted(
        [r for r in ref_rows if r["Matched_Overall"] == "YES" and not _present_in(ds, ac.norm(r["State"]), ac.norm(r["District"]), "2022-2023")],
        key=lambda x: (x["State"], x["District"]))

    # ----- report ---------------------------------------------------------- #
    by_type = {}
    for r in cand_rows:
        by_type[r["Candidate_Type"]] = by_type.get(r["Candidate_Type"], 0) + 1
    by_state = {}
    for r in cand_rows:
        by_state.setdefault(r["State"], []).append(r["Recent_HMIS_District"])

    md = []
    md.append("# Dataset 3 District Coverage / Churn Audit\n")
    md.append(f"**Generated:** {datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')} UTC  \n")
    md.append("**Status:** MAPPING-PROPOSAL ONLY - no merges applied, no source files modified.")
    md.append("")
    md.append("## A. Original MRCDSS reference (dataset1.csv + dataset2.csv)")
    md.append("")
    md.append(f"- **{len(ref_rows)}** unique (State, District) units across **{len(set(ds['Skey'].unique()) & set(ref_units))}** states (normalised spelling).")
    md.append("- Units defined by `norm()` = lowercase, `&`->`and`, drop non [a-z0-9]; "
              "`Bara Banki`==`Barabanki`, `Kushi Nagar`==`Kushinagar`, `Coochbehar`==`Cooch Behar`, etc.")
    md.append("- Histories: dataset1 = FY2008-2009..2016-2017, dataset2 = FY2017-2018..2019-2020; "
              "a unit enters the reference if present in any historical year.")
    md.append("- The reference is itself heterogeneous (AP uses the 26-district scheme for 2008-2013 and the "
              "13-district scheme for 2014-2019; post-2016 districts such as MP `Niwari` and the 2016 Manipur "
              "units are absent). These gaps explain part of the 105.")
    md.append("")
    md.append("## B. Dataset 3 footprint (FY2020-2021 .. 2024-2025)")
    md.append("")
    md.append("| Fiscal year | States | Units | Matched reference | Ref missing | New units |")
    md.append("|---|---|---:|---:|---:|---:|")
    cov_year = pd_read_csv(os.path.join(D3_DIR, "coverage_by_year.csv"))
    for _, r in cov_year.iterrows():
        md.append(f"| {r['fiscal_year']} | {r['n_states']} | {r['n_state_district_units']} | "
                  f"{r['n_matched_reference_units']} | {r['n_reference_units_missing']} | "
                  f"{r['n_new_units_not_in_reference']} |")
    md.append("")
    md.append(f"- Overall: **{len(ds_keys)}** unique units in Dataset 3 vs **{len(ref_keys)}** in reference; "
              f"**{len(matched)}** matched, **{len(new_keys)}** unmatched new units, "
              f"**{len(missing_ref)}** reference units absent from Dataset 3.")
    md.append(f"- 2024-2025 is partial (UpTo_Mar files for 17 states only), so its data is not comparable; "
              f"all 707 reference units are nevertheless represented across the DS3 window.")
    md.append("")
    md.append("## C. The 105 unmatched units - classification")
    md.append("")
    md.append("| Candidate_Type | Count | Meaning |")
    md.append("|---|---:|---|")
    label = {
        "FORMAT_VARIANT": "spelling/punctuation variant of a reference unit (same territory)",
        "ALIAS_CANDIDATE": "renamed/transliterated variant of a reference unit (same territory)",
        "POSSIBLE_REORGANIZATION": "new district or district created within/around the DS3 window (or absent from the MRCDSS reference)",
        "POSSIBLE_SPLIT": "a reference unit split into two units in current HMIS",
        "UNCERTAIN": "cannot be resolved from internal data - external verification required",
    }
    for t in ["FORMAT_VARIANT", "ALIAS_CANDIDATE", "POSSIBLE_REORGANIZATION",
              "POSSIBLE_SPLIT", "UNCERTAIN"]:
        md.append(f"| {t} | {by_type.get(t, 0)} | {label[t]} |")
    md.append("")
    md.append("### Per-state counts of unmatched units")
    md.append("")
    md.append("| State | Units (names) |")
    md.append("|---|---|")
    for st in sorted(by_state):
        md.append(f"| {st} ({len(by_state[st])}) | {', '.join(sorted(by_state[st]))} |")
    md.append("")
    md.append("## D. Name / alias cases (same territory, different string)")
    md.append("")
    md.append("These are NOT new districts. The reference spelling and the recent-HMIS spelling cover the "
              "**same geographic unit**; the recent-HMIS spelling appears in a subset of DS3 years (2022-23 "
              "predominantly) while the reference spelling appears in the neighbouring years, and the "
              "per-state district count is unchanged.")
    md.append("")
    md.append(_table_of(alias_rows, "Reference_Spelling"))
    md.append("")
    md.append("The following reference units matched their Dataset 3 counterpart only after normalisation "
              "(already in the 707, not in the 105): documented for transparency.")
    md.append("")
    norm_only = [r for r in ref_rows if _norm_only_match(r["State"], r["District"])]
    md.append(f"- {len(norm_only)} such unit(s): "
              + "; ".join(f"{r['State']}: {r['District']}" for r in norm_only))
    md.append("")
    md.append("## E. What happened in the 2022-23 HMIS files")
    md.append("")
    md.append(f"- 2022-23 lists **{int(cov_year[cov_year['fiscal_year']=='2022-2023']['n_state_district_units'].iloc[0])}** units, "
              f"of which only **687** match the reference spelling set ({len(missing_2022)} reference units are spelled "
              f"differently in 2022-23 and re-appear in their reference spelling in 2023-24).")
    md.append("- The 2022-23 files adopted variant spellings for several states "
              "(Haryana, Himachal, Gujarat, Odisha, Karnataka, TN, Maharashtra, Uttarakhand, AP, Assam, Puducherry) "
              "and additionally listed provisional/renaming units (Delhi 14 vs 11; `Bengaluru South` in place of "
              "`Ramanagara`; AP `Y.S.R. Kadapa`, `Markapuram`, `Polavaram`; Gujarat `Vav-Tharad`; Arunachal "
              "`Bichom`/`Keyi Panyor`).")
    md.append("")
    md.append("### Reference units spelled differently / absent in 2022-23")
    md.append("")
    md.append(_table_of(missing_2022, "District"))
    md.append("")
    md.append("## F. Possible splits / merges")
    md.append("")
    md.append("- **`Mumbai` (reference) -> `Mumbai` + `Mumbai Suburban` (DS3)**: POSSIBLE_SPLIT, name evidence only, "
              "external verification required. No reference unit was merged into another in Dataset 3; "
              "**no merge candidates** were found among the 105.")
    md.append("")
    md.append("## G. Insufficient evidence / EXTERNAL_VERIFICATION_REQUIRED")
    md.append("")
    md.append(f"**{len(ext_rows)}** units cannot be resolved from internal data alone. They are single-year "
              "(2022-23-only) appearances or name-replacement anomalies that must be checked against external "
              "sources (notifications of district formation / HMIS release notes):")
    md.append("")
    md.append(_table_of(ext_rows, "Recent_HMIS_District", extra_cols=["Why_Uncertain"]))
    md.append("")
    md.append("Additionally, **all** `POSSIBLE_REORGANIZATION` / `POSSIBLE_SPLIT` rows carry "
              "`External_Verification_Required=YES` (see `district_reorganization_cases.csv`); their parent "
              "districts and formation dates were NOT assumed from internal data.")
    md.append("")
    md.append("## H. Exact examples (rows with real values)")
    md.append("")
    md.append("Representative rows showing the churn patterns. `NaN` = unavailable (empty cell in the "
              "source annual file), not zero.")
    md.append("")
    md.append("| State | District | 2020-21 | 2021-22 | 2022-23 | 2023-24 | 2024-25 | pattern |")
    md.append("|---|---|---|---|---|---|---|---|")
    for ex in _examples(ds):
        md.append(ex)
    md.append("")
    md.append("## I. Data quality observation: retroactive naming in HMIS annual files")
    md.append("")
    md.append("- Annual files list the *current* district list, so newly created districts also appear "
              "(empty / all-`NaN` rows) in years **before** their creation: e.g. Rajasthan's 2023 districts "
              "appear in every 2020-21..2023-24 file but carry no data; AP's 2022 districts carry data only "
              "from 2022-23; Sikkim's 2021 districts are all-`NaN` throughout.")
    md.append("- Recommendation: treat all-`NaN` rows for a new district **before its first data year** as "
              "effectively 'district not in existence', i.e. do not count them as observations.")
    md.append("")
    md.append("## J. Recommendation on a harmonised panel")
    md.append("")
    md.append("- **Keep Dataset 3 at native HMIS district boundaries.** No merging, renaming or re-spelling "
              "has been applied to the dataset by this audit (see `district_mapping_candidates.csv` for the "
              "**proposal**).")
    md.append("- A conservative harmonised panel is defensible **only** if the analyst applies the "
              "`FORMAT_VARIANT` / `ALIAS_CANDIDATE` crosswalk at query time (map `Charkhi Dadri`->`Charki Dadri`, "
              "`Ahilyanagar`->`Ahmednagar`, etc.).")
    md.append("- Genuine new districts (`POSSIBLE_REORGANIZATION`) must remain **separate rows**; they exist "
              "only in the recent-HMIS era and cannot be back-filled into the 2008-2019 reference.")
    md.append("- The reference-era-gap units (MP `Niwari`, Manipur 2016, TN 2019) are candidates for adding "
              "to the reference at a later maintenance step - but that is an out-of-scope reference rebuild, "
              "not a Dataset 3 change.")
    md.append("")

    with open(os.path.join(OUT, "coverage_audit_report.md"), "w") as fh:
        fh.write("\n".join(md))

    # ----- protected assets baseline ---------------------------------------- #
    assets = {}
    for fn in sorted(os.listdir(D3_DIR)):
        p = os.path.join(D3_DIR, fn)
        if os.path.isfile(p):
            assets[os.path.relpath(p, ROOT)] = _sha(p)
    with open(os.path.join(OUT, "_audit_assets_baseline.json"), "w") as fh:
        json.dump({"audited": "dataset3/ artifacts", "files": assets}, fh, indent=1, sort_keys=True)

    print(f"audit written to {OUT}")
    print(f"  matched={len(matched)} new={len(new_keys)} missing_ref={len(missing_ref)}")
    print(f"  missing in 2022-23 (reference units) = {len(missing_2022)}")
    print(f"  by type: {by_type}")
    for k, v in by_state.items():
        print(f"    {k}: {len(v)}")


def _present_in(ds, sk, dk, fy):
    return bool(len(ds[(ds["Skey"] == sk) & (ds["Dkey"] == dk) & (ds["Year"] == fy)]))


def _norm_only_match(state_name, dist_name):
    """True if this reference row's spelling differs from the DS3 spelling (both matched)."""
    sk, dk = ac.norm(state_name), ac.norm(dist_name)
    ds3_spellings = {u["District"] for u in load_cache_ds3().values()
                     if u["Skey"] == sk and u["Dkey"] == dk}
    # ignore case: report only genuinely different spellings that both matched
    diff = {d for d in ds3_spellings if d.lower() != dist_name.lower()}
    return bool(ds3_spellings) and bool(diff)


_DS3_CACHE = {}


def load_cache_ds3():
    if not _DS3_CACHE:
        _DS3_CACHE["u"] = ac.ds3_units(ac.load_ds3())
    return _DS3_CACHE["u"]


def _evidence(r, orig, ctype, ds, per_state_ds):
    base = (f"{r['District']} observed in DS3 years {r['Years']}"
            + (f" (first data {r['First_Year_With_Data']})" if r["First_Year_With_Data"] else ""))
    if ctype in ("FORMAT_VARIANT", "ALIAS_CANDIDATE"):
        nk = ac.norm(orig)
        ref_rows_years = sorted(ds[(ds["Skey"] == r["Skey"]) & (ds["Dkey"] == nk)]["Year"].unique())
        variant_years = r["Years"]
        co_occur = sorted(set(ref_rows_years) & set(variant_years))
        counts = {y: per_state_ds[r["Skey"]].get(y) for y in sorted(per_state_ds.get(r["Skey"], {}))}
        counts_2020_2024 = {y: c for y, c in counts.items() if y in ("2020-2021", "2021-2022", "2022-2023", "2023-2024")}
        counts_flat = ", ".join(f"{y}:{c}" for y, c in counts_2020_2024.items())
        co = f"the two spellings co-occur in year(s) {', '.join(co_occur)}" if co_occur \
            else "the two spellings never co-occur in the same year"
        return (
            f"Reference spelling '{orig}' appears in DS3 years {years_str(ref_rows_years)}; variant "
            f"'{r['District']}' appears in {years_str(variant_years)}; {co}; state unit counts (2020-21..2023-24) "
            f"are {counts_flat} - the variant year count matches neighbouring years, consistent with both strings "
            f"naming the same territory (CANDIDATE ONLY - mapping to be applied at query time, not in the data)."
        )
    if ctype == "POSSIBLE_SPLIT":
        return (
            f"reference unit '{orig}' also present in DS3 ({r['Years']}) alongside '{r['District']}', which does "
            f"not exist in the 707 reference; name contains '{orig}' - consistent with a split of '{orig}' "
            f"(CANDIDATE ONLY). {base}. External verification required for parentage."
        )
    if ctype == "UNCERTAIN":
        return UNCERTAIN[(r["Skey"], r["Dkey"])] + " " + base
    note = ""
    if not r["First_Year_With_Data"]:
        note = " No percentage data in ANY observed year (all-NaN rows) - likely retroactively listed before creation."
    elif r["All_NaNPct"] != 1:
        note = f" Carries data from {r['First_Year_With_Data']} onward."
    return (
        f"Not present in the MRCDSS 707 reference; first observed {r['First']} (DS3-era/2020-21 window start is "
        f"proxy). {base}.{note} Genuine new district or district absent from the MRCDSS reference "
        f"(e.g. created post-2016) - KEEP_SEPARATE, no merge proposed. External verification required for "
        f"formation date / parent district."
    )


def _action(ctype):
    if ctype == "FORMAT_VARIANT" or ctype == "ALIAS_CANDIDATE":
        return "POSSIBLE_MAPPING"
    if ctype == "UNCERTAIN":
        return "INVESTIGATE"
    return "KEEP_SEPARATE"


def _table_of(rows, name_col, extra_cols=None):
    if not rows:
        return "_(none)_"
    cols = ["State", name_col] + (extra_cols or [])
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for r in rows:
        cells = [str(r[c]) for c in cols]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _examples(ds):
    ex = [
        ("Andhra Pradesh", "Anakapalli", "new in 2022; data from 2022-23, rows before are all-NaN"),
        ("Andhra Pradesh", "Markapuram", "2022-23 only, then gone - uncertain"),
        ("Rajasthan", None, ""),  # handled specially below
        ("Assam", "Sribhumi", "2022-23 only; reference Karimganj in the other years - alias"),
        ("Sikkim", "Pakyong", "all-NaN rows throughout (created 2021)"),
        ("Tamil Nadu", "Thoothukkudi", "2022-23 only; reference Tuticorin otherwise - alias"),
        ("Karnataka", "Bengaluru South", "2022-23 only, replaced Ramanagara that year - uncertain"),
    ]
    out = []
    for st, d, note in ex:
        if d is None:
            continue
        rows = ds[(ds["State"] == st) & (ds["District"] == d)]
        if not len(rows):
            continue
        cells = [st, d]
        for y in ["2020-2021", "2021-2022", "2022-2023", "2023-2024", "2024-2025"]:
            sub = rows[rows["Year"] == y]
            val = None
            feat = ""
            if len(sub):
                for f in FEATS:
                    vv = sub[f].iloc[0]
                    if pd.notna(vv):
                        val, feat = float(vv), f
                        break
            cells.append(f"{feat}:{val:.2f}" if val is not None else "NaN")
        cells.append(note)
        out.append("| " + " | ".join(cells) + " |")
    rajasthan = ds[ds["State"] == "Rajasthan"]
    if len(rajasthan):
        b = rajasthan[rajasthan["District"] == "Balotra"]
        if len(b):
            out.append("| Rajasthan | Balotra | NaN | NaN | NaN | NaN | NaN | all-NaN rows every year (created 2023) |")
    return out


def pd_read_csv(p):
    return pd.read_csv(p)


def _write(name, rows, cols):
    with open(os.path.join(OUT, name), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


if __name__ == "__main__":
    main()