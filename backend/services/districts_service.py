import os
import pandas as pd
from typing import Optional, List, Dict, Any

from config import DECISION_SUPPORT_CSV, RISK_CLUSTERS_CSV, PREPROCESSED_CSV
from services.data_loader import load_csv, get_record_count


RISK_CLASS_MAP = {
    "Low": "Low Risk",
    "Medium": "Medium Risk",
    "High": "High Risk",
}

PRIORITY_MAP = {
    "Low": "Low Priority",
    "Medium": "Medium Priority",
    "High": "High Priority",
}


def get_districts(state: Optional[str] = None,
                  district: Optional[str] = None,
                  risk_class: Optional[str] = None,
                  priority: Optional[str] = None,
                  year: Optional[int] = None,
                  page: int = 1,
                  per_page: int = 10):
    df = load_csv(DECISION_SUPPORT_CSV)
    if df is None:
        return {"count": 0, "records": [], "page": page, "per_page": per_page, "total": 0}

    if state:
        df = df[df["State"] == state]
    if district:
        df = df[df["District"].str.contains(district, case=False, na=False)]
    if risk_class:
        mapped = RISK_CLASS_MAP.get(risk_class, risk_class)
        df = df[df["risk_class"] == mapped]
    if priority:
        mapped = PRIORITY_MAP.get(priority, priority)
        df = df[df["priority_level"] == mapped]
    if year is not None:
        df = df[df["Year"] == year]

    total = len(df)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = df.iloc[start:end]

    records = []
    for _, row in paginated.iterrows():
        record = {
            "state": row.get("State", ""),
            "district": row.get("District", ""),
            "year": int(row.get("Year", 0)),
            "risk_class": row.get("risk_class", ""),
            "priority": row.get("priority_level", ""),
            "top_planning_focus": row.get("planning_focus_1", ""),
        }
        records.append(record)

    return {
        "count": len(records),
        "records": records,
        "page": page,
        "per_page": per_page,
        "total": total,
    }


def get_district_detail(state: str, district: str):
    ds_df = load_csv(DECISION_SUPPORT_CSV)
    rc_df = load_csv(RISK_CLUSTERS_CSV)

    if ds_df is None:
        return None

    mask = (ds_df["State"] == state) & (ds_df["District"] == district)
    district_df = ds_df[mask].sort_values("Year")

    if len(district_df) == 0:
        return None

    records = []
    for _, row in district_df.iterrows():
        record = {
            "state": row.get("State", ""),
            "district": row.get("District", ""),
            "year": int(row.get("Year", 0)),
            "risk_class": row.get("risk_class", ""),
            "priority": row.get("priority_level", ""),
            "top_contributing_feature_1": row.get("top_contributing_feature_1", ""),
            "top_contributing_feature_2": row.get("top_contributing_feature_2", ""),
            "top_contributing_feature_3": row.get("top_contributing_feature_3", ""),
            "planning_focus_1": row.get("planning_focus_1", ""),
            "planning_focus_2": row.get("planning_focus_2", ""),
            "planning_focus_3": row.get("planning_focus_3", ""),
        }

        if rc_df is not None and "State" in rc_df.columns and "District" in rc_df.columns:
            rc_mask = (rc_df["State"] == state) & (rc_df["District"] == district) & (rc_df["Year"] == int(row.get("Year", 0)))
            rc_match = rc_df[rc_mask]
            if len(rc_match) > 0:
                rc = rc_match.iloc[0]
                record["ANC_First_Trimester_Pct"] = float(rc.get("ANC_First_Trimester_Pct", 0))
                record["TT2_Booster_Pct"] = float(rc.get("TT2_Booster_Pct", 0))
                record["Severe_Anemia_Pct"] = float(rc.get("Severe_Anemia_Pct", 0))
                record["Institutional_Delivery_Pct"] = float(rc.get("Institutional_Delivery_Pct", 0))
                record["PNC_48h_Pct"] = float(rc.get("PNC_48h_Pct", 0))
                record["Obstetric_Complications_Pct"] = float(rc.get("Obstetric_Complications_Pct", 0))

        records.append(record)

    years = sorted(set(int(r["year"]) for r in records))

    return {
        "state": state,
        "district": district,
        "record_count": len(records),
        "years": years,
        "records": records,
    }


def get_all_states():
    df = load_csv(DECISION_SUPPORT_CSV)
    if df is None:
        return []
    return sorted(df["State"].unique().tolist())


def get_all_years():
    df = load_csv(DECISION_SUPPORT_CSV)
    if df is None:
        return []
    return sorted(df["Year"].unique().tolist())


def get_latest_district_observations():
    """Project the latest available observation for each (State, District) unit.

    This is a read-only projection over the existing decision-support CSV. It does
    not modify ML/DSS logic, models, or analytical results. For every unique
    (State, District) pair, the record with the maximum Year is selected and used
    as that unit's current risk profile.
    """
    df = load_csv(DECISION_SUPPORT_CSV)
    if df is None or len(df) == 0:
        return {
            "count": 0,
            "records": [],
            "total": 0,
        }

    # Sort descending by Year and keep the first (latest) row per (State, District).
    sorted_df = df.sort_values(["State", "District", "Year"], ascending=[True, True, False])
    latest_df = sorted_df.drop_duplicates(subset=["State", "District"], keep="first")

    records = []
    for _, row in latest_df.iterrows():
        records.append({
            "state": row.get("State", ""),
            "district": row.get("District", ""),
            "year": int(row.get("Year", 0)),
            "risk_class": row.get("risk_class", ""),
            "priority": row.get("priority_level", ""),
            "top_contributing_feature_1": row.get("top_contributing_feature_1", ""),
            "top_contributing_feature_2": row.get("top_contributing_feature_2", ""),
            "top_contributing_feature_3": row.get("top_contributing_feature_3", ""),
            "planning_focus_1": row.get("planning_focus_1", ""),
            "planning_focus_2": row.get("planning_focus_2", ""),
            "planning_focus_3": row.get("planning_focus_3", ""),
        })

    return {
        "count": len(records),
        "records": records,
        "total": len(records),
    }
