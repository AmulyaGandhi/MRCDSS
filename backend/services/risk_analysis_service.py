import os
import pandas as pd
from config import (
    RISK_CLUSTERS_CSV,
    CLUSTER_PROFILES_CSV,
    CLUSTERING_METRICS_TXT,
    MODEL_COMPARISON_CSV,
    BEST_MODEL_METRICS_JSON,
    SENSITIVITY_METRICS_TXT,
    SENSITIVITY_CLUSTERS_CSV,
    SHAP_VALUES_TEST_CSV,
)
from services.data_loader import load_csv


def _evaluation_design() -> dict:
    df = load_csv(RISK_CLUSTERS_CSV)
    if df is None or "risk_class" not in df.columns:
        return {}
    from sklearn.model_selection import train_test_split

    train_idx, test_idx = train_test_split(
        df.index, test_size=0.2, random_state=42, stratify=df["risk_class"]
    )
    train_units = set(zip(df.loc[train_idx, "State"], df.loc[train_idx, "District"]))
    test_units = list(zip(df.loc[test_idx, "State"], df.loc[test_idx, "District"]))
    shared_records = sum(1 for key in test_units if key in train_units)
    test_records = len(test_units)
    return {
        "label_source": "K-Means-derived risk profiles",
        "selection_metric": "macro-F1",
        "test_records": test_records,
        "test_units": len(set(test_units)),
        "test_units_also_in_training": len({key for key in test_units if key in train_units}),
        "test_records_sharing_units_with_training": shared_records,
        "test_records_sharing_units_with_training_proportion": (
            round(shared_records / test_records, 4) if test_records else 0.0
        ),
        "grouped_or_temporal_validation_completed": False,
        "note": (
            "The 80/20 split is record-level. State–District units therefore appear in both training "
            "and test partitions, so the metrics measure reproducibility of K-Means-derived labels on "
            "seen units, not external or clinical predictive accuracy."
        ),
    }


def _shap_summary() -> dict:
    shap_df = load_csv(SHAP_VALUES_TEST_CSV)
    if shap_df is None or len(shap_df) == 0:
        return {}
    features = []
    for feature in shap_df.columns:
        values = pd.to_numeric(shap_df[feature], errors="coerce").dropna()
        if len(values) == 0:
            continue
        positive = values[values > 0]
        negative = values[values < 0]
        features.append({
            "feature": feature,
            "positive_mean": float(positive.mean()) if len(positive) else 0.0,
            "negative_mean": float(negative.mean()) if len(negative) else 0.0,
            "mean_abs_shap": float(values.abs().mean()),
            "positive_count": int(len(positive)),
            "negative_count": int(len(negative)),
        })
    features.sort(key=lambda item: item["mean_abs_shap"], reverse=True)
    return {
        "class_label": "High Risk",
        "records": int(len(shap_df)),
        "features": features,
        "note": (
            "Saved test-set SHAP values explain the Logistic Regression model output for the High Risk "
            "class. Positive values push toward High Risk; negative values push away from it. These are "
            "global test-set summaries, not signed explanations for an individual district-year record."
        ),
    }


def _sensitivity_analysis(metrics: dict, sensitivity_metrics: dict, clusters_df, sensitivity_df) -> dict:
    primary_high = 0
    sensitivity_high = 0
    changed = 0
    total = 0
    if clusters_df is not None and "risk_class" in clusters_df.columns:
        primary_high = int((clusters_df["risk_class"] == "High Risk").sum())
    if sensitivity_df is not None and "risk_class" in sensitivity_df.columns:
        sensitivity_high = int((sensitivity_df["risk_class"] == "High Risk").sum())
    if clusters_df is not None and sensitivity_df is not None:
        keys = ["State", "District", "Year", "source_dataset"]
        if all(k in clusters_df.columns for k in keys) and all(k in sensitivity_df.columns for k in keys):
            merged = clusters_df[keys + ["risk_class"]].merge(
                sensitivity_df[keys + ["risk_class"]],
                on=keys,
                suffixes=("_primary", "_sensitivity"),
            )
            total = int(len(merged))
            changed = int((merged["risk_class_primary"] != merged["risk_class_sensitivity"]).sum())
    return {
        "primary_features": 6,
        "sensitivity_features": 5,
        "primary_silhouette": metrics.get("silhouette_score", 0.238081),
        "sensitivity_silhouette": sensitivity_metrics.get("silhouette_score", 0.231),
        "primary_high_risk_size": primary_high,
        "sensitivity_high_risk_size": sensitivity_high,
        "risk_class_changed": changed,
        "risk_class_change_proportion": round(changed / total, 4) if total else 0.0,
        "risk_class_agreement": round(1 - changed / total, 4) if total else 0.0,
    }


