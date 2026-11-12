"""Serve the unified MRCDSS + Recent HMIS dataset (read-only).

Reads the derived `data/unified/unified_mr_cdss_data.csv`, which appends the
historical MRCDSS rows (Dataset 1/2 as used by the existing risk model) and the
Recent HMIS extension (Dataset 3) into one table. Nothing is written and no
indicator is recomputed at request time. Existing endpoints are untouched; this
service is purely additive.
"""
from __future__ import annotations

import os
import re

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UNIFIED_CSV = os.path.join(PROJECT_ROOT, "data", "unified", "unified_mr_cdss_data.csv")

FEATURE_ORDER = [
    "ANC_First_Trimester_Pct",
    "TT2_Booster_Pct",
    "Severe_Anemia_Pct",
    "Institutional_Delivery_Pct",
    "SBA_Home_Delivery_Pct",
    "PNC_48h_Pct",
    "Obstetric_Complications_Pct",
]

FEATURE_DISPLAY = {
    "ANC_First_Trimester_Pct": "ANC First Trimester",
    "TT2_Booster_Pct": "TT2 / Booster",
    "Severe_Anemia_Pct": "Severe Anemia",
    "Institutional_Delivery_Pct": "Institutional Delivery",
    "SBA_Home_Delivery_Pct": "SBA Home Delivery (raw reference)",
    "PNC_48h_Pct": "PNC within 48h",
    "Obstetric_Complications_Pct": "Obstetric Complications",
}

PERIOD_TEXTS = {
    "data_coverage": "MRCDSS data coverage: 2008-2025",
    "risk_model_period": "Risk model period: historical MRCDSS data",
    "recent_hmis_extension": "Recent HMIS extension: 2020-2025",
    "partial_2024_2025": ("2024-25 is a partial year: 17 states with complete UpTo_Mar files "
                          "are included; other states were excluded from the annual Recent HMIS set"),
}

_CACHE = {"df": None}


def _norm(value):
    s = re.sub(r"&", "and", str(value).lower())
    return re.sub(r"[^a-z0-9]", "", s)


def _dataframe():
    if _CACHE["df"] is None:
        _CACHE["df"] = pd.read_csv(UNIFIED_CSV)
    return _CACHE["df"]


def _records(df, cols):
    out = []
    for row in df.itertuples(index=False):
        rec = {}
        for col in cols:
            v = getattr(row, col)
            if isinstance(v, float) and pd.isna(v):
                rec[col] = None
            elif isinstance(v, (int, str)):
                rec[col] = v
            elif pd.isna(v):
                rec[col] = None
            else:
                rec[col] = v
        out.append(rec)
    return out


def get_unified_overview():
    df = _dataframe()
    counts = df["source_dataset"].value_counts().to_dict()
    era = df["data_era"].value_counts().to_dict()
    historical = df[df["data_era"] == "HISTORICAL_MRCDSS"]
    recent = df[df["data_era"] == "RECENT_HMIS"]
    feature_availability = []
    for col in FEATURE_ORDER:
        feature_availability.append({
            "key": col,
            "name": FEATURE_DISPLAY[col],
            "historical_valid": int(historical[col].notna().sum()),
            "historical_total": int(len(historical)),
            "recent_valid": int(recent[col].notna().sum()),
            "recent_total": int(len(recent)),
        })
    return {
        "dataset": "Unified MRCDSS + Recent HMIS",
        "total_observations": int(len(df)),
        "counts_by_source": {
            "dataset1": int(counts.get("dataset1", 0)),
            "dataset2": int(counts.get("dataset2", 0)),
            "recent_hmis": int(counts.get("recent_hmis", 0)),
        },
        "counts_by_era": {
            "HISTORICAL_MRCDSS": int(era.get("HISTORICAL_MRCDSS", 0)),
            "RECENT_HMIS": int(era.get("RECENT_HMIS", 0)),
        },
        "n_state_district_units": int(
            df.groupby([df["State"].map(_norm), df["District"].map(_norm)]).ngroups
        ),
        "n_states": int(df["State"].nunique()),
        "historical_years": sorted(historical["Year"].unique().tolist()),
        "recent_years": sorted(recent["Year"].unique().tolist()),
        "period_texts": dict(PERIOD_TEXTS),
        "feature_availability": feature_availability,
        "risk_classification": {
            "historical_with_risk": int(historical["risk_class"].notna().sum()),
            "recent_with_risk": int(recent["risk_class"].notna().sum()),
            "note": "Historical MRCDSS records retain their original risk classification; "
                    "Recent HMIS records are not assigned any risk class.",
        },
    }


