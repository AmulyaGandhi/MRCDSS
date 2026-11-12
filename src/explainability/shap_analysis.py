import os
import pickle
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATA_PATH = os.path.join(BASE_DIR, "outputs", "risk_classification", "district_year_risk_clusters.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "explainability")

FEATURES = [
    "ANC_First_Trimester_Pct",
    "TT2_Booster_Pct",
    "Severe_Anemia_Pct",
    "Institutional_Delivery_Pct",
    "PNC_48h_Pct",
    "Obstetric_Complications_Pct",
]

FEATURE_LABELS = [
    "ANC First Trimester %",
    "TT2 Booster %",
    "Severe Anemia %",
    "Institutional Delivery %",
    "PNC 48h %",
    "Obstetric Complications %",
]

RANDOM_STATE = 42
TEST_SIZE = 0.2
RISK_CLASS_INDEX = {"High Risk": 0, "Low Risk": 1, "Medium Risk": 2}


def load_model():
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


def load_test_data():
    df = pd.read_csv(DATA_PATH)
    from sklearn.model_selection import train_test_split
    X = df[FEATURES]
    y = df["risk_class"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    df_test = df.loc[X_test.index].copy()
    return X_train, X_test, y_train, y_test, df_test


def get_shap_explainer(model, scaler, X_train):
    import shap
    X_train_scaled = scaler.transform(X_train)
    explainer = shap.LinearExplainer(model, X_train_scaled, feature_names=FEATURES)
    return explainer


def compute_global_importance(explainer, X_test_scaled):
    shap_values_all = explainer.shap_values(X_test_scaled)
    if isinstance(shap_values_all, list):
        high_risk_idx = RISK_CLASS_INDEX["High Risk"]
        shap_target = shap_values_all[high_risk_idx]
    else:
        shap_values = np.array(shap_values_all)
        if shap_values.ndim == 3:
            high_risk_idx = RISK_CLASS_INDEX["High Risk"]
            shap_target = shap_values[:, :, high_risk_idx]
        else:
            shap_target = shap_values
    mean_abs = np.abs(shap_target).mean(axis=0)
    importance = pd.DataFrame({
        "feature": FEATURES,
        "mean_abs_shap": mean_abs,
    }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
    return shap_target, importance


import shap as shap_lib


def create_plots(shap_values, X_test_scaled):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    shap_lib.summary_plot(shap_values, X_test_scaled, feature_names=FEATURES, show=False)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "shap_summary.png"), dpi=150, bbox_inches="tight")
    plt.close()

    mean_abs = np.abs(shap_values).mean(axis=0)
    sorted_idx = np.argsort(mean_abs)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(range(len(sorted_idx)), mean_abs[sorted_idx], color="steelblue")
    ax.set_yticks(range(len(sorted_idx)))
    ax.set_yticklabels([FEATURES[i] for i in sorted_idx])
    ax.set_xlabel("Mean |SHAP| value")
    ax.set_title("SHAP Feature Importance (Bar)")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "shap_bar.png"), dpi=150, bbox_inches="tight")
    plt.close()


def get_class_specific_insights(importance_df, shap_values, X_test_scaled, y_test):
    insights = {}
    for risk_class in ["Low Risk", "Medium Risk", "High Risk"]:
        mask = y_test == risk_class
        if mask.sum() == 0:
            continue
        class_shap = shap_values[mask]
        class_mean_abs = np.abs(class_shap).mean(axis=0)
        sorted_idx = np.argsort(class_mean_abs)[::-1]
        top_features = []
        for idx in sorted_idx[:3]:
            direction = "protective" if FEATURES[idx] in [
                "ANC_First_Trimester_Pct", "TT2_Booster_Pct",
                "Institutional_Delivery_Pct", "PNC_48h_Pct"
            ] else "risk"
            top_features.append({
                "feature": FEATURES[idx],
                "mean_abs_shap": class_mean_abs[idx],
                "direction": direction,
            })
        insights[risk_class] = {
            "top_features": top_features,
            "n_samples": int(mask.sum()),
        }
    return insights