def parse_clustering_metrics(path: str) -> dict:
    metrics = {}
    if not os.path.exists(path):
        return metrics
    with open(path) as f:
        for line in f:
            line = line.strip()
            if "Silhouette Score:" in line:
                metrics["silhouette_score"] = float(line.split(":")[1].strip())
            elif "Davies-Bouldin Index:" in line:
                metrics["davies_bouldin_index"] = float(line.split(":")[1].strip())
            elif "Calinski-Harabasz Index:" in line:
                metrics["calinski_harabasz_index"] = float(line.split(":")[1].strip())
    return metrics


def get_risk_analysis():
    clusters_df = load_csv(RISK_CLUSTERS_CSV)
    profiles_df = load_csv(CLUSTER_PROFILES_CSV)
    metrics = parse_clustering_metrics(CLUSTERING_METRICS_TXT)
    model_df = load_csv(MODEL_COMPARISON_CSV)
    with open(BEST_MODEL_METRICS_JSON) as f:
        import json
        best_model = json.load(f)

    risk_counts = {}
    if clusters_df is not None and "risk_class" in clusters_df.columns:
        risk_counts = {k: int(v) for k, v in clusters_df["risk_class"].value_counts().to_dict().items()}

    cluster_profiles = []
    if profiles_df is not None:
        for _, row in profiles_df.iterrows():
            profile = {
                "cluster_id": int(row.get("cluster_id", 0)),
                "cluster_size": int(row.get("cluster_size", 0)),
                "ANC_First_Trimester_Pct": float(row.get("ANC_First_Trimester_Pct_mean", 0)),
                "TT2_Booster_Pct": float(row.get("TT2_Booster_Pct_mean", 0)),
                "Severe_Anemia_Pct": float(row.get("Severe_Anemia_Pct_mean", 0)),
                "Institutional_Delivery_Pct": float(row.get("Institutional_Delivery_Pct_mean", 0)),
                "PNC_48h_Pct": float(row.get("PNC_48h_Pct_mean", 0)),
                "Obstetric_Complications_Pct": float(row.get("Obstetric_Complications_Pct_mean", 0)),
            }
            cluster_profiles.append(profile)

    model_comparison = []
    if model_df is not None:
        for _, row in model_df.iterrows():
            model = {
                "model": row.get("model", ""),
                "accuracy": float(row.get("accuracy", 0)),
                "precision": float(row.get("precision_macro", 0)),
                "recall": float(row.get("recall_macro", 0)),
                "f1": float(row.get("f1_macro", 0)),
                "roc_auc": float(row.get("roc_auc_macro_ovr", 0)),
            }
            model_comparison.append(model)

    confusion_matrix = []
    if best_model and "confusion_matrix" in best_model and "confusion_labels" in best_model:
        labels = best_model["confusion_labels"]
        matrix = best_model["confusion_matrix"]
        for i, label in enumerate(labels):
            row_data = {"actual": label}
            for j, col_label in enumerate(labels):
                key = f"predicted_{col_label.replace(' ', '_')}"
                row_data[key] = int(matrix[i][j])
            confusion_matrix.append(row_data)

    sensitivity_metrics = parse_clustering_metrics(SENSITIVITY_METRICS_TXT)
    sensitivity_df = load_csv(SENSITIVITY_CLUSTERS_CSV)

    return {
        "risk_counts": risk_counts,
        "cluster_profiles": cluster_profiles,
        "clustering_metrics": {
            "silhouette_score": metrics.get("silhouette_score", 0),
            "davies_bouldin_index": metrics.get("davies_bouldin_index", 0),
            "calinski_harabasz_index": metrics.get("calinski_harabasz_index", 0),
        },
        "clustering_notes": {
            "k_selection": "K=3 was fixed for the Low/Medium/High design; a full K-selection diagnostic was not used.",
            "silhouette_interpretation": (
                "A silhouette near 0.24 indicates weak-to-moderate separation, not strong, well-separated clusters."
            ),
            "label_sensitivity": (
                "Removing Severe Anemia changes the risk class of a large share of district-year records, "
                "so cluster labels should be treated as analytically sensitive."
            ),
        },
        "model_comparison": model_comparison,
        "confusion_matrix": confusion_matrix,
        "evaluation_design": _evaluation_design(),
        "shap_summary": _shap_summary(),
        "sensitivity_analysis": _sensitivity_analysis(metrics, sensitivity_metrics, clusters_df, sensitivity_df),
    }
