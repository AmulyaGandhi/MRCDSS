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


def _normalized_key(df: pd.DataFrame):
    return df["State"].map(_norm) + "||" + df["District"].map(_norm)


def get_unified_overview():
    df = _dataframe()
    counts = df["source_dataset"].value_counts().to_dict()
    era = df["data_era"].value_counts().to_dict()
    historical = df[df["data_era"] == "HISTORICAL_MRCDSS"]
    recent = df[df["data_era"] == "RECENT_HMIS"]
    normalized_units = int(_normalized_key(df).nunique())
    raw_units = int(df[["State", "District"]].drop_duplicates().shape[0])
    normalized_states = int(df["State"].map(_norm).nunique())
    raw_states = int(df["State"].nunique())
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
        "n_state_district_units": normalized_units,
        "n_states": normalized_states,
        "identity_reconciliation": {
            "raw_state_district_entries": raw_units,
            "normalized_state_district_units": normalized_units,
            "duplicate_normalized_entries": raw_units - normalized_units,
            "raw_state_strings": raw_states,
            "normalized_states": normalized_states,
            "note": (
                "Raw State/District spellings are retained for provenance. Counts, listings, and "
                "retrieval use case-, punctuation-, and '&/and'-insensitive normalized keys."
            ),
        },
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
    work = df.copy()
    work["_state_key"] = work["State"].map(_norm)
    work["_district_key"] = work["District"].map(_norm)
    districts = []
    for (state_key, district_key), group in work.groupby(["_state_key", "_district_key"], sort=True):
        historical = group[group["data_era"] == "HISTORICAL_MRCDSS"]
        recent = group[group["data_era"] == "RECENT_HMIS"]
        latest_h = historical.sort_values("Year").iloc[-1] if len(historical) else None
        latest_r = recent.sort_values("Year").iloc[-1] if len(recent) else None
        display_row = latest_h if latest_h is not None else latest_r
        aliases = (
            group[["State", "District"]]
            .drop_duplicates()
            .sort_values(["State", "District"])
            .to_dict("records")
        )
        districts.append({
            "state": display_row["State"],
            "district": display_row["District"],
            "normalized_state": state_key,
            "normalized_district": district_key,
            "aliases": aliases,
            "historical_records": int(len(historical)),
            "recent_records": int(len(recent)),
            "historical_years": sorted(historical["Year"].unique().tolist()) if len(historical) else [],
            "recent_years": sorted(recent["Year"].unique().tolist()) if len(recent) else [],
            "latest_historical_year": str(latest_h["Year"]) if latest_h is not None else None,
            "latest_historical_risk_class": latest_h["risk_class"] if latest_h is not None else None,
            "latest_recent_year": str(latest_r["Year"]) if latest_r is not None else None,
        })
    return {
        "count": len(districts),
        "raw_entry_count": int(df[["State", "District"]].drop_duplicates().shape[0]),
        "districts": districts,
        "note": (
            "One record per normalized State–District identity. Raw spelling aliases are preserved in "
            "the aliases field; no source records were merged or rewritten."
        ),
    }


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

    aliases = (
        matched[["State", "District"]]
        .drop_duplicates()
        .sort_values(["State", "District"])
        .to_dict("records")
    )
    return {
        "state": str(historical["State"].iloc[0]) if len(historical) else str(recent["State"].iloc[0]),
        "district": str(historical["District"].iloc[0]) if len(historical) else str(recent["District"].iloc[0]),
        "normalized_state": target_s,
        "normalized_district": target_d,
        "aliases": aliases,
        "historical_records": int(len(historical)),
        "recent_records": int(len(recent)),
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