def get_representative_examples(X_test, y_test, df_test):
    examples = []
    for risk_class in ["Low Risk", "Medium Risk", "High Risk"]:
        mask = y_test == risk_class
        if mask.sum() == 0:
            continue
        subset_idx = np.where(mask)[0]
        sample_idx = subset_idx[0]
        example = {
            "State": df_test.iloc[sample_idx]["State"],
            "District": df_test.iloc[sample_idx]["District"],
            "Year": int(df_test.iloc[sample_idx]["Year"]),
            "predicted_class": risk_class,
            "features": {f: float(df_test.iloc[sample_idx][f]) for f in FEATURES},
        }
        examples.append(example)
    return examples


def get_local_explanations(explainer, X_test_scaled, X_test, y_test, df_test, n_examples=1):
    examples = []
    for risk_class in ["Low Risk", "Medium Risk", "High Risk"]:
        mask = y_test == risk_class
        if mask.sum() == 0:
            continue
        subset_idx = np.where(mask)[0]
        sample_idx = subset_idx[0]
        shap_values_all = explainer.shap_values(X_test_scaled[sample_idx:sample_idx+1])
        class_idx = RISK_CLASS_INDEX[risk_class]
        if isinstance(shap_values_all, list):
            shap_values = shap_values_all[class_idx]
        else:
            shap_values = np.array(shap_values_all)
            if shap_values.ndim == 3:
                shap_values = shap_values[:, :, class_idx]

        contributions = []
        for i, feat in enumerate(FEATURES):
            contributions.append({
                "feature": feat,
                "shap_value": float(shap_values[0][i]),
                "feature_value": float(X_test.iloc[sample_idx][feat]),
            })
        contributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

        example = {
            "State": df_test.iloc[sample_idx]["State"],
            "District": df_test.iloc[sample_idx]["District"],
            "Year": int(df_test.iloc[sample_idx]["Year"]),
            "predicted_class": risk_class,
            "top_contributions": contributions[:3],
        }
        examples.append(example)
    return examples


def run_shap_analysis():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    model, scaler = load_model()
    X_train, X_test, y_train, y_test, df_test = load_test_data()

    explainer = get_shap_explainer(model, scaler, X_train)

    X_train_scaled = scaler.transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    shap_values, importance_df = compute_global_importance(explainer, X_test_scaled)
    print("Global Feature Importance (mean |SHAP|):")
    for _, row in importance_df.iterrows():
        print(f"  {row['feature']}: {row['mean_abs_shap']:.6f}")

    create_plots(shap_values, X_test_scaled)
    print("Saved: shap_summary.png, shap_bar.png")

    class_insights = get_class_specific_insights(importance_df, shap_values, X_test_scaled, y_test)
    print("\nClass-Specific Insights:")
    for cls, info in class_insights.items():
        print(f"  {cls} (n={info['n_samples']}):")
        for ft in info["top_features"]:
            print(f"    {ft['feature']}: {ft['mean_abs_shap']:.4f} ({ft['direction']})")

    local_explanations = get_local_explanations(explainer, X_test_scaled, X_test, y_test, df_test)
    print("\nLocal Explanations:")
    for ex in local_explanations:
        print(f"  {ex['State']}, {ex['District']} ({ex['Year']}) - {ex['predicted_class']}:")
        for c in ex["top_contributions"]:
            print(f"    {c['feature']}: SHAP={c['shap_value']:.4f}, value={c['feature_value']:.2f}")

    shap_values_df = pd.DataFrame(shap_values, columns=FEATURES)
    shap_values_df.to_csv(os.path.join(OUTPUT_DIR, "shap_values_test.csv"), index=False)
    importance_df.to_csv(os.path.join(OUTPUT_DIR, "feature_importance.csv"), index=False)
    print("\nSaved: shap_values_test.csv, feature_importance.csv")

    report_lines = generate_report(importance_df, class_insights, local_explanations)
    report_path = os.path.join(OUTPUT_DIR, "explainability_report.md")
    with open(report_path, "w") as f:
        f.write(report_lines)
    print(f"Saved: explainability_report.md")

    return importance_df, shap_values, class_insights, local_explanations


