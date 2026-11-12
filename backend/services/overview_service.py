import os
import pandas as pd
from typing import Optional

from config import (
    RISK_CLUSTERS_CSV,
    PRIORITY_SUMMARY_CSV,
    FEATURE_IMPORTANCE_CSV,
    PREPROCESSED_CSV,
    DECISION_SUPPORT_CSV,
)
from services.data_loader import load_csv, get_record_count


def get_overview_data():
    clusters_df = load_csv(RISK_CLUSTERS_CSV)
    priority_df = load_csv(PRIORITY_SUMMARY_CSV)
    features_df = load_csv(PREPROCESSED_CSV)
    importance_df = load_csv(FEATURE_IMPORTANCE_CSV)
    ds_df = load_csv(DECISION_SUPPORT_CSV)

    total_records = get_record_count(clusters_df)
    state_district_units = get_record_count(priority_df)
    state_count = len(priority_df["State"].unique()) if priority_df is not None and "State" in priority_df.columns else 0

    if clusters_df is not None and "Year" in clusters_df.columns:
        min_year = int(clusters_df["Year"].min())
        max_year = int(clusters_df["Year"].max())
    else:
        min_year = 2008
        max_year = 2019

    risk_dist = {}
    if clusters_df is not None and "risk_class" in clusters_df.columns:
        risk_counts = clusters_df["risk_class"].value_counts().to_dict()
        risk_dist = {k: int(v) for k, v in risk_counts.items()}

    priority_dist = {}
    if ds_df is not None and "priority_level" in ds_df.columns:
        priority_counts = ds_df["priority_level"].value_counts().to_dict()
        priority_dist = {k: int(v) for k, v in priority_counts.items()}

    feature_ranking = []
    if importance_df is not None and "feature" in importance_df.columns and "mean_abs_shap" in importance_df.columns:
        sorted_df = importance_df.sort_values("mean_abs_shap", ascending=False)
        for _, row in sorted_df.iterrows():
            feature_ranking.append({
                "feature": row["feature"],
                "mean_abs_shap": float(row["mean_abs_shap"]),
            })

    return {
        "total_records": total_records,
        "state_district_units": state_district_units,
        "state_count": state_count,
        "year_coverage": {"start": min_year, "end": max_year},
        "risk_distribution": risk_dist,
        "priority_distribution": priority_dist,
        "feature_ranking": feature_ranking,
    }
