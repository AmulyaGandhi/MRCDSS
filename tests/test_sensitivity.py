import os
import pytest
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "clustering"))
from sensitivity import run_experiment, FEATURES_5, OUTPUT_DIR


SENSITIVITY_DIR = "outputs/risk_classification/sensitivity_without_severe_anemia"


class TestSensitivityOutputFiles:
    def test_main_output_exists(self):
        assert os.path.exists(os.path.join(SENSITIVITY_DIR, "district_year_risk_clusters.csv"))

    def test_cluster_profiles_exists(self):
        assert os.path.exists(os.path.join(SENSITIVITY_DIR, "cluster_profiles.csv"))

    def test_cluster_centroids_exists(self):
        assert os.path.exists(os.path.join(SENSITIVITY_DIR, "cluster_centroids.csv"))

    def test_clustering_metrics_exists(self):
        assert os.path.exists(os.path.join(SENSITIVITY_DIR, "clustering_metrics.txt"))

    def test_sensitivity_report_exists(self):
        assert os.path.exists(os.path.join(SENSITIVITY_DIR, "sensitivity_report.md"))


class TestSensitivityOutputIntegrity:
    def test_output_shape(self):
        df = pd.read_csv(os.path.join(SENSITIVITY_DIR, "district_year_risk_clusters.csv"))
        assert df.shape[0] == 8405

    def test_columns(self):
        df = pd.read_csv(os.path.join(SENSITIVITY_DIR, "district_year_risk_clusters.csv"))
        expected = ["State", "District", "Year", "source_dataset"] + FEATURES_5 + ["cluster_id", "risk_class"]
        assert list(df.columns) == expected

    def test_no_duplicates(self):
        df = pd.read_csv(os.path.join(SENSITIVITY_DIR, "district_year_risk_clusters.csv"))
        assert df.duplicated(subset=["State", "District", "Year", "source_dataset"]).sum() == 0

    def test_three_clusters(self):
        df = pd.read_csv(os.path.join(SENSITIVITY_DIR, "district_year_risk_clusters.csv"))
        assert set(df["cluster_id"].unique()) == {0, 1, 2}

    def test_no_missing_assignments(self):
        df = pd.read_csv(os.path.join(SENSITIVITY_DIR, "district_year_risk_clusters.csv"))
        assert df["cluster_id"].isna().sum() == 0
        assert df["risk_class"].isna().sum() == 0

    def test_risk_classes_valid(self):
        df = pd.read_csv(os.path.join(SENSITIVITY_DIR, "district_year_risk_clusters.csv"))
        assert set(df["risk_class"].unique()) == {"Low Risk", "Medium Risk", "High Risk"}


class TestSensitivityFeatureExclusion:
    def test_severe_anemia_not_in_features(self):
        df = pd.read_csv(os.path.join(SENSITIVITY_DIR, "district_year_risk_clusters.csv"))
        assert "Severe_Anemia_Pct" not in df.columns

    def test_other_features_present(self):
        df = pd.read_csv(os.path.join(SENSITIVITY_DIR, "district_year_risk_clusters.csv"))
        for feat in FEATURES_5:
            assert feat in df.columns


class TestSensitivityComparison:
    def test_similar_row_count(self):
        df6 = pd.read_csv("outputs/risk_classification/district_year_risk_clusters.csv")
        df5 = pd.read_csv(os.path.join(SENSITIVITY_DIR, "district_year_risk_clusters.csv"))
        assert len(df6) == len(df5) == 8405

    def test_different_cluster_assignments(self):
        df6 = pd.read_csv("outputs/risk_classification/district_year_risk_clusters.csv")
        df5 = pd.read_csv(os.path.join(SENSITIVITY_DIR, "district_year_risk_clusters.csv"))
        same = (df6["cluster_id"] == df5["cluster_id"]).sum()
        assert same < len(df6) * 0.9, "Clusters too similar — feature exclusion had minimal effect"

    def test_different_risk_distributions(self):
        df6 = pd.read_csv("outputs/risk_classification/district_year_risk_clusters.csv")
        df5 = pd.read_csv(os.path.join(SENSITIVITY_DIR, "district_year_risk_clusters.csv"))
        dist6 = df6["risk_class"].value_counts().sort_index().to_dict()
        dist5 = df5["risk_class"].value_counts().sort_index().to_dict()
        assert dist6 != dist5, "Risk distributions should differ between 6F and 5F models"


class TestSensitivityReproducibility:
    def test_same_result_on_rerun(self):
        df1, _, _, _ = run_experiment(FEATURES_5, "/tmp/sens_test1")
        df2, _, _, _ = run_experiment(FEATURES_5, "/tmp/sens_test2")
        assert np.array_equal(df1["cluster_id"].values, df2["cluster_id"].values)

    def test_original_6f_unchanged(self):
        df6 = pd.read_csv("outputs/risk_classification/district_year_risk_clusters.csv")
        assert len(df6) == 8405
        assert df6["cluster_id"].nunique() == 3
