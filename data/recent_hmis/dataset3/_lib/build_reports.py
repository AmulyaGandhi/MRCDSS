"""Generate Dataset 3 analytics artifacts (coverage, quality, metadata, reports).

Reads the built Dataset 3 CSVs plus the legacy reference coverage (dataset1.csv,
dataset2.csv) and writes the remaining dataset3/ outputs. Read-only on all inputs.
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import datetime

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
LIB = os.path.join(ROOT, "data", "recent_hmis", "dataset3", "_lib")
if LIB not in sys.path:
    sys.path.insert(0, LIB)
import build_dataset3 as bd

OUT = bd.OUT
D3 = os.path.join(OUT, "dataset3_recent_hmis.csv")
FLAGS = os.path.join(OUT, "percent_invalid_flags.csv")
COUNTS = os.path.join(OUT, "indicator_counts.csv")
SRCMAP = os.path.join(OUT, "source_file_mapping.csv")

FEATS = list(bd.FEATURES)


def norm(key):
    # alias-normalise: fold case, '&'->'and', drop spaces/punctuation so that
    # e.g. 'Bara Banki'=='-barabanki', 'Kushinagar'=='Kushi Nagar',
    # 'Coochbehar'=='Cooch Behar', 'The Dadra And Nagar...'==local spelling.
    s = re.sub(r"[&]", "and", (key or "").lower())
    return re.sub(r"[^a-z0-9]", "", s)


def load_reference():
    d1 = pd.read_csv(os.path.join(ROOT, "dataset1.csv"))
    d2 = pd.read_csv(os.path.join(ROOT, "dataset2.csv"))
    units = set()
    states = set()
    for d in (d1, d2):
        for _, r in d.iterrows():
            units.add((norm(r["State"]), norm(r["District"])))
            states.add(norm(r["State"]))
    return states, units


def main():
    df = pd.read_csv(D3, na_values=[""], keep_default_na=True)
    flags = pd.read_csv(FLAGS)
    counts = pd.read_csv(COUNTS)
    srcmap = pd.read_csv(SRCMAP)
    ref_states, ref_units = load_reference()

    df["Skey"] = df.apply(lambda r: (norm(r["State"]), norm(r["District"])), axis=1)
    df["_n"] = 1

    YPK = lambda s: s  # noqa
    years = sorted(df["Year"].unique())

    # ---------------- coverage by year ----------------
    cov_year = []
    for y in years:
        sub = df[df["Year"] == y]
        units = set(zip(sub["State"].map(norm), sub["District"].map(norm)))
        matched = units & ref_units
        cov_year.append({
            "fiscal_year": y,
            "n_states": sub["State"].nunique(),
            "n_state_district_units": len(units),
            "n_matched_reference_units": len(matched),
            "n_reference_units_missing": len(ref_units - units),
            "n_new_units_not_in_reference": len(units - ref_units),
            "note": "" if y != "2024-2025" else "partial - UpTo_Mar files only for 17 states",
        })
    with open(os.path.join(OUT, "coverage_by_year.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(cov_year[0].keys())); w.writeheader(); w.writerows(cov_year)

    # ------------- coverage by state -------------
    cov_state = []
    for st, g in df.groupby("State"):
        byyear = g.groupby("Year")["District"].count().to_dict()
        allunits = set(zip(g["State"].map(norm), g["District"].map(norm)))
        cov_state.append({
            "state": st,
            "n_years_present": int(g["Year"].nunique()),
            "years_present": ";".join(years),
            "n_district_year_observations": int(len(g)),
            "n_unique_district_units": int(g["District"].nunique()),
            "units_per_year": "|".join(f"{y}:{byyear.get(y,0)}" for y in years),
        })
    cov_state.sort(key=lambda r: (r["n_years_present"], -r["n_district_year_observations"]), reverse=True)
    with open(os.path.join(OUT, "coverage_by_state.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(cov_state[0].keys())); w.writeheader(); w.writerows(cov_state)

    # ---------------- reference comparison lists ----------------
    all_units = set(df["Skey"]) 
    match_rows, new_rows = [], []
    for u in sorted(ref_units - all_units):
        match_rows.append({"state": u[0], "district": u[1], "in_dataset3": "no"})
    for u in sorted(all_units - ref_units):
        new_rows.append({"state": u[0], "district": u[1], "in_reference_707": "no"})
    with open(os.path.join(OUT, "coverage_reference_missing_units.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["state", "district", "in_dataset3"]); w.writeheader(); w.writerows(match_rows)
    with open(os.path.join(OUT, "coverage_new_units_not_in_707.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["state", "district", "in_reference_707"]); w.writeheader(); w.writerows(new_rows)

    # ---------------- district churn (year pairs) ----------------
    churn = []
    for a, b in zip(years, years[1:]):
        ua = set(zip(df[df.Year == a]["State"].map(norm), df[df.Year == a]["District"].map(norm)))
        ub = set(zip(df[df.Year == b]["State"].map(norm), df[df.Year == b]["District"].map(norm)))
        churn.append({"year_pair": f"{a}->{b}", "units_appearing_in_later": len(ub - ua),
                      "units_disappeared": len(ua - ub)})
    with open(os.path.join(OUT, "district_churn.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["year_pair", "units_appearing_in_later", "units_disappeared"])
        w.writeheader(); w.writerows(churn)

    # ---------------- missingness & invalid per feature ----------------
    miss = []
    for f in FEATS:
        for y in years:
            sub = df[df["Year"] == y]
            nv = int(sub[f].notna().sum())
            miss.append({"feature": f, "fiscal_year": y, "n_total": len(sub),
                         "n_valid": nv, "n_missing": int(len(sub) - nv),
                         "missing_pct": round((1 - nv / len(sub)) * 100, 2) if len(sub) else None})
    json.dump(miss, open(os.path.join(OUT, "_missingness.json"), "w"), indent=1)

    # invalid flags summary
    inv = {}
    for f in FEATS:
        bad = df[df[f].notna() & ((df[f] < 0) | (df[f] > 100))]
        inv[f] = {"invalid_lt_0": int((bad[f] < 0).sum()), "invalid_gt_100": int((bad[f] > 100).sum()),
                  "invalid_gt_100_max": round(float(bad[f].max()), 4) if len(bad) else None}
    json.dump({"invalid_per_feature": inv,
               "flags_file_rows": int(len(flags))},
              open(os.path.join(OUT, "_invalid_summary.json"), "w"), indent=1)

    # zero denominators
    zd = {}
    for f in FEATS:
        zd[f] = int(counts[f"{f}_denominator"].fillna(-1).eq(0).sum())
    json.dump(zd, open(os.path.join(OUT, "_zero_denominators.json"), "w"), indent=1)

    # duplicates
    dups = int(df.duplicated(["State", "District", "Year"]).sum())

    # ---------------- feature_definitions.csv ----------------
    defrows = []
    for f, cfg in bd.FEATURES.items():
        defrows.append({
            "Feature": f,
            "Formula": cfg["description"],
            "Numerator HMIS Items": "+".join(cfg["num_codes"]),
            "Denominator HMIS Items": "+".join(cfg["den_codes"]),
            "Years Available": (", ".join(sorted(cfg["years"])) if cfg["years"] else "2020-2021 .. 2024-2025"),
            "Comparator": "recent-HMIS indicator (not comparable to legacy 2008-2019 feature) "
                          if f == "Severe_Anemia_Pct" else "reconstructable",
            "Caveats": _caveat(f),
        })
    with open(os.path.join(OUT, "feature_definitions.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(defrows[0].keys())); w.writeheader(); w.writerows(defrows)

    # ---------------- metadata json ----------------
    meta = {
        "dataset": "dataset3_recent_hmis",
        "purpose": "Standalone district-year analytical dataset of recent-HMIS maternal indicators "
                   "reconstructed from cumulative annual HMIS raw files (district Total columns).",
        "granularity": "State + District + Fiscal Year",
        "years": years,
        "source": "NHSRC HMIS portal cumulative annual releases (B.Cummulative UpTo_Mar files); "
                  "2024-2025 only where UpTo_Mar files were acquired",
        "year_selection": "annual cumulative UpTo_Mar file per state; partial cumulative months (2024-25) excluded",
        "primary_columns": bd.PRIMARY_COLS,
        "district_value": "district Total column (Total = Public + Private = Urban + Rural; state = sum of districts)",
        "features": {f: {"formula": cfg["description"], "years": sorted(cfg["years"]) if cfg["years"] else "all"}
                     for f, cfg in bd.FEATURES.items()},
        "caveats": {
            "TT2_Booster_Pct": "TT2 and booster sums may double-count women given both; preserved, not adjusted.",
            "Severe_Anemia_Pct": "Definition changed: threshold <7 (2020-23) to <=7 (2023-24+); Hb<11 terminology "
                                 "relabelled (7.1-10.9 g/dl). Recent-HMIS indicator only; not claimed as harmonized "
                                 "with Dataset 1/2.",
            "Obstetric_Complications_Pct": "Aggregate item 5.1 exists 2020-21..2022-23 only; schema break in "
                                           "2023-24+ to HRP items. Left NaN for 2023-24 and 2024-25. Not replaced "
                                           "by event-count components.",
        },
        "excluded": {
            "Institutional_Delivery_Pct": "Legacy denominator was ANC registrations (2.2/1.1), newer schema uses a "
                                          "different delivery structure; not constructed to avoid non-comparability.",
            "PNC_48h_Pct": "No comparable within-48-hour institutional PNC indicator across required years "
                           "(6.1 home-only; 6.2 is 48h-14d; 2.2.1 meaning changed across eras).",
            "legacy_2020_21_ut_files": ["Dadra & Nagar Haveli", "Daman & Diu"],
            "partial_2024_25_months": "apr..feb cumulative files available for 36 states but excluded from annual panel",
            "fy_2025_26": "files listed on portal but anonymous downloads returned HTTP 500; not downloaded, not included",
        },
        "validation": {
            "denominator_zero_returns_nan": True,
            "missing_numerator_returns_nan": True,
            "missing_denominator_returns_nan": True,
            "no_clipping": True,
            "out_of_range_flagged_not_fixed": True,
            "no_imputation": True,
        },
        "rounding": "percentages written to 4 decimals; computed from full integer counts; NaN = unavailable",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "row_counts": {"total": int(len(df)),
                       "per_year": {y: int((df["Year"] == y).sum()) for y in years}},
        "coverage": {"n_unique_state_district": int(df["Skey"].nunique()),
                     "n_states_overall": int(df["State"].nunique()),
                     "reference_36_states_matched": int(len(set(df["State"].map(norm)) & ref_states)),
                     "reference_707_units_matched_overall": int(len(all_units & ref_units))},
    }
    with open(os.path.join(OUT, "dataset3_metadata.json"), "w") as fh:
        json.dump(meta, fh, indent=2)

    print("reports artifacts written. total rows =", len(df),
          "| unique S-D =", int(df["Skey"].nunique()),
          "| dups =", dups)


def _caveat(f):
    return {
        "ANC_First_Trimester_Pct": "denominator is (NEW) PW ANC registered; 1.1 label gains 'NEW' from 2023-24",
        "TT2_Booster_Pct": "possible double-count between 1.2.2 and 1.2.3; values may legitimately exceed 100",
        "Severe_Anemia_Pct": "definition changed <7 (2020-23) -> <=7 (2023-24+); recent-HMIS indicator only",
        "Obstetric_Complications_Pct": "2020-2021..2022-2023 only; numerator 5.1 attended cases; denominator is "
                                       "home SBA + home non-SBA + institutional deliveries",
    }[f]


if __name__ == "__main__":
    main()