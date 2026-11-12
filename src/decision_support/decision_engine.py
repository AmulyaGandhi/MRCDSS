import os
import sys
import pickle
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from planning_rules import (
    FEATURES,
    FEATURE_PLANNING_MAP,
    RISK_TO_PRIORITY,
    INPUT_PATH,
    OUTPUT_DIR,
)

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "models")


def load_data():
    df = pd.read_csv(INPUT_PATH)
    return df


def load_model_and_scaler():
    model_path = os.path.join(MODELS_DIR, "logistic_regression.pkl")
    scaler_path = os.path.join(MODELS_DIR, "logistic_regression_scaler.pkl")
    with open(model_path, "rb") as f:
        pipeline = pickle.load(f)
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    if hasattr(pipeline, "named_steps") and "classifier" in pipeline.named_steps:
        model = pipeline.named_steps["classifier"]
    else:
        model = pipeline
    return model, scaler


def compute_shap_all(model, scaler, df):
    import shap as shap_lib
    X = df[FEATURES]
    X_scaled = scaler.transform(X)

    background = X_scaled[:100]
    explainer = shap_lib.LinearExplainer(model, background, feature_names=FEATURES)
    shap_values_all = explainer.shap_values(X_scaled)

    if isinstance(shap_values_all, list):
        predicted = model.predict(X_scaled)
        class_idx = {"High Risk": 0, "Low Risk": 1, "Medium Risk": 2}
        result = np.zeros((len(X_scaled), len(FEATURES)))
        for i in range(len(X_scaled)):
            pred_class = predicted[i]
            idx = class_idx.get(pred_class, 0)
            result[i] = np.array(shap_values_all[idx])[i]
        return result
    else:
        shap_arr = np.array(shap_values_all)
        if shap_arr.ndim == 3:
            predicted = model.predict(X_scaled)
            class_idx = {"High Risk": 0, "Low Risk": 1, "Medium Risk": 2}
            result = np.zeros((len(X_scaled), len(FEATURES)))
            for i in range(len(X_scaled)):
                pred_class = predicted[i]
                idx = class_idx.get(pred_class, 0)
                result[i] = shap_arr[i, :, idx]
            return result
        return shap_arr


def get_top_contributing_features(shap_row, n=3):
    abs_shap = shap_row[FEATURES].abs()
    sorted_features = abs_shap.sort_values(ascending=False).head(n).index.tolist()
    return sorted_features


def build_district_decision_support(df, shap_values):
    if len(df) != len(shap_values):
        raise ValueError(f"Row count mismatch: df={len(df)}, shap={len(shap_values)}")

    records = []
    for i, (_, row) in enumerate(df.iterrows()):
        shap_row = pd.Series(shap_values[i], index=FEATURES)
        risk_class = row["risk_class"]
        priority = RISK_TO_PRIORITY[risk_class]

        top_features = get_top_contributing_features(shap_row, n=3)

        record = {
            "State": row["State"],
            "District": row["District"],
            "Year": int(row["Year"]),
            "source_dataset": row["source_dataset"],
            "risk_class": risk_class,
            "priority_level": priority,
            "top_contributing_feature_1": top_features[0] if len(top_features) > 0 else "",
            "top_contributing_feature_2": top_features[1] if len(top_features) > 1 else "",
            "top_contributing_feature_3": top_features[2] if len(top_features) > 2 else "",
            "planning_focus_1": FEATURE_PLANNING_MAP.get(top_features[0], "") if len(top_features) > 0 else "",
            "planning_focus_2": FEATURE_PLANNING_MAP.get(top_features[1], "") if len(top_features) > 1 else "",
            "planning_focus_3": FEATURE_PLANNING_MAP.get(top_features[2], "") if len(top_features) > 2 else "",
        }
        records.append(record)

    return pd.DataFrame(records)


