import os
import pandas as pd
from config import PRIORITY_SUMMARY_CSV, DECISION_SUPPORT_CSV, PLANNING_RULES_CSV
from services.data_loader import load_csv, get_record_count


def get_planning_priorities():
    ds_df = load_csv(DECISION_SUPPORT_CSV)
    summary_df = load_csv(PRIORITY_SUMMARY_CSV)
    rules_df = load_csv(PLANNING_RULES_CSV)

    priority_distribution = {}
    if ds_df is not None and "priority_level" in ds_df.columns:
        priority_counts = ds_df["priority_level"].value_counts().to_dict()
        priority_distribution = {k: int(v) for k, v in priority_counts.items()}

    persistent_priority_info = {
        "total_districts": 0,
        "persistent_high": 0,
        "persistent_medium": 0,
        "persistent_low": 0,
    }
    if summary_df is not None:
        persistent_priority_info["total_districts"] = len(summary_df)
        if "persistent_priority" in summary_df.columns:
            priority_counts = summary_df["persistent_priority"].value_counts().to_dict()
            for key, count in priority_counts.items():
                if "High" in key:
                    persistent_priority_info["persistent_high"] = int(count)
                elif "Medium" in key:
                    persistent_priority_info["persistent_medium"] = int(count)
                elif "Low" in key:
                    persistent_priority_info["persistent_low"] = int(count)

    planning_rules = []
    if rules_df is not None:
        for _, row in rules_df.iterrows():
            rule = {
                "feature": row.get("feature", ""),
                "planning_focus": row.get("planning_focus", ""),
                "feature_direction": row.get("feature_direction", ""),
            }
            planning_rules.append(rule)

    feature_planning_focus_counts = []
    if ds_df is not None:
        feature_cols = [
            "top_contributing_feature_1", "top_contributing_feature_2", "top_contributing_feature_3",
        ]
        feature_counts = {}
        for col in feature_cols:
            if col in ds_df.columns:
                for val in ds_df[col].dropna():
                    feature_counts[val] = feature_counts.get(val, 0) + 1

        for feature, count in sorted(feature_counts.items(), key=lambda x: x[1], reverse=True):
            feature_planning_focus_counts.append({
                "feature": feature,
                "count": int(count),
            })

    return {
        "priority_distribution": priority_distribution,
        "persistent_priority_info": persistent_priority_info,
        "planning_rules": planning_rules,
        "feature_planning_focus_counts": feature_planning_focus_counts,
    }
