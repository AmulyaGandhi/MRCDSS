import os
import pickle
import pytest
import pandas as pd
import numpy as np
import sys
from sklearn.preprocessing import StandardScaler
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "classification"))
from evaluate_models import load_data, evaluate_model, load_model, load_scaler, FEATURES, TARGET
from train_models import load_data as train_load, split_data, MODEL_CONFIGS, FEATURES as TRAIN_FEATURES


CLASSIFICATION_DIR = "outputs/classification"
MODELS_DIR = "models"


class TestClassificationOutputs:
    def test_model_comparison_exists(self):
        assert os.path.exists(os.path.join(CLASSIFICATION_DIR, "model_comparison.csv"))

    def test_classification_report_exists(self):
        assert os.path.exists(os.path.join(CLASSIFICATION_DIR, "classification_report.md"))

    def test_best_model_metrics_exists(self):
        assert os.path.exists(os.path.join(CLASSIFICATION_DIR, "best_model_metrics.json"))

    def test_confusion_matrices_exist(self):
        for name in ["logistic_regression", "decision_tree", "random_forest", "xgboost"]:
            path = os.path.join(CLASSIFICATION_DIR, "confusion_matrices", f"{name}_confusion_matrix.png")
            assert os.path.exists(path), f"Missing: {path}"

    def test_models_saved(self):
        for name in ["logistic_regression", "decision_tree", "random_forest", "xgboost"]:
            path = os.path.join(MODELS_DIR, f"{name}.pkl")
            assert os.path.exists(path), f"Missing model: {path}"


class TestModelComparisonCSV:
    def test_has_all_models(self):
        df = pd.read_csv(os.path.join(CLASSIFICATION_DIR, "model_comparison.csv"))
        assert len(df) == 4
        expected_models = ["Logistic Regression", "Decision Tree", "Random Forest", "XGBoost"]
        for m in expected_models:
            assert m in df["model"].values, f"Missing model: {m}"

    def test_has_required_metrics(self):
        df = pd.read_csv(os.path.join(CLASSIFICATION_DIR, "model_comparison.csv"))
        required = ["model", "accuracy", "precision_macro", "recall_macro", "f1_macro"]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_all_metrics_in_range(self):
        df = pd.read_csv(os.path.join(CLASSIFICATION_DIR, "model_comparison.csv"))
        for _, row in df.iterrows():
            assert 0 <= row["accuracy"] <= 1
            assert 0 <= row["precision_macro"] <= 1
            assert 0 <= row["recall_macro"] <= 1
            assert 0 <= row["f1_macro"] <= 1


class TestBestModel:
    def test_best_model_exists(self):
        path = os.path.join(CLASSIFICATION_DIR, "best_model_metrics.json")
        assert os.path.exists(path)
        with open(path) as f:
            best = pickle.load(f) if False else __import__("json").load(f)
        assert "model" in best
        assert "f1_macro" in best

    def test_best_model_is_logistic_regression(self):
        path = os.path.join(CLASSIFICATION_DIR, "best_model_metrics.json")
        with open(path) as f:
            import json
            best = json.load(f)
        assert best["model"] == "Logistic Regression"
        assert best["f1_macro"] >= 0.99

    def test_best_model_has_per_class_metrics(self):
        path = os.path.join(CLASSIFICATION_DIR, "best_model_metrics.json")
        with open(path) as f:
            import json
            best = json.load(f)
        for cls in ["High Risk", "Low Risk", "Medium Risk"]:
            assert cls in best["per_class"], f"Missing per-class metrics for {cls}"
            for metric in ["precision", "recall", "f1", "support"]:
                assert metric in best["per_class"][cls], f"Missing {metric} for {cls}"


class TestClassificationReport:
    def test_report_mentions_derived_labels(self):
        with open(os.path.join(CLASSIFICATION_DIR, "classification_report.md")) as f:
            content = f.read()
        assert "derived" in content.lower() or "DERIVED" in content

    def test_report_has_all_models(self):
        with open(os.path.join(CLASSIFICATION_DIR, "classification_report.md")) as f:
            content = f.read()
        for model in ["Logistic Regression", "Decision Tree", "Random Forest", "XGBoost"]:
            assert model in content, f"Missing model in report: {model}"

    def test_report_has_methodological_limitations(self):
        with open(os.path.join(CLASSIFICATION_DIR, "classification_report.md")) as f:
            content = f.read()
        assert "limitation" in content.lower() or "Limitation" in content