def build_district_priority_summary(dss_df):
    summary_records = []

    grouped = dss_df.groupby(["State", "District"])
    for (state, district), group in grouped:
        years_observed = len(group)
        high_years = int((group["risk_class"] == "High Risk").sum())
        medium_years = int((group["risk_class"] == "Medium Risk").sum())
        low_years = int((group["risk_class"] == "Low Risk").sum())
        high_proportion = round(high_years / years_observed, 4) if years_observed > 0 else 0.0

        latest_year = int(group["Year"].max())
        latest_row = group[group["Year"] == latest_year].iloc[0]
        latest_risk = latest_row["risk_class"]

        if years_observed >= 2 and high_years >= 2:
            persistent = "Persistent High Priority"
        elif years_observed >= 2 and medium_years >= 2:
            persistent = "Persistent Medium Priority"
        elif years_observed >= 2 and low_years >= 2:
            persistent = "Persistent Low Priority"
        else:
            persistent = "Insufficient History"

        all_contributing = []
        for col in ["top_contributing_feature_1", "top_contributing_feature_2", "top_contributing_feature_3"]:
            all_contributing.extend(group[col].tolist())
        contrib_counts = pd.Series(all_contributing).value_counts()
        common_features = "; ".join(contrib_counts.head(3).index.tolist())

        summary = {
            "State": state,
            "District": district,
            "years_observed": years_observed,
            "high_risk_years": high_years,
            "medium_risk_years": medium_years,
            "low_risk_years": low_years,
            "high_risk_proportion": high_proportion,
            "latest_year": latest_year,
            "latest_risk_class": latest_risk,
            "persistent_priority": persistent,
            "common_contributing_features": common_features,
        }
        summary_records.append(summary)

    return pd.DataFrame(summary_records)


def generate_planning_rules_csv():
    rules = []
    for feat in FEATURES:
        rules.append({
            "feature": feat,
            "planning_focus": FEATURE_PLANNING_MAP[feat],
            "feature_direction": "protective (higher=better)" if feat in [
                "ANC_First_Trimester_Pct", "TT2_Booster_Pct",
                "Institutional_Delivery_Pct", "PNC_48h_Pct"
            ] else "risk (higher=worse)",
        })
    return pd.DataFrame(rules)