def get_unified_districts():
    df = _dataframe()
    districts = []
    groups = {
        "historical": df[df["data_era"] == "HISTORICAL_MRCDSS"],
        "recent": df[df["data_era"] == "RECENT_HMIS"],
    }
    keys = {}
    for era, sub in groups.items():
        for (state, district), part in sub.groupby([sub["State"], sub["District"]]):
            keys.setdefault((state, district), {"historical": pd.DataFrame(), "recent": pd.DataFrame()})
            keys[(state, district)][era] = part
    for (state, district), parts in sorted(keys.items()):
        h = parts["historical"]
        r = parts["recent"]
        latest_h = h.sort_values("Year").iloc[-1] if len(h) else None
        latest_r = r.sort_values("Year").iloc[-1] if len(r) else None
        districts.append({
            "state": state,
            "district": district,
            "historical_records": int(len(h)),
            "recent_records": int(len(r)),
            "historical_years": sorted(h["Year"].unique().tolist()) if len(h) else [],
            "recent_years": sorted(r["Year"].unique().tolist()) if len(r) else [],
            "latest_historical_year": str(latest_h["Year"]) if latest_h is not None else None,
            "latest_historical_risk_class": latest_h["risk_class"] if latest_h is not None else None,
            "latest_recent_year": str(latest_r["Year"]) if latest_r is not None else None,
        })
    return {"count": len(districts), "districts": districts}


def get_unified_district(state: str, district: str):
    df = _dataframe()
    target_s = _norm(state)
    target_d = _norm(district)
    row_match = (
        df["State"].map(_norm).eq(target_s)
        & df["District"].map(_norm).eq(target_d)
    )
    matched = df[row_match]
    if matched.empty:
        return {"state": state, "district": district, "matched": False,
                "historical": [], "recent": [], "period_texts": dict(PERIOD_TEXTS)}
    historical = matched[matched["data_era"] == "HISTORICAL_MRCDSS"].sort_values("Year")
    recent = matched[matched["data_era"] == "RECENT_HMIS"].sort_values("Year")

    hist_cols = ["Year", "risk_class", "priority_level",
                 "top_contributing_feature_1", "top_contributing_feature_2", "top_contributing_feature_3",
                 "planning_focus_1", "planning_focus_2", "planning_focus_3", *FEATURE_ORDER]
    rec_cols = ["Year", *FEATURE_ORDER, "source_dataset", "hmis_source_file",
                "indicator_definition_status"]

    return {
        "state": str(historical["State"].iloc[0]) if len(historical) else str(recent["State"].iloc[0]),
        "district": str(historical["District"].iloc[0]) if len(historical) else str(recent["District"].iloc[0]),
        "matched": True,
        "historical": _records(historical, hist_cols),
        "recent": _records(recent, rec_cols),
        "period_texts": dict(PERIOD_TEXTS),
    }


def get_unified_years():
    df = _dataframe()
    historical = df[df["data_era"] == "HISTORICAL_MRCDSS"]
    recent = df[df["data_era"] == "RECENT_HMIS"]
    return {
        "historical": sorted(historical["Year"].unique().tolist()),
        "recent": sorted(recent["Year"].unique().tolist()),
        "period_texts": dict(PERIOD_TEXTS),
    }