import os
os.environ.setdefault("DYLD_LIBRARY_PATH", "/opt/homebrew/opt/libomp/lib")
os.environ["DYLD_LIBRARY_PATH"] = "/opt/homebrew/opt/libomp/lib:" + os.environ.get("DYLD_LIBRARY_PATH", "")

from sklearn.preprocessing import LabelEncoder
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score,
)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_PATH = os.path.join(BASE_DIR, "outputs", "risk_classification", "district_year_risk_clusters.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "classification")
RANDOM_STATE = 42
FEATURES = [
    "ANC_First_Trimester_Pct",
    "TT2_Booster_Pct",
    "Severe_Anemia_Pct",
    "Institutional_Delivery_Pct",
    "PNC_48h_Pct",
    "Obstetric_Complications_Pct",
]
TARGET = "risk_class"
MODEL_NAMES = ["Logistic Regression", "Decision Tree", "Random Forest", "XGBoost"]


def load_data():
    df = pd.read_csv(INPUT_PATH)
    X = df[FEATURES]
    y = df[TARGET]
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    return X_train, X_test, y_train, y_test


def load_model(name):
    path = os.path.join(MODELS_DIR, f"{name.replace(' ', '_').lower()}.pkl")
    with open(path, "rb") as f:
        return pickle.load(f)


def load_scaler(name):
    path = os.path.join(MODELS_DIR, f"{name.replace(' ', '_').lower()}_scaler.pkl")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    return None


def evaluate_model(model, scaler, X_test, y_test, name):
    if scaler is not None:
        X_eval = scaler.transform(X_test)
    else:
        X_eval = X_test

    is_xgb = name == "XGBoost"
    label_encoder = None
    if is_xgb:
        label_encoder = LabelEncoder()
        label_encoder.fit(y_test)

    y_pred_encoded = model.predict(X_eval)
    if is_xgb and label_encoder is not None:
        y_pred = label_encoder.inverse_transform(y_pred_encoded)
    else:
        y_pred = y_pred_encoded

    y_prob = None
    if hasattr(model, "predict_proba"):
        y_prob = model.predict_proba(X_eval)

    if is_xgb and label_encoder is not None:
        y_test_eval = label_encoder.transform(y_test)
    else:
        y_test_eval = y_test

    metrics = {
        "model": name,
        "accuracy": accuracy_score(y_test, y_pred),
        "precision_macro": precision_score(y_test, y_pred, average="macro"),
        "recall_macro": recall_score(y_test, y_pred, average="macro"),
        "f1_macro": f1_score(y_test, y_pred, average="macro"),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    }

    if y_prob is not None:
        try:
            metrics["roc_auc_macro_ovr"] = roc_auc_score(
                y_test_eval, y_prob, multi_class="ovr", average="macro"
            )
        except Exception:
            metrics["roc_auc_macro_ovr"] = None

    y_report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    metrics["per_class"] = {}
    for cls in ["High Risk", "Low Risk", "Medium Risk"]:
        if cls in y_report:
            metrics["per_class"][cls] = {
                "precision": round(y_report[cls].get("precision", 0), 6),
                "recall": round(y_report[cls].get("recall", 0), 6),
                "f1": round(y_report[cls].get("f1-score", 0), 6),
                "support": int(y_report[cls].get("support", 0)),
            }

    metrics["confusion_labels"] = sorted(y_test.unique().tolist())
    return metrics


def plot_confusion_matrices(all_metrics):
    os.makedirs(os.path.join(OUTPUT_DIR, "confusion_matrices"), exist_ok=True)
    for m in all_metrics:
        name_clean = m["model"].replace(" ", "_").lower()
        cm = np.array(m["confusion_matrix"])
        labels = m.get("confusion_labels", ["High Risk", "Low Risk", "Medium Risk"])

        fig, ax = plt.subplots(figsize=(6, 5))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=labels, yticklabels=labels, ax=ax)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        ax.set_title(f"Confusion Matrix: {m['model']}")
        plt.tight_layout()
        fig.savefig(os.path.join(OUTPUT_DIR, "confusion_matrices", f"{name_clean}_confusion_matrix.png"))
        plt.close(fig)
        print(f"  Saved: {name_clean}_confusion_matrix.png")


def select_best_model(all_metrics):
    best = None
    best_f1 = -1
    for m in all_metrics:
        if m["f1_macro"] > best_f1:
            best_f1 = m["f1_macro"]
            best = m
    return best