class TestDataSplit:
    def test_train_test_split(self):
        X, y = train_load()
        X_train, X_test, y_train, y_test = split_data(X, y)
        assert len(X_train) == 6724
        assert len(X_test) == 1681
        assert len(X_train) + len(X_test) == 8405

    def test_stratified_split(self):
        X, y = train_load()
        X_train, X_test, y_train, y_test = split_data(X, y)
        train_dist = y_train.value_counts(normalize=True).sort_index().to_dict()
        test_dist = y_test.value_counts(normalize=True).sort_index().to_dict()
        for cls in train_dist:
            assert abs(train_dist[cls] - test_dist[cls]) < 0.01, f"Class {cls} distribution mismatch"

    def test_no_target_leakage(self):
        df = pd.read_csv(os.path.join("outputs", "risk_classification", "district_year_risk_clusters.csv"))
        feature_cols = FEATURES
        assert "risk_class" not in feature_cols
        assert "State" not in feature_cols
        assert "District" not in feature_cols
        assert "Year" not in feature_cols
        assert "source_dataset" not in feature_cols
        assert "cluster_id" not in feature_cols


class TestModelEvaluation:
    def test_evaluate_logistic_regression(self):
        df = pd.read_csv(os.path.join("outputs", "risk_classification", "district_year_risk_clusters.csv"))
        X_train, X_test, y_train, y_test = split_data(df[FEATURES], df[TARGET])
        model = load_model("Logistic Regression")
        scaler = load_scaler("Logistic Regression")
        metrics = evaluate_model(model, scaler, X_test, y_test, "Logistic Regression")
        assert metrics["accuracy"] > 0.9
        assert metrics["f1_macro"] > 0.9

    def test_evaluate_decision_tree(self):
        df = pd.read_csv(os.path.join("outputs", "risk_classification", "district_year_risk_clusters.csv"))
        X_train, X_test, y_train, y_test = split_data(df[FEATURES], df[TARGET])
        model = load_model("Decision Tree")
        scaler = load_scaler("Decision Tree")
        metrics = evaluate_model(model, scaler, X_test, y_test, "Decision Tree")
        assert metrics["accuracy"] > 0.9

    def test_evaluate_random_forest(self):
        df = pd.read_csv(os.path.join("outputs", "risk_classification", "district_year_risk_clusters.csv"))
        X_train, X_test, y_train, y_test = split_data(df[FEATURES], df[TARGET])
        model = load_model("Random Forest")
        scaler = load_scaler("Random Forest")
        metrics = evaluate_model(model, scaler, X_test, y_test, "Random Forest")
        assert metrics["accuracy"] > 0.9

    def test_evaluate_xgboost(self):
        df = pd.read_csv(os.path.join("outputs", "risk_classification", "district_year_risk_clusters.csv"))
        X_train, X_test, y_train, y_test = split_data(df[FEATURES], df[TARGET])
        model = load_model("XGBoost")
        scaler = load_scaler("XGBoost")
        metrics = evaluate_model(model, scaler, X_test, y_test, "XGBoost")
        assert metrics["accuracy"] > 0.9

    def test_confusion_matrix_shape(self):
        df = pd.read_csv(os.path.join("outputs", "risk_classification", "district_year_risk_clusters.csv"))
        X_train, X_test, y_train, y_test = split_data(df[FEATURES], df[TARGET])
        model = load_model("Logistic Regression")
        scaler = load_scaler("Logistic Regression")
        metrics = evaluate_model(model, scaler, X_test, y_test, "Logistic Regression")
        cm = np.array(metrics["confusion_matrix"])
        assert cm.shape == (3, 3)
        assert cm.sum() == len(y_test)


class TestPreprocessingCorrectness:
    def test_scaler_fitted_on_train(self):
        path = os.path.join(MODELS_DIR, "logistic_regression_scaler.pkl")
        assert os.path.exists(path)
        with open(path, "rb") as f:
            scaler = pickle.load(f)
        assert hasattr(scaler, "mean_")
        assert hasattr(scaler, "scale_")

    def test_no_data_leakage_in_scaler(self):
        df = pd.read_csv(os.path.join("outputs", "risk_classification", "district_year_risk_clusters.csv"))
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            df[FEATURES], df[TARGET], test_size=0.2, random_state=42, stratify=df[TARGET]
        )
        scaler = StandardScaler()
        scaler.fit(X_train)
        with open(os.path.join(MODELS_DIR, "logistic_regression_scaler.pkl"), "rb") as f:
            saved_scaler = pickle.load(f)
        np.testing.assert_array_almost_equal(scaler.mean_, saved_scaler.mean_, decimal=10)
        np.testing.assert_array_almost_equal(scaler.scale_, saved_scaler.scale_, decimal=10)


class TestReproducibility:
    def test_same_predictions_on_reload(self):
        df = pd.read_csv(os.path.join("outputs", "risk_classification", "district_year_risk_clusters.csv"))
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            df[FEATURES], df[TARGET], test_size=0.2, random_state=42, stratify=df[TARGET]
        )
        model = load_model("Random Forest")
        scaler = load_scaler("Random Forest")
        X_eval = scaler.transform(X_test) if scaler is not None else X_test
        y_pred1 = model.predict(X_eval)
        model2 = load_model("Random Forest")
        y_pred2 = model2.predict(X_eval)
        assert np.array_equal(y_pred1, y_pred2)
