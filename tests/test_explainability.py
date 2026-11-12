import os
import pytest
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "explainability"))
from shap_analysis import (
    load_model,
    load_test_data,
    get_shap_explainer,
    compute_global_importance,
    get_class_specific_insights,
    get_local_explanations,
    FEATURES,
)


OUTPUT_DIR = "outputs/explainability"


class TestOutputFiles:
    def test_shap_summary_exists(self):
        assert os.path.exists(os.path.join(OUTPUT_DIR, "shap_summary.png"))

    def test_shap_bar_exists(self):
        assert os.path.exists(os.path.join(OUTPUT_DIR, "shap_bar.png"))

    def test_feature_importance_exists(self):
        assert os.path.exists(os.path.join(OUTPUT_DIR, "feature_importance.csv"))

    def test_shap_values_exists(self):
        assert os.path.exists(os.path.join(OUTPUT_DIR, "shap_values_test.csv"))

    def test_report_exists(self):
        assert os.path.exists(os.path.join(OUTPUT_DIR, "explainability_report.md"))


class TestFeatureImportance:
    def test_all_6_features_present(self):
        fi = pd.read_csv(os.path.join(OUTPUT_DIR, "feature_importance.csv"))
        assert len(fi) == 6
        assert set(fi["feature"]) == set(FEATURES)

    def test_features_ranked_by_importance(self):
        fi = pd.read_csv(os.path.join(OUTPUT_DIR, "feature_importance.csv"))
        values = fi["mean_abs_shap"].tolist()
        assert values == sorted(values, reverse=True), "Not ranked descending"

    def test_no_negative_importance(self):
        fi = pd.read_csv(os.path.join(OUTPUT_DIR, "feature_importance.csv"))
        assert (fi["mean_abs_shap"] >= 0).all()


class TestSHAPValues:
    def test_correct_shape(self):
        model, scaler = load_model()
        X_train, X_test, y_train, y_test, df_test = load_test_data()
        explainer = get_shap_explainer(model, scaler, X_train)
        X_test_scaled = scaler.transform(X_test)
        shap_values, importance = compute_global_importance(explainer, X_test_scaled)
        assert shap_values.shape == (len(X_test), 6), f"Expected (1681, 6), got {shap_values.shape}"

    def test_no_nan_inf(self):
        sv = pd.read_csv(os.path.join(OUTPUT_DIR, "shap_values_test.csv"))
        assert sv.shape == (1681, 6)
        assert not sv.isna().any().any(), "NaN values found"
        assert not np.isinf(sv.select_dtypes(include=[np.number]).values).any(), "Inf values found"

    def test_feature_names_match(self):
        sv = pd.read_csv(os.path.join(OUTPUT_DIR, "shap_values_test.csv"))
        assert list(sv.columns) == FEATURES

    def test_all_test_observations_have_explanation(self):
        sv = pd.read_csv(os.path.join(OUTPUT_DIR, "shap_values_test.csv"))
        assert len(sv) == 1681, f"Expected 1681 test observations, got {len(sv)}"


class TestReportContent:
    def test_mentions_derived_labels(self):
        with open(os.path.join(OUTPUT_DIR, "explainability_report.md")) as f:
            content = f.read()
        assert "derived" in content.lower() or "K-Means" in content

    def test_mentions_not_causal(self):
        with open(os.path.join(OUTPUT_DIR, "explainability_report.md")) as f:
            content = f.read()
        assert "causal" in content.lower() or "NOT" in content

    def test_has_global_importance(self):
        with open(os.path.join(OUTPUT_DIR, "explainability_report.md")) as f:
            content = f.read()
        assert "Global Feature Importance" in content

    def test_has_class_specific(self):
        with open(os.path.join(OUTPUT_DIR, "explainability_report.md")) as f:
            content = f.read()
        for cls in ["Low Risk", "Medium Risk", "High Risk"]:
            assert cls in content, f"Missing class: {cls}"

    def test_has_local_explanations(self):
        with open(os.path.join(OUTPUT_DIR, "explainability_report.md")) as f:
            content = f.read()
        assert "representative" in content.lower() or "Local" in content or "Local SHAP" in content


class TestClassSpecificInsights:
    def test_all_classes_have_insights(self):
        model, scaler = load_model()
        X_train, X_test, y_train, y_test, df_test = load_test_data()
        X_train_scaled = scaler.transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        explainer = get_shap_explainer(model, scaler, X_train)
        shap_values, importance = compute_global_importance(explainer, X_test_scaled)
        insights = get_class_specific_insights(importance, shap_values, X_test_scaled, y_test)
        for cls in ["Low Risk", "Medium Risk", "High Risk"]:
            assert cls in insights, f"Missing insights for {cls}"
            assert "top_features" in insights[cls]
            assert "n_samples" in insights[cls]
            assert len(insights[cls]["top_features"]) >= 1


class TestLocalExplanations:
    def test_three_examples(self):
        model, scaler = load_model()
        X_train, X_test, y_train, y_test, df_test = load_test_data()
        X_train_scaled = scaler.transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        explainer = get_shap_explainer(model, scaler, X_train)
        examples = get_local_explanations(explainer, X_test_scaled, X_test, y_test, df_test)
        assert len(examples) == 3, f"Expected 3 examples, got {len(examples)}"

    def test_examples_have_required_fields(self):
        model, scaler = load_model()
        X_train, X_test, y_train, y_test, df_test = load_test_data()
        X_train_scaled = scaler.transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        explainer = get_shap_explainer(model, scaler, X_train)
        examples = get_local_explanations(explainer, X_test_scaled, X_test, y_test, df_test)
        for ex in examples:
            assert "State" in ex
            assert "District" in ex
            assert "Year" in ex
            assert "predicted_class" in ex
            assert "top_contributions" in ex
            for cls in ["Low Risk", "Medium Risk", "High Risk"]:
                if ex["predicted_class"] == cls:
                    break
            else:
                pytest.fail(f"Invalid predicted class: {ex['predicted_class']}")
            for c in ex["top_contributions"]:
                assert "feature" in c
                assert "shap_value" in c
                assert "feature_value" in c

    def test_no_nan_in_contributions(self):
        model, scaler = load_model()
        X_train, X_test, y_train, y_test, df_test = load_test_data()
        X_train_scaled = scaler.transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        explainer = get_shap_explainer(model, scaler, X_train)
        examples = get_local_explanations(explainer, X_test_scaled, X_test, y_test, df_test)
        for ex in examples:
            for c in ex["top_contributions"]:
                assert not np.isnan(c["shap_value"]), f"NaN SHAP value in {ex}"
                assert not np.isinf(c["shap_value"]), f"Inf SHAP value in {ex}"
