import pandas as pd
from config import PRIORITY_SUMMARY_CSV, DECISION_SUPPORT_CSV, PLANNING_RULES_CSV
from services.data_loader import load_csv


REPEATED_PRIORITY_RULE = (
    "Repeated priority is a historical pattern label: a State–District unit receives it when at "
    "least two historical district-year records have the same priority level. It does not require "
    "consecutive years and does not describe the unit's latest priority."
)

REPEATED_PRIORITY_LABELS = {
    "High": "Repeated High Priority Observations",
    "Medium": "Repeated Medium Priority Observations",
    "Low": "Repeated Low Priority Observations",
    "Insufficient": "Insufficient History",
}


def repeated_priority_label(value: str | None) -> str:
    text = str(value or "")
    if "High" in text:
        return REPEATED_PRIORITY_LABELS["High"]
    if "Medium" in text:
        return REPEATED_PRIORITY_LABELS["Medium"]
    if "Low" in text:
        return REPEATED_PRIORITY_LABELS["Low"]
    return REPEATED_PRIORITY_LABELS["Insufficient"]


def _latest_historical_rows(ds_df: pd.DataFrame) -> pd.DataFrame:
    if ds_df is None or len(ds_df) == 0 or "Year" not in ds_df.columns:
        return pd.DataFrame()
    sorted_df = ds_df.sort_values(["State", "District", "Year"], ascending=[True, True, False])
    return sorted_df.drop_duplicates(subset=["State", "District"], keep="first")


def get_planning_priorities():
    ds_df = load_csv(DECISION_SUPPORT_CSV)
    summary_df = load_csv(PRIORITY_SUMMARY_CSV)
    rules_df = load_csv(PLANNING_RULES_CSV)

    priority_distribution = {}
    latest_priority_distribution = {}
    total_district_year_records = 0
    latest_year = None
    if ds_df is not None and "priority_level" in ds_df.columns:
        total_district_year_records = int(len(ds_df))
        priority_counts = ds_df["priority_level"].value_counts().to_dict()
        priority_distribution = {k: int(v) for k, v in priority_counts.items()}
        latest_df = _latest_historical_rows(ds_df)
        if len(latest_df):
            latest_priority_distribution = {
                k: int(v) for k, v in latest_df["priority_level"].value_counts().to_dict().items()
            }
            latest_year = int(latest_df["Year"].max())

    repeated_priority_info = {
        "total_units": 0,
        "total_district_year_records": total_district_year_records,
        "repeated_high": 0,
        "repeated_medium": 0,
        "repeated_low": 0,
        "insufficient_history": 0,
        "repeated_high_proportion": 0.0,
        "repeated_medium_proportion": 0.0,
        "repeated_low_proportion": 0.0,
        "latest_observation_year": latest_year,
        "rule": REPEATED_PRIORITY_RULE,
        "label": "Repeated priority observations",
    }
    if summary_df is not None:
        repeated_priority_info["total_units"] = int(len(summary_df))
        if "persistent_priority" in summary_df.columns:
            priority_counts = summary_df["persistent_priority"].value_counts().to_dict()
            for key, count in priority_counts.items():
                text = str(key)
                if "High" in text:
                    repeated_priority_info["repeated_high"] = int(count)
                elif "Medium" in text:
                    repeated_priority_info["repeated_medium"] = int(count)
                elif "Low" in text:
                    repeated_priority_info["repeated_low"] = int(count)
            labelled = int(sum(priority_counts.values()))
            repeated_priority_info["insufficient_history"] = int(len(summary_df) - labelled)
        total_units = repeated_priority_info["total_units"]
        if total_units:
            for key in ("high", "medium", "low"):
                repeated_priority_info[f"repeated_{key}_proportion"] = round(
                    repeated_priority_info[f"repeated_{key}"] / total_units, 4
                )

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
        latest_df = _latest_historical_rows(ds_df)
        feature_counts = {}
        for col in feature_cols:
            if col in ds_df.columns:
                for val in ds_df[col].dropna():
                    entry = feature_counts.setdefault(val, {
                        "record_top3_appearances": 0,
                        "record_top1_appearances": 0,
                        "latest_units_top3": 0,
                        "latest_units_top1": 0,
                    })
                    entry["record_top3_appearances"] += 1
        if "top_contributing_feature_1" in ds_df.columns:
            for val in ds_df["top_contributing_feature_1"].dropna():
                feature_counts[val]["record_top1_appearances"] += 1
        if len(latest_df):
            top3_cols = [c for c in feature_cols if c in latest_df.columns]
            for _, row in latest_df.iterrows():
                values = [row.get(c) for c in top3_cols if pd.notna(row.get(c))]
                for feature in set(values):
                    feature_counts.setdefault(feature, {
                        "record_top3_appearances": 0,
                        "record_top1_appearances": 0,
                        "latest_units_top3": 0,
                        "latest_units_top1": 0,
                    })["latest_units_top3"] += 1
                if "top_contributing_feature_1" in latest_df.columns:
                    top1 = row.get("top_contributing_feature_1")
                    if pd.notna(top1):
                        feature_counts[top1]["latest_units_top1"] += 1

        for feature, counts in sorted(
            feature_counts.items(),
            key=lambda x: x[1]["record_top3_appearances"],
            reverse=True,
        ):
            feature_planning_focus_counts.append({
                "feature": feature,
                **{k: int(v) for k, v in counts.items()},
            })

    return {
        "priority_distribution": priority_distribution,
        "latest_priority_distribution": latest_priority_distribution,
        "repeated_priority_info": repeated_priority_info,
        "priority_semantics": {
            "priority_distribution": "District-year historical records by DSS priority level.",
            "latest_priority_distribution": (
                "One latest historical record per State–District unit. This is the unit's latest "
                "historical assessment, not its current or live priority."
            ),
            "repeated_priority_info": REPEATED_PRIORITY_RULE,
        },
        "planning_focus_label": "Model-attributed planning focus",
        "planning_focus_note": (
            "Planning focus is mapped from the model's absolute SHAP top contributors. It indicates "
            "where the model attributed influence, not a verified district needs assessment."
        ),
        "planning_rules": planning_rules,
        "feature_planning_focus_counts": feature_planning_focus_counts,
        "feature_planning_focus_note": (
            "Record appearances count district-year records where a feature appears among the top "
            "three contributors. Latest-unit columns count distinct units once, using each unit's "
            "latest historical observation."
        ),
    }