def generate_report(dss_df, summary_df, rules_df):
    lines = []
    lines.append("# Decision Support System Report")
    lines.append("")
    lines.append("**Type**: Public-health planning DSS")
    lines.append("**Purpose**: Transform risk classifications and SHAP contributing factors into district priority and planning focus.")
    lines.append("")
    lines.append("## Important Notes")
    lines.append("")
    lines.append("- This is a **public-health planning** DSS, not a clinical diagnosis or treatment recommendation system.")
    lines.append("- Risk labels originate from **K-Means clustering** (derived, not clinical ground truth).")
    lines.append("- SHAP values explain the supervised classifier's behavior; they do **not prove causation**.")
    lines.append("- Priority levels are derived from risk class mapping: High Risk → High Priority, Medium Risk → Medium Priority, Low Risk → Low Priority.")
    lines.append("- Persistent priority labels require multiple observed years and repeated risk classifications.")
    lines.append("- Planning focus areas are transparent rule-based mappings, not clinical recommendations.")
    lines.append("")

    lines.append("## DSS Record Count")
    lines.append(f"- Total records: {len(dss_df)}")
    lines.append(f"- Unique district-years: {dss_df[['State','District','Year','source_dataset']].drop_duplicates().shape[0]}")
    lines.append("")

    lines.append("## Priority Distribution")
    priority_counts = dss_df["priority_level"].value_counts()
    for priority in ["High Priority", "Medium Priority", "Low Priority"]:
        count = priority_counts.get(priority, 0)
        lines.append(f"- {priority}: {count}")
    lines.append("")

    lines.append("Risk class to priority mapping:")
    for risk, priority in RISK_TO_PRIORITY.items():
        count = len(dss_df[dss_df["risk_class"] == risk])
        lines.append(f"  {risk} → {priority}: {count}")
    lines.append("")

    lines.append("## District Priority Summary")
    lines.append(f"- Total districts: {len(summary_df)}")
    for persistent in ["Persistent High Priority", "Persistent Medium Priority", "Persistent Low Priority", "Insufficient History"]:
        count = len(summary_df[summary_df["persistent_priority"] == persistent])
        lines.append(f"- {persistent}: {count}")
    lines.append("")

    lines.append("## Top Recurring Contributing Features")
    all_contributing = []
    for col in ["top_contributing_feature_1", "top_contributing_feature_2", "top_contributing_feature_3"]:
        all_contributing.extend(dss_df[col].tolist())
    feat_counts = pd.Series(all_contributing).value_counts()
    for feat, count in feat_counts.head(6).items():
        planning = FEATURE_PLANNING_MAP.get(feat, "Unknown")
        lines.append(f"- {feat}: appears {count} times → {planning}")
    lines.append("")

    lines.append("## Districts by Persistent Priority")
    for persistent in ["Persistent High Priority", "Persistent Medium Priority"]:
        persistent_districts = summary_df[summary_df["persistent_priority"] == persistent]
        lines.append(f"\n### {persistent} ({len(persistent_districts)} districts)")
        if len(persistent_districts) > 0:
            for _, row in persistent_districts.head(10).iterrows():
                lines.append(
                    f"- {row['State']}, {row['District']}: "
                    f"{row['high_risk_years']}H/{row['medium_risk_years']}M/{row['low_risk_years']}L "
                    f"out of {row['years_observed']} years, latest: {row['latest_risk_class']} ({row['latest_year']})"
                )
    lines.append("")

    lines.append("## Planning Rules")
    lines.append("")
    lines.append("| Feature | Planning Focus | Direction |")
    lines.append("|---------|----------------|-----------|")
    for _, row in rules_df.iterrows():
        lines.append(f"| {row['feature']} | {row['planning_focus']} | {row['feature_direction']} |")
    lines.append("")

    lines.append("## Methodology Limitations")
    lines.append("")
    lines.append("1. **Derived labels**: Risk classes are from K-Means, not clinical assessment.")
    lines.append("2. **Planning, not clinical**: Priority levels and planning focus are for resource planning, not individual medical decisions.")
    lines.append("3. **SHAP explanation**: Contributing features explain the model's classification behavior, not causal mechanisms.")
    lines.append("4. **Persistence ≠ severity**: Persistent priority labels indicate repeated observations, not clinical severity.")
    lines.append("5. **Correlated features**: SHAP may distribute importance among correlated features.")

    return "\n".join(lines)


def run_dss():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df = load_data()
    model, scaler = load_model_and_scaler()

    print("Computing SHAP values for all records...")
    shap_values = compute_shap_all(model, scaler, df)
    print(f"SHAP values computed: {shap_values.shape}")

    dss_df = build_district_decision_support(df, shap_values)
    dss_path = os.path.join(OUTPUT_DIR, "district_decision_support.csv")
    dss_df.to_csv(dss_path, index=False)
    print(f"Saved: district_decision_support.csv ({len(dss_df)} records)")

    summary_df = build_district_priority_summary(dss_df)
    summary_path = os.path.join(OUTPUT_DIR, "district_priority_summary.csv")
    summary_df.to_csv(summary_path, index=False)
    print(f"Saved: district_priority_summary.csv ({len(summary_df)} districts)")

    rules_df = generate_planning_rules_csv()
    rules_path = os.path.join(OUTPUT_DIR, "planning_rules.csv")
    rules_df.to_csv(rules_path, index=False)
    print(f"Saved: planning_rules.csv")

    report = generate_report(dss_df, summary_df, rules_df)
    report_path = os.path.join(OUTPUT_DIR, "decision_support_report.md")
    with open(report_path, "w") as f:
        f.write(report)
    print(f"Saved: decision_support_report.md")

    return dss_df, summary_df, rules_df


if __name__ == "__main__":
    run_dss()