def generate_report(importance_df, class_insights, local_explanations):
    lines = []
    lines.append("# SHAP Explainability Analysis")
    lines.append("")
    lines.append("**Model**: Logistic Regression (best-performing supervised classifier)")
    lines.append("**Purpose**: Explain why the model assigns each district-year to its derived risk class.")
    lines.append("")
    lines.append("## Important Interpretation Notes")
    lines.append("")
    lines.append("- Risk labels originate from **K-Means clustering** (derived, not clinical ground truth).")
    lines.append("- SHAP explains the **Logistic Regression model's classification behavior**.")
    lines.append("- This analysis shows which features **contributed to the model's classification**.")
    lines.append("- This is **NOT** clinical causal inference. Features do not clinically cause risk.")
    lines.append("- K-Means risk classes are the target; the supervised classifier reproduces these derived profiles.")
    lines.append("")

    lines.append("## Global Feature Importance")
    lines.append("")
    lines.append("Ranked by mean absolute SHAP value on the test set:")
    lines.append("")
    lines.append("| Rank | Feature | Mean |SHAP| |")
    lines.append("|------|---------|------------|")
    for i, (_, row) in enumerate(importance_df.iterrows()):
        lines.append(f"| {i+1} | {row['feature']} | {row['mean_abs_shap']:.6f} |")
    lines.append("")

    lines.append("## Class-Specific Interpretation")
    lines.append("")
    for cls in ["Low Risk", "Medium Risk", "High Risk"]:
        if cls not in class_insights:
            continue
        info = class_insights[cls]
        lines.append(f"### {cls}")
        lines.append(f"(n={info['n_samples']} district-years)")
        lines.append("")
        lines.append("Features most contributing to the model's classification for this class:")
        lines.append("")
        lines.append("| Feature | Mean |SHAP| | Contribution Direction |")
        lines.append("|---------|------------|------------------------|")
        for ft in info["top_features"]:
            lines.append(f"| {ft['feature']} | {ft['mean_abs_shap']:.4f} | {ft['direction']} |")
        lines.append("")

    lines.append("## Representative District-Year Explanations")
    lines.append("")
    lines.append("Local SHAP explanations for one example from each risk class:")
    lines.append("")

    for ex in local_explanations:
        lines.append(f"### {ex['predicted_class']}")
        lines.append(f"**Location**: {ex['State']}, {ex['District']}")
        lines.append(f"**Year**: {ex['Year']}")
        lines.append("")
        lines.append("Top contributing features to the model's classification:")
        lines.append("")
        lines.append("| Feature | Feature Value | SHAP Value | Direction |")
        lines.append("|---------|--------------|------------|-----------|")
        for c in ex["top_contributions"]:
            direction = "increases risk" if c["shap_value"] > 0 else "decreases risk"
            lines.append(
                f"| {c['feature']} | {c['feature_value']:.2f} | {c['shap_value']:.4f} | {direction} |"
            )
        lines.append("")

    lines.append("## Methodology Limitations")
    lines.append("")
    lines.append("1. **Derived labels**: Risk classes originate from K-Means, not clinical assessment.")
    lines.append("2. **Model explanation, not causal inference**: SHAP values indicate contribution to the model's classification, not clinical causation.")
    lines.append("3. **Logistic Regression**: Linear model explanations may not capture non-linear relationships that tree-based models would find.")
    lines.append("4. **Test set only**: Explanations are for the 20% held-out test set (1,681 district-years).")
    lines.append("5. **Feature correlation**: SHAP may distribute importance among correlated features, affecting individual attribution.")

    return "\n".join(lines)


if __name__ == "__main__":
    run_shap_analysis()
