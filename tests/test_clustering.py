import os
import pytest
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "clustering"))
from risk_clustering import (
    load_data,
    standardize,
    run_clustering,
    build_profiles,
    compute_centroids,
    compute_metrics,
    rank_clusters_by_risk,
    assign_risk_classes,
    run_clustering_pipeline,
    FEATURES,
    KEEP_COLUMNS,
    RISK_CLASSES,
    INPUT_PATH,
    OUTPUT_PATH,
    RANDOM_STATE,
    N_INIT,
    K,
)


class TestOutputFiles:
    def test_main_output_exists(self):
        assert os.path.exists(OUTPUT_PATH)

    def test_cluster_profiles_exists(self):
        assert os.path.exists("outputs/risk_classification/cluster_profiles.csv")

    def test_cluster_centroids_exists(self):
        assert os.path.exists("outputs/risk_classification/cluster_centroids.csv")

    def test_clustering_metrics_exists(self):
        assert os.path.exists("outputs/risk_classification/clustering_metrics.txt")

    def test_report_exists(self):
        assert os.path.exists("outputs/risk_classification/risk_classification_report.md")


class TestMainOutput:
    def test_output_shape(self):
        df = pd.read_csv(OUTPUT_PATH)
        assert df.shape[0] == 8405, f"Expected 8405 rows, got {df.shape[0]}"

    def test_output_columns(self):
        df = pd.read_csv(OUTPUT_PATH)
        expected = KEEP_COLUMNS + FEATURES + ["cluster_id", "risk_class"]
        assert list(df.columns) == expected, f"Columns mismatch: {list(df.columns)}"

    def test_no_duplicates(self):
        df = pd.read_csv(OUTPUT_PATH)
        dupes = df.duplicated(subset=["State", "District", "Year", "source_dataset"], keep=False)
        assert dupes.sum() == 0

    def test_no_missing_cluster(self):
        df = pd.read_csv(OUTPUT_PATH)
        assert df["cluster_id"].isna().sum() == 0

    def test_no_missing_risk_class(self):
        df = pd.read_csv(OUTPUT_PATH)
        assert df["risk_class"].isna().sum() == 0

    def test_exactly_three_clusters(self):
        df = pd.read_csv(OUTPUT_PATH)
        assert set(df["cluster_id"].unique()) == {0, 1, 2}

    def test_risk_classes_valid(self):
        df = pd.read_csv(OUTPUT_PATH)
        valid = {"Low Risk", "Medium Risk", "High Risk"}
        actual = set(df["risk_class"].unique())
        assert actual == valid, f"Invalid risk classes: {actual}"

    def test_every_row_has_risk_class(self):
        df = pd.read_csv(OUTPUT_PATH)
        for rc in RISK_CLASSES:
            assert rc in df["risk_class"].values, f"Missing risk class: {rc}"

    def test_feature_values_unchanged(self):
        sel = pd.read_csv(INPUT_PATH)
        df = pd.read_csv(OUTPUT_PATH)
        for col in KEEP_COLUMNS + FEATURES:
            pd.testing.assert_series_equal(
                df[col].reset_index(drop=True),
                sel[col].reset_index(drop=True),
                check_names=False,
            )

    def test_source_dataset_preserved(self):
        df = pd.read_csv(OUTPUT_PATH)
        assert set(df["source_dataset"].unique()) == {"D1", "D2"}


class TestClusteringFunctionality:
    def test_load_data(self):
        df = load_data()
        assert len(df) == 8405

    def test_standardize(self):
        df = load_data()
        X_scaled, scaler = standardize(df)
        assert X_scaled.shape == (8405, 6)
        assert abs(X_scaled.mean().mean()) < 0.1
        assert abs(X_scaled.std().mean() - 1.0) < 0.1

    def test_run_clustering(self):
        df = load_data()
        X_scaled, _ = standardize(df)
        labels, km = run_clustering(X_scaled)
        assert len(labels) == 8405
        assert set(labels) == {0, 1, 2}
        assert hasattr(km, "cluster_centers_")

    def test_build_profiles(self):
        df = load_data()
        X_scaled, _ = standardize(df)
        labels, _ = run_clustering(X_scaled)
        profiles, df_tagged = build_profiles(df, labels)
        assert len(profiles) == 3
        assert "cluster_id" in profiles.columns
        assert "cluster_size" in profiles.columns
        for feat in FEATURES:
            assert f"{feat}_mean" in profiles.columns
            assert f"{feat}_median" in profiles.columns

    def test_compute_centroids(self):
        df = load_data()
        X_scaled, scaler = standardize(df)
        centroids, km = compute_centroids(X_scaled, scaler, df)
        assert centroids.shape[0] == 3
        assert centroids.shape[1] == 12
        assert centroids.index.name == "cluster_id"

    def test_compute_metrics(self):
        df = load_data()
        X_scaled, _ = standardize(df)
        labels, _ = run_clustering(X_scaled)
        metrics = compute_metrics(X_scaled, labels)
        assert "silhouette_score" in metrics
        assert "davies_bouldin_index" in metrics
        assert "calinski_harabasz_index" in metrics
        assert metrics["silhouette_score"] >= -1
        assert metrics["silhouette_score"] <= 1
        assert metrics["davies_bouldin_index"] >= 0
        assert metrics["calinski_harabasz_index"] > 0

    def test_rank_clusters_by_risk(self):
        df = load_data()
        X_scaled, _ = standardize(df)
        labels, _ = run_clustering(X_scaled)
        profiles, _ = build_profiles(df, labels)
        ranking = rank_clusters_by_risk(profiles)
        assert len(ranking) == 3
        cluster_ids = [r[0] for r in ranking]
        assert set(cluster_ids) == {0, 1, 2}

    def test_assign_risk_classes(self):
        df = load_data()
        X_scaled, _ = standardize(df)
        labels, _ = run_clustering(X_scaled)
        profiles, df_tagged = build_profiles(df, labels)
        ranking = rank_clusters_by_risk(profiles)
        df_classified = assign_risk_classes(df_tagged, profiles, ranking)
        assert "risk_class" in df_classified.columns
        assert set(df_classified["risk_class"].unique()) == set(RISK_CLASSES)


class TestPipelineIntegration:
    def test_pipeline_runs(self):
        result = run_clustering_pipeline()
        assert len(result) == 4

    def test_preprocessed_unchanged(self):
        pre = pd.read_csv("outputs/preprocessed_output.csv")
        assert pre.shape[0] == 8405

    def test_final_features_unchanged(self):
        final = pd.read_csv("outputs/selected_features/final_model_features.csv")
        assert final.shape[0] == 8405


class TestReproducibility:
    def test_same_result_on_rerun(self):
        df1 = load_data()
        X_scaled1, scaler1 = standardize(df1)
        labels1, _ = run_clustering(X_scaled1)

        df2 = load_data()
        X_scaled2, scaler2 = standardize(df2)
        labels2, _ = run_clustering(X_scaled2)

        assert np.array_equal(labels1, labels2), "Clustering not reproducible"
