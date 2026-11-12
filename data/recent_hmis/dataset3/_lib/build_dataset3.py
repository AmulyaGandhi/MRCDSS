"""Construct Dataset 3: standalone district-year recent-HMIS analytical dataset.

Reads RAW cumulative HMIS XLSX files (read-only) and the inspection parsers,
recomputes four indicators at district Total level, and writes analysis outputs
under data/recent_hmis/dataset3/. Never modifies raw files or any MRCDSS output.
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import warnings

warnings.filterwarnings("ignore")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
LIB = os.path.join(ROOT, "data", "recent_hmis", "inspection", "_lib")
if LIB not in sys.path:
    sys.path.insert(0, LIB)

import hmis_reader as hr
import reconstruct as rc

OUT = os.path.join(ROOT, "data", "recent_hmis", "dataset3")
MANIFEST = os.path.join(ROOT, "data", "recent_hmis", "raw", "_manifest.json")

YEAR_ORDER = ["2020-2021", "2021-2022", "2022-2023", "2023-2024", "2024-2025"]

# --------------------------------------------------------------------------- #
# Feature definitions (codes refer to the HMIS 'Data Item Wise Report' layout)
# --------------------------------------------------------------------------- #
FEATURES = {
    "ANC_First_Trimester_Pct": {
        "num_codes": ["1.1.1"], "den_codes": ["1.1"], "sum_num": False,
        "description": "1.1.1 (ANC within 1st trimester) / 1.1 ((NEW) PW ANC registered) x 100",
        "years": None,
    },
    "TT2_Booster_Pct": {
        "num_codes": ["1.2.2", "1.2.3"], "den_codes": ["1.1"], "sum_num": True,
        "description": "(1.2.2 TT2/Td2 + 1.2.3 TT/Td Booster) / 1.1 ((NEW) PW ANC registered) x 100 "
                       "- possible double-count for women given both doses",
        "years": None,
    },
    "Severe_Anemia_Pct": {
        "num_codes": ["1.4.3"], "den_codes": ["1.4.2"], "sum_num": False,
        "description": "1.4.3 (Hb<7 old schema / Hb<=7 new schema) / 1.4.2 (Hb<11) x 100 "
                       "- definition changed across schema; recent-HMIS indicator only",
        "years": None,
    },
    "Obstetric_Complications_Pct": {
        "num_codes": ["5.1"], "den_codes": ["2.1.1.a", "2.1.1.b", "2.2"], "sum_num": False,
        "description": "5.1 (aggregate obstetric complications attended) / "
                       "(home SBA + home non-SBA + institutional deliveries) x 100; "
                       "available 2020-21 .. 2022-23 only",
        "years": {"2020-2021", "2021-2022", "2022-2023"},
    },
}

PRIMARY_COLS = ["State", "District", "Year", "source_dataset"] + list(FEATURES)

# Legacy pre-merger UT files from FY 2020-21 (covered by the merged file below)
EXCLUDED_LEGACY = {"dadra and nagar haveli": "2020-2021", "daman and diu": "2020-2021"}


def norm(key: str) -> str:
    return " ".join(re.sub(r"[&]", "and", (key or "").lower()).split())


def load_manifest():
    with open(MANIFEST) as fh:
        return [r for r in json.load(fh) if r.get("status") == "downloaded"]


def select_files(records):
    """Returns (selected, excluded): lists of (fy, state, rec[, reason])."""
    selected, excluded = [], []
    for r in records:
        fy = r["fiscal_year"]
        st = r["state"]
        mon = (r.get("cumulative_month") or "").strip().lower()
        fname = (r.get("filename") or "").lower()
        is_mar = mon.startswith("mar") or "_upto_mar" in fname
        if fy == "2025-2026":
            continue
        if norm(st) in EXCLUDED_LEGACY:
            excluded.append((fy, st, r, "2020-21 legacy pre-merger UT file; merged file used instead"))
            continue
        if fy == "2024-2025":
            if is_mar:
                selected.append((fy, st, r))
            else:
                excluded.append((fy, st, r, "partial cumulative month; excluded from annual panel"))
            continue
        if is_mar:
            selected.append((fy, st, r))
        else:
            excluded.append((fy, st, r, "unexpected non-Mar cumulative file"))
    return selected, excluded


def extract_file(path):
    """Parse one workbook -> (ws, {district_name: {code: float|None}}) on Total columns."""
    ws = hr.load(path)
    if not ws.groups:
        raise ValueError("no district groups parsed")
    need = sorted({c for f in FEATURES.values() for c in (f["num_codes"] + f["den_codes"])})
    items_by_code = {c: rc.item_by_code(ws, c) for c in need}
    out = {}
    for g in ws.groups[1:]:
        name = (g.name or "").strip()
        if not name:
            continue
        vals = {}
        for c in need:
            it = items_by_code[c]
            vals[c] = rc.num(it.values.get(g.name)) if it is not None else None
        out[name] = vals
    return ws, out


def compute(fy, items):
    """Apply per-feature validation rules. Returns (values, flags, raw)."""
    values, flags, raw = {}, {}, {}
    for fname, cfg in FEATURES.items():
        years = cfg["years"]
        nn = [items[c] for c in cfg["num_codes"]]
        dd = [items[c] for c in cfg["den_codes"]]
        if years is not None and fy not in years:
            values[fname], raw[fname] = None, {"n": None, "d": None}
            flags[fname] = "structurally unavailable: aggregate 5.1 not in 2023-24+ schema"
            continue
        miss_n = [c for c, v in zip(cfg["num_codes"], nn) if v is None]
        miss_d = [c for c, v in zip(cfg["den_codes"], dd) if v is None]
        n = sum(nn) if not miss_n else None
        d = sum(dd) if not miss_d else None
        raw[fname] = {"n": n, "d": d}
        if n is None or d is None:
            values[fname] = None
            flags[fname] = ("numerator missing (%s)" % ",".join(miss_n) if miss_n else "") + \
                           (("; " if miss_n and miss_d else "") +
                            ("denominator missing (%s)" % ",".join(miss_d) if miss_d else ""))
            continue
        if d == 0:
            values[fname], flags[fname] = None, "denominator == 0"
            continue
        v = n / d * 100.0
        values[fname] = v
        flags[fname] = f"invalid range (value {v:.3f} outside [0,100])" if (v < 0 or v > 100) else ""
    return values, flags, raw


def main():
    os.makedirs(OUT, exist_ok=True)
    selected, excluded = select_files(load_manifest())
    selected.sort(key=lambda x: (YEAR_ORDER.index(x[0]), norm(x[1])))

    rows, counts, flag_rows, src_map, file_errors = [], [], [], [], []
    n_zero = {f: 0 for f in FEATURES}

    for fy, st, rec in selected:
        lp = rec.get("local_path")
        path = os.path.join(ROOT, lp) if lp else None
        if not path or not os.path.exists(path):
            file_errors.append((fy, st, "missing local file"))
            continue
        try:
            ws, items = extract_file(path)
        except Exception as e:  # noqa: BLE001
            file_errors.append((fy, st, f"parse error: {e}"))
            continue
        districts = sorted(items)
        if ws.groups[0].name.strip() and not districts:
            file_errors.append((fy, st, "no districts parsed"))
            continue
        seen = {}
        dups = []
        for d in districts:
            seen[d] = seen.get(d, 0) + 1
            if seen[d] == 2:
                dups.append(d)
            obs = {"fy": fy, "items": items[d]}
            values, flags, raw = compute(fy, items[d])
            for fname in FEATURES:
                if flags[fname] == "denominator == 0":
                    n_zero[fname] += 1
            rows.append({"State": st, "District": d, "Year": fy,
                         "source_dataset": "recent_hmis_annual_up_to_mar", **values})
            counts.append({**{"State": st, "District": d, "Year": fy,
                              "source_file": rec.get("filename"),
                              "cumulative_month": rec.get("cumulative_month")},
                           **{f"{f}_numerator": raw[f]["n"] for f in FEATURES},
                           **{f"{f}_denominator": raw[f]["d"] for f in FEATURES}})
            for fname in FEATURES:
                if flags[fname]:
                    flag_rows.append({"State": st, "District": d, "Year": fy, "Feature": fname,
                                      "flag": flags[fname],
                                      "value": "" if values[fname] is None
                                      else round(values[fname], 4)})
        src_map.append({"fiscal_year": fy, "state": st, "filename": rec.get("filename"),
                        "cumulative_month": rec.get("cumulative_month"),
                        "server_path": rec.get("server_path"), "local_path": rec.get("local_path"),
                        "sha256": rec.get("sha256"), "file_size_bytes": rec.get("file_size_bytes"),
                        "last_modified_date": rec.get("last_modified_date"),
                        "n_districts_parsed": len(districts),
                        "duplicate_district_names": ",".join(dups) if dups else ""})
        print(f"  {fy} {st:30} districts={len(districts):3}")

    with open(os.path.join(OUT, "dataset3_recent_hmis.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=PRIMARY_COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if k in FEATURES and r[k] is None
                            else (round(r[k], 4) if k in FEATURES and isinstance(r[k], float) else r[k]))
                        for k in PRIMARY_COLS})

    ccols = list(counts[0].keys())
    with open(os.path.join(OUT, "indicator_counts.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=ccols)
        w.writeheader(); w.writerows(counts)

    with open(os.path.join(OUT, "percent_invalid_flags.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["State", "District", "Year", "Feature", "flag", "value"])
        w.writeheader(); w.writerows(flag_rows)

    with open(os.path.join(OUT, "source_file_mapping.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(src_map[0].keys()))
        w.writeheader(); w.writerows(src_map)

    json.dump({"selected_count": len(selected), "excluded_count": len(excluded),
               "zero_denominators": n_zero, "file_errors": file_errors},
              open(os.path.join(OUT, "_build_run_summary.json"), "w"), indent=1)

    print(f"\nprimary rows: {len(rows)}  zero_denominators: {n_zero}  file_errors: {len(file_errors)}")
    return rows, counts, flag_rows, src_map, selected, excluded, file_errors


if __name__ == "__main__":
    main()