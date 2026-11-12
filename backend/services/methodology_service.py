import os
from config import (
    CLUSTERING_METRICS_TXT,
    RISK_CLUSTERS_CSV,
    MODEL_COMPARISON_CSV,
    BEST_MODEL_METRICS_JSON,
)


def get_methodology():
    items = []

    clustering_metrics = {}
    if os.path.exists(CLUSTERING_METRICS_TXT):
        with open(CLUSTERING_METRICS_TXT) as f:
            for line in f:
                line = line.strip()
                if "Silhouette Score:" in line:
                    clustering_metrics["silhouette"] = float(line.split(":")[1].strip())
                elif "Davies-Bouldin Index:" in line:
                    clustering_metrics["davies_bouldin"] = float(line.split(":")[1].strip())
                elif "Calinski-Harabasz Index:" in line:
                    clustering_metrics["calinski_harabasz"] = float(line.split(":")[1].strip())

    clustering_info = (
        "Risk profiles derived using K-Means clustering (K=3, random_state=42, n_init=10) "
        "on StandardScaler-normalized features from the six validated maternal-health indicators."
    )
    if clustering_metrics:
        clustering_info += (
            f" Silhouette={clustering_metrics.get('silhouette', 'N/A')}, "
            f"DBI={clustering_metrics.get('davies_bouldin', 'N/A')}, "
            f"CHI={clustering_metrics.get('calinski_harabasz', 'N/A')}."
        )

    items.append({
        "category": "Risk Profile Derivation",
        "title": "K-Means Clustering",
        "value": clustering_info,
    })

    model_info = (
        "Supervised models (Logistic Regression, Decision Tree, Random Forest, XGBoost) were trained "
        "to classify district-year records into the K-Means-derived risk classes using the same six-feature space."
    )
    items.append({
        "category": "Supervised Classification",
        "title": "Model Comparison",
        "value": model_info,
    })

    selected_model_info = "Logistic Regression was selected as the best-performing model based on accuracy, F1, and ROC-AUC."
    try:
        with open(BEST_MODEL_METRICS_JSON) as f:
            import json
            best = json.load(f)
        selected_model_info = (
            f"Selected model: {best.get('model', 'Logistic Regression')} "
            f"(accuracy={best.get('accuracy', 'N/A'):.4f}, F1={best.get('f1_macro', 'N/A'):.4f}, "
            f"ROC-AUC={best.get('roc_auc_macro_ovr', 'N/A'):.4f})."
        )
    except Exception:
        pass
    items.append({
        "category": "Model Selection",
        "title": "Selected Model",
        "value": selected_model_info,
    })

    shap_info = (
        "SHAP (SHapley Additive exPlanations) values were computed on the Logistic Regression model "
        "to explain which features contributed to each classification decision. "
        "SHAP values indicate contribution direction and magnitude, not causation."
    )
    items.append({
        "category": "Explainability",
        "title": "SHAP Analysis",
        "value": shap_info,
    })

    dss_info = (
        "The Decision Support System maps risk classifications and SHAP contributing factors into "
        "district priority levels and planning focus areas using transparent rule-based mappings."
    )
    items.append({
        "category": "Decision Support",
        "title": "DSS Workflow",
        "value": dss_info,
    })

    feature_info = (
        "Six features used across all methods: ANC_First_Trimester_Pct, TT2_Booster_Pct, "
        "Severe_Anemia_Pct, Institutional_Delivery_Pct, PNC_48h_Pct, Obstetric_Complications_Pct."
    )
    items.append({
        "category": "Features",
        "title": "Feature Set",
        "value": feature_info,
    })

    sensitivity_info = (
        "Sensitivity analysis was performed excluding Severe_Anemia_Pct due to cross-dataset "
        "harmonization uncertainty (D1 median 3.6% vs D2 median 51.5%). "
        "Results: silhouette 0.231 (primary 0.238), indicating marginal differences."
    )
    items.append({
        "category": "Sensitivity Analysis",
        "title": "Feature Exclusion Test",
        "value": sensitivity_info,
    })

    disclaimer_info = (
        "Risk classes are derived from unsupervised clustering patterns and are not clinical diagnoses. "
        "SHAP values explain model behavior, not causal relationships. "
        "Planning priorities are public-health planning guidance, not individual medical recommendations."
    )
    items.append({
        "category": "Disclaimer",
        "title": "Important Notes",
        "value": disclaimer_info,
    })

    return {"items": items}
