"""Serve pre-aggregated, read-only summaries of the Dataset 3 recent-HMIS extension.

Reads the prepared Dataset 3 CSV (dataset3_recent_hmis.csv) and the coverage
audit mapping file; NO indicator is recomputed from raw HMIS files at request
time and nothing is written. The original MRCDSS model/DSS data is untouched.
"""
from __future__ import annotations

import os
import re

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D3_DIR = os.path.join(PROJECT_ROOT, "data", "recent_hmis", "dataset3")
D3_CSV = os.path.join(D3_DIR, "dataset3_recent_hmis.csv")
AUDIT_MAPPING_CSV = os.path.join(D3_DIR, "coverage_audit", "district_mapping_candidates.csv")

FEATURE_DISPLAY = {
    "ANC_First_Trimester_Pct": "ANC First Trimester",
    "TT2_Booster_Pct": "TT2 / Booster",
    "Severe_Anemia_Pct": "Severe Anemia",
    "Obstetric_Complications_Pct": "Obstetric Complications",
}

INDICATOR_DETAILS = {
    "ANC_First_Trimester_Pct": {
        "status": "Available",
        "note": ("Computed from HMIS 'NEW' PW ANC registrations; the point-of-care label is stable "
                 "across the acquired period (a 'NEW' clarifier is added from 2023-24)."),
    },
    "TT2_Booster_Pct": {
        "status": "Available — values may exceed 100",
        "note": ("TT2 and booster components may overlap, so reconstructed percentages can "
                 "legitimately exceed 100; values above 100 are retained, not clipped."),
    },
    "Severe_Anemia_Pct": {
        "status": "Definition changed",
        "note": ("Hb threshold changed from <7 g/dl (2020-21..2022-23) to <=7 g/dl from 2023-24. "
                 "Interpreted as one recent-HMIS series within Dataset 3 only."),
    },
    "Obstetric_Complications_Pct": {
        "status": "Available through 2022-23",
        "note": ("Aggregate indicator available through 2022-23; the newer HMIS schema does not "
                 "provide the same aggregate, so values are NaN from 2023-24 onward."),
    },
}

HARMONIZATION_ROWS = [
    {"indicator": "ANC First Trimester", "status": "Comparable",
     "reason": "Same underlying ANC registration and first-trimester items across the acquired years."},
    {"indicator": "TT2 / Booster", "status": "Comparable with caveat",
     "reason": "TT2 and booster may overlap; reconstructed values may legitimately exceed 100."},
    {"indicator": "Severe Anemia", "status": "Definition changed",
     "reason": "Hb threshold changed <7 (2020-23) to <=7 (2023-24+)."},
    {"indicator": "Institutional Delivery", "status": "Not comparable",
     "reason": "Newer HMIS schema uses a different delivery structure; excluded from Dataset 3."},
    {"indicator": "PNC within 48 hours", "status": "Not comparable",
     "reason": "No comparable within-48h institutional indicator across the acquired years; excluded."},
    {"indicator": "Obstetric Complications", "status": "Available through 2022-23; schema changes afterward",
     "reason": "Aggregate item available through 2022-23; newer schema switches to HRP-based items."},
]

YEAR_AVAILABILITY = [
    {"fiscal_year": "2020-2021",
     "availability": "Complete annual UpTo_Mar coverage — 36 states"},
    {"fiscal_year": "2021-2022",
     "availability": "Complete annual UpTo_Mar coverage — 36 states"},
    {"fiscal_year": "2022-2023",
     "availability": "Complete annual UpTo_Mar coverage — 36 states"},
    {"fiscal_year": "2023-2024",
     "availability": "Complete annual UpTo_Mar coverage — 36 states"},
    {"fiscal_year": "2024-2025",
     "availability": ("17 states with acquired UpTo_Mar files; other states only had partial "
                      "cumulative files and were excluded from the annual Dataset 3")},
    {"fiscal_year": "2025-2026",
     "availability": ("Not included because anonymous HMIS file downloads returned HTTP 500")},
]

REFERENCE_707_NOTE = (
    "The original MRCDSS reference contains 707 State-District units. Dataset 3 contains 812 "
    "distinct State-District identifiers across the acquired years. The difference is primarily "
    "associated with district reorganization, aliases, formatting variants, and HMIS's retrospective "
    "listing of newly created districts."
)

DISTRICT_NATIVE_NOTE = (
    "District identifiers were retained at their native HMIS representation; no automatic district "
    "merging was performed."
)

DISCLAIMER = (
    "Dataset 3 is a recent-HMIS analytical extension and was not used to retrain or externally "
    "validate the existing MRCDSS classifier."
)


def _norm(value):
    s = re.sub(r"&", "and", str(value).lower())
    return re.sub(r"[^a-z0-9]", "", s)


def _load_csv():
    if not os.path.exists(D3_CSV):
        return None
    return pd.read_csv(D3_CSV)


_CACHE = {"df": None, "audit": None}


def _dataframe():
    if _CACHE["df"] is None:
        _CACHE["df"] = _load_csv()
    return _CACHE["df"]


def _audit_counts():
    if _CACHE["audit"] is None:
        if not os.path.exists(AUDIT_MAPPING_CSV):
            _CACHE["audit"] = {}
        else:
            mapping = pd.read_csv(AUDIT_MAPPING_CSV)
            _CACHE["audit"] = mapping["Candidate_Type"].value_counts().to_dict() if len(mapping) else {}
    return _CACHE["audit"]