def generate_report(all_metrics, best_model, train_size, test_size, class_dist_train, class_dist_test):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    comparison_rows = []
    for m in all_metrics:
        train_time = None
        try:
            with open(os.path.join(MODELS_DIR, "training_results.pkl"), "rb") as f:
                train_results = pickle.load(f)
            train_time = train_results["models"].get(m["model"], {}).get("metrics", {}).get("train_time_seconds")
        except Exception:
            pass
        comparison_rows.append({
            "model": m["model"],
            "accuracy": round(m["accuracy"], 6),
            "precision_macro": round(m["precision_macro"], 6),
            "recall_macro": round(m["recall_macro"], 6),
            "f1_macro": round(m["f1_macro"], 6),
            "roc_auc_macro_ovr": round(m.get("roc_auc_macro_ovr", 0), 6) if m.get("roc_auc_macro_ovr") else None,
            "train_time_seconds": train_time,
        })
    comparison_df = pd.DataFrame(comparison_rows)
    comparison_df.to_csv(os.path.join(OUTPUT_DIR, "model_comparison.csv"), index=False)
    print("Saved: model_comparison.csv")

    best_metrics_path = os.path.join(OUTPUT_DIR, "best_model_metrics.json")
    with open(best_metrics_path, "w") as f:
        json.dump(best_model, f, indent=2, default=str)
    print("Saved: best_model_metrics.json")

    report_lines = []
    report_lines.append("# Supervised Classification of Derived District-Year Risk Profiles")
    report_lines.append("")
    report_lines.append("**Methodology**: Supervised classification of derived district-year risk profiles")
    report_lines.append("**Note**: K-Means risk classes are DERIVED labels, not independent clinical ground truth.")
    report_lines.append("")
    report_lines.append("## Data Split")
    report_lines.append(f"- Training size: {train_size}")
    report_lines.append(f"- Test size: {test_size}")
    report_lines.append(f"- Split: 80/20 stratified, random_state=42")
    report_lines.append(f"- Class distribution (train): {class_dist_train}")
    report_lines.append(f"- Class distribution (test): {class_dist_test}")
    report_lines.append("")
    report_lines.append("## Model Comparison (Test Set)")
    report_lines.append("")
    report_lines.append("| Model | Accuracy | Precision (macro) | Recall (macro) | F1 (macro) | ROC-AUC (macro OVR) |")
    report_lines.append("|-------|----------|-------------------|----------------|------------|---------------------|")
    for m in all_metrics:
        roc_val = m.get("roc_auc_macro_ovr")
        roc_str = f"{roc_val:.4f}" if roc_val is not None else "N/A"
        report_lines.append(
            f"| {m['model']} | {m['accuracy']:.4f} | {m['precision_macro']:.4f} | {m['recall_macro']:.4f} | {m['f1_macro']:.4f} | {roc_str} |"
        )
    report_lines.append("")

    report_lines.append("## Per-Class Metrics")
    for m in all_metrics:
        report_lines.append(f"\n### {m['model']}")
        report_lines.append("| Class | Precision | Recall | F1 | Support |")
        report_lines.append("|-------|-----------|--------|----|---------|")
        for cls in ["High Risk", "Low Risk", "Medium Risk"]:
            if cls in m.get("per_class", {}):
                pc = m["per_class"][cls]
                report_lines.append(
                    f"| {cls} | {pc['precision']:.4f} | {pc['recall']:.4f} | {pc['f1']:.4f} | {pc['support']} |"
                )
        report_lines.append("")

    report_lines.append("## Confusion Matrices")
    for m in all_metrics:
        report_lines.append(f"\n### {m['model']}")
        cm = np.array(m["confusion_matrix"])
        labels = m.get("confusion_labels", ["High Risk", "Low Risk", "Medium Risk"])
        report_lines.append(f"Predicted: {labels}")
        report_lines.append(f"Actual rows: {labels}")
        for i, label in enumerate(labels):
            row_vals = "  ".join(str(v) for v in cm[i])
            report_lines.append(f"  {label}: {row_vals}")
        report_lines.append("")

    report_lines.append("## Best Model")
    report_lines.append(f"**Best model**: {best_model['model']}")
    report_lines.append(f"**Reason**: Highest macro F1-score ({best_model['f1_macro']:.4f}), indicating best balanced performance across all three risk classes.")
    report_lines.append("")
    report_lines.append("## Methodological Limitations")
    report_lines.append("1. **Derived labels**: Risk classes are from K-Means clustering, not clinical ground truth. Model performance measures consistency with unsupervised profiles, not clinical accuracy.")
    report_lines.append("2. **Class imbalance**: Risk classes have unequal sizes, which may bias accuracy toward majority classes.")
    report_lines.append("3. **Feature-target leakage potential**: Features and risk labels are derived from the same underlying data, which may inflate performance metrics.")
    report_lines.append("4. **No external validation**: Performance is measured on a split of the same dataset. External validation is needed for generalizability.")
    report_lines.append("5. **No clinical claims**: Results should not be interpreted as clinical prediction accuracy.")

    report_path = os.path.join(OUTPUT_DIR, "classification_report.md")
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))
    print(f"Saved: classification_report.md")


def run_evaluation():
    X_train, X_test, y_train, y_test = load_data()

    train_size = len(X_train)
    test_size = len(X_test)
    class_dist_train = y_train.value_counts().to_dict()
    class_dist_test = y_test.value_counts().to_dict()

    all_metrics = []
    for name in MODEL_NAMES:
        print(f"\nEvaluating {name}...")
        model = load_model(name)
        scaler = load_scaler(name)
        metrics = evaluate_model(model, scaler, X_test, y_test, name)
        all_metrics.append(metrics)
        print(f"  Accuracy: {metrics['accuracy']:.4f}, F1(macro): {metrics['f1_macro']:.4f}")

    plot_confusion_matrices(all_metrics)
    best = select_best_model(all_metrics)

    generate_report(all_metrics, best, train_size, test_size, class_dist_train, class_dist_test)

    return all_metrics, best


if __name__ == "__main__":
    all_metrics, best = run_evaluation()
    print(f"\nBest model: {best['model']} (F1 macro: {best['f1_macro']:.4f})")