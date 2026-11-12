import os
os.environ.setdefault("DYLD_LIBRARY_PATH", "/opt/homebrew/opt/libomp/lib")
os.environ["DYLD_LIBRARY_PATH"] = "/opt/homebrew/opt/libomp/lib:" + os.environ.get("DYLD_LIBRARY_PATH", "")

from sklearn.preprocessing import LabelEncoder
import pickle
import time
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_PATH = os.path.join(BASE_DIR, "outputs", "risk_classification", "district_year_risk_clusters.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")
RANDOM_STATE = 42
TEST_SIZE = 0.2

FEATURES = [
    "ANC_First_Trimester_Pct",
    "TT2_Booster_Pct",
    "Severe_Anemia_Pct",
    "Institutional_Delivery_Pct",
    "PNC_48h_Pct",
    "Obstetric_Complications_Pct",
]

TARGET = "risk_class"

MODEL_CONFIGS = {
    "Logistic Regression": {
        "pipeline": Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)),
        ]),
        "requires_scaling": True,
    },
    "Decision Tree": {
        "pipeline": DecisionTreeClassifier(random_state=RANDOM_STATE),
        "requires_scaling": False,
    },
    "Random Forest": {
        "pipeline": RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1),
        "requires_scaling": False,
    },
    "XGBoost": {
        "pipeline": None,
        "requires_scaling": False,
    },
}


def load_data():
    df = pd.read_csv(INPUT_PATH)
    X = df[FEATURES]
    y = df[TARGET]
    return X, y


def split_data(X, y):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    return X_train, X_test, y_train, y_test


def get_model(name):
    config = MODEL_CONFIGS[name]
    if name == "XGBoost":
        from xgboost import XGBClassifier
        pipeline = XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=RANDOM_STATE,
            n_jobs=-1,
            eval_metric="mlogloss",
        )
        return pipeline, config["requires_scaling"]
    return config["pipeline"], config["requires_scaling"]


def train_all_models():
    os.makedirs(MODELS_DIR, exist_ok=True)
    X, y = load_data()
    X_train, X_test, y_train, y_test = split_data(X, y)

    train_size = len(X_train)
    test_size = len(X_test)
    class_dist_train = y_train.value_counts().to_dict()
    class_dist_test = y_test.value_counts().to_dict()

    print(f"Training set: {train_size} rows")
    print(f"Test set: {test_size} rows")
    print(f"Train class distribution: {class_dist_train}")
    print(f"Test class distribution: {class_dist_test}")

    results = {
        "train_size": train_size,
        "test_size": test_size,
        "class_distribution_train": class_dist_train,
        "class_distribution_test": class_dist_test,
        "models": {},
    }

    for name in MODEL_CONFIGS:
        print(f"\nTraining {name}...")
        model, needs_scaling = get_model(name)

        if needs_scaling:
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            X_fit_train, y_fit_train = X_train_scaled, y_train
            X_fit_test = X_test_scaled
        else:
            X_fit_train, y_fit_train = X_train, y_train
            X_fit_test = X_test

        is_xgb = name == "XGBoost"
        label_encoder = None
        if is_xgb:
            label_encoder = LabelEncoder()
            y_fit_train = label_encoder.fit_transform(y_fit_train)
            y_fit_test_encoded = label_encoder.transform(y_test)
        else:
            y_fit_test_encoded = y_test

        start = time.time()
        model.fit(X_fit_train, y_fit_train)
        train_time = time.time() - start

        y_pred_encoded = model.predict(X_fit_test)
        if is_xgb and label_encoder is not None:
            y_pred = label_encoder.inverse_transform(y_pred_encoded)
        else:
            y_pred = y_pred_encoded

        y_prob = None
        if hasattr(model, "predict_proba"):
            y_prob = model.predict_proba(X_fit_test)
            if is_xgb and label_encoder is not None:
                pass

        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision_macro": precision_score(y_test, y_pred, average="macro"),
            "recall_macro": recall_score(y_test, y_pred, average="macro"),
            "f1_macro": f1_score(y_test, y_pred, average="macro"),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
            "train_time_seconds": round(train_time, 4),
        }

        if y_prob is not None:
            from sklearn.metrics import roc_auc_score
            try:
                metrics["roc_auc_macro_ovr"] = roc_auc_score(y_test, y_prob, multi_class="ovr", average="macro")
            except Exception:
                metrics["roc_auc_macro_ovr"] = None

        y_report = classification_report(y_test, y_pred, output_dict=True)
        metrics["per_class"] = {}
        for cls in ["High Risk", "Low Risk", "Medium Risk"]:
            if cls in y_report:
                metrics["per_class"][cls] = {
                    "precision": y_report[cls].get("precision", 0),
                    "recall": y_report[cls].get("recall", 0),
                    "f1": y_report[cls].get("f1-score", 0),
                    "support": y_report[cls].get("support", 0),
                }

        model_path = os.path.join(MODELS_DIR, f"{name.replace(' ', '_').lower()}.pkl")
        scaler_path = None
        if needs_scaling:
            scaler_path = os.path.join(MODELS_DIR, f"{name.replace(' ', '_').lower()}_scaler.pkl")
            with open(scaler_path, "wb") as f:
                pickle.dump(scaler, f)
        with open(model_path, "wb") as f:
            pickle.dump(model, f)

        results["models"][name] = {
            "metrics": metrics,
            "model_path": model_path,
            "scaler_path": scaler_path,
        }
        print(f"  Accuracy: {metrics['accuracy']:.4f}, F1(macro): {metrics['f1_macro']:.4f}")
        print(f"  Precision(macro): {metrics['precision_macro']:.4f}, Recall(macro): {metrics['recall_macro']:.4f}")
        print(f"  Train time: {metrics['train_time_seconds']:.4f}s")

    results_path = os.path.join(MODELS_DIR, "training_results.pkl")
    with open(results_path, "wb") as f:
        pickle.dump(results, f)

    return results, X_train, X_test, y_train, y_test


if __name__ == "__main__":
    results, X_train, X_test, y_train, y_test = train_all_models()
    print("\nAll models trained and saved.")