def get_recent_hmis_overview():
    df = _dataframe()
    if df is None:
        raise FileNotFoundError(D3_CSV)
    year_counts = df.groupby("Year").size().to_dict()
    return {
        "dataset": "Dataset 3 / Recent HMIS Extension",
        "total_observations": int(len(df)),
        "observations_by_year": {str(y): int(year_counts.get(y, 0)) for y in sorted(df["Year"].unique())},
        "n_state_district_units": int(df.groupby([df["State"].map(_norm), df["District"].map(_norm)]).ngroups),
        "n_states": int(df["State"].nunique()),
        "years": sorted(df["Year"].unique().tolist()),
        "notes": {
            "partial_2024_2025": "2024-25: 17 states with complete UpTo_Mar files",
            "not_included_2025_2026": "2025-26: not included because anonymous HMIS file downloads returned HTTP 500",
        },
        "year_availability": list(YEAR_AVAILABILITY),
    }


def get_recent_hmis_coverage():
    df = _dataframe()
    if df is None:
        raise FileNotFoundError(D3_CSV)
    ordered = ["2020-2021", "2021-2022", "2022-2023", "2023-2024", "2024-2025"]
    years_coverage = []
    df["_partial"] = df["Year"] == "2024-2025"
    for fy in ordered:
        sub = df[df["Year"] == fy]
        years_coverage.append({
            "fiscal_year": fy,
            "observations": int(len(sub)),
            "states": int(sub["State"].nunique()),
            "partial": bool(fy == "2024-2025"),
        })
    ref_units = 707
    ds3_units = int(df.groupby([df["State"].map(_norm), df["District"].map(_norm)]).ngroups)
    audit_counts = _audit_counts()
    type_label_map = {
        "FORMAT_VARIANT": "Format variants",
        "ALIAS_CANDIDATE": "Alias candidates",
        "POSSIBLE_REORGANIZATION": "Possible reorganizations",
        "POSSIBLE_SPLIT": "Possible split",
        "UNCERTAIN": "Uncertain",
    }
    candidates = {
        "reference_707_units": ref_units,
        "dataset_3_distinct_identifiers": ds3_units,
        "difference": max(ds3_units - ref_units, 0),
        "by_candidate_type": [
            {"type": type_label_map[k], "count": int(audit_counts.get(k, 0))}
            for k in type_label_map
        ],
        "reference_note": REFERENCE_707_NOTE,
        "native_representation_note": DISTRICT_NATIVE_NOTE,
    }
    return {
        "years_coverage": years_coverage,
        "district_coverage": candidates,
    }


def _feature_distribution(df_feature):
    """Bucket percentages into 10-pp bins; values above 100 form their own bin (not clipped)."""
    values = df_feature.dropna().astype(float)
    bins = [f"{i}-{i + 9}" for i in range(0, 100, 10)]
    counts = {b: int(((values >= i) & (values < i + 10)).sum()) for i, b in
              zip(range(0, 100, 10), bins)}
    above = int((values >= 100).sum())
    total = int(values.notna().sum())
    return {"bins": [{"label": b, "count": counts[b]} for b in bins] + [{"label": "100+", "count": above}],
            "total_values": total}


def get_recent_hmis_districts_latest():
    """Latest Recent HMIS observation per State+District (for the Recent HMIS map).

    Keeps the same key space as the historical /api/districts/latest endpoint but
    always reflects the most recent Dataset 3 observation for each district. Only
    used for the Recent HMIS data view; it never assigns a historical risk class.
    """
    df = _dataframe()
    if df is None:
        raise FileNotFoundError(D3_CSV)
    records = []
    norm_key = df["State"].map(_norm) + "|" + df["District"].map(_norm)
    for key, part in df.groupby(norm_key):
        latest = part.sort_values("Year").iloc[-1]
        records.append({
            "state": latest["State"],
            "district": latest["District"],
            "year": str(latest["Year"]),
            "ANC_First_Trimester_Pct": _float_or_none(latest["ANC_First_Trimester_Pct"]),
            "TT2_Booster_Pct": _float_or_none(latest["TT2_Booster_Pct"]),
            "Severe_Anemia_Pct": _float_or_none(latest["Severe_Anemia_Pct"]),
            "Obstetric_Complications_Pct": _float_or_none(latest["Obstetric_Complications_Pct"]),
        })
    return {
        "count": len(records),
        "records": records,
        "note": "Latest Recent HMIS (Dataset 3) observation per district; no risk classification.",
    }


def _float_or_none(value):
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(f):
        return None
    return f


def get_recent_hmis_indicators():
    df = _dataframe()
    if df is None:
        raise FileNotFoundError(D3_CSV)
    indicators = []
    distributions = {}
    for col, label in FEATURE_DISPLAY.items():
        valid = int(df[col].notna().sum())
        missing = int(len(df) - valid)
        indicators.append({
            "key": col,
            "name": label,
            "valid": valid,
            "missing": missing,
            "status": INDICATOR_DETAILS[col]["status"],
            "note": INDICATOR_DETAILS[col]["note"],
        })
        if col in ("ANC_First_Trimester_Pct", "TT2_Booster_Pct", "Severe_Anemia_Pct"):
            distributions[col] = _feature_distribution(df[col])
    return {
        "indicators": indicators,
        "distributions": distributions,
        "harmonization": list(HARMONIZATION_ROWS),
        "disclaimer": DISCLAIMER,
    }