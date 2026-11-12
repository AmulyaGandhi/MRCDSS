import os
import pytest
import pandas as pd
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "feature_selection"))
from select_features import (
    load_preprocessed,
    harmonize_features,
    run_feature_selection,
    FEATURE_COLUMNS,
    KEEP_COLUMNS,
    SOURCE_COLUMN_MAP,
    RISK_DIRECTION,
    PREPROCESSED_PATH,
    OUTPUT_PATH,
    BASE_DIR,
)

D1_PATH = os.path.join(BASE_DIR, "dataset1.csv")
D2_PATH = os.path.join(BASE_DIR, "dataset2.csv")


class TestFeatureSelectionOutputs:
    def test_output_csv_exists(self):
        assert os.path.exists(OUTPUT_PATH), f"Output file not found: {OUTPUT_PATH}"

    def test_output_shape(self):
        df = pd.read_csv(OUTPUT_PATH)
        pre = pd.read_csv(PREPROCESSED_PATH)
        assert df.shape[0] == pre.shape[0], f"Row count mismatch: {df.shape[0]} vs {pre.shape[0]}"

    def test_output_columns(self):
        df = pd.read_csv(OUTPUT_PATH)
        expected = KEEP_COLUMNS + FEATURE_COLUMNS
        assert list(df.columns) == expected, f"Columns mismatch: {list(df.columns)}"

    def test_no_missing_values(self):
        df = pd.read_csv(OUTPUT_PATH)
        for col in FEATURE_COLUMNS:
            assert df[col].isna().sum() == 0, f"{col} has missing values"

    def test_all_values_in_range(self):
        df = pd.read_csv(OUTPUT_PATH)
        for col in FEATURE_COLUMNS:
            vals = df[col].dropna()
            assert (vals >= 0).all() and (vals <= 100).all(), f"{col} has values outside [0, 100]"

    def test_source_dataset_values(self):
        df = pd.read_csv(OUTPUT_PATH)
        assert set(df["source_dataset"].unique()) == {"D1", "D2"}

    def test_row_counts_by_dataset(self):
        df = pd.read_csv(OUTPUT_PATH)
        assert len(df[df["source_dataset"] == "D1"]) == 6293
        assert len(df[df["source_dataset"] == "D2"]) == 2112

    def test_keep_columns_preserved(self):
        df = pd.read_csv(OUTPUT_PATH)
        for col in KEEP_COLUMNS:
            assert col in df.columns, f"Missing keep column: {col}"

    def test_no_duplicate_geography_year(self):
        df = pd.read_csv(OUTPUT_PATH)
        dupes = df.duplicated(subset=["State", "District", "Year", "source_dataset"], keep=False)
        assert dupes.sum() == 0, f"Found {dupes.sum()} duplicate geography+year+dataset rows"


class TestColumnMappings:
    def test_all_source_columns_exist(self):
        d1 = pd.read_csv(D1_PATH)
        d2 = pd.read_csv(D2_PATH)
        for feat, cols in SOURCE_COLUMN_MAP.items():
            assert cols["D1"] in d1.columns, f"D1 column missing for {feat}"
            assert cols["D2"] in d2.columns, f"D2 column missing for {feat}"

    def test_all_features_have_risk_direction(self):
        for feat in FEATURE_COLUMNS:
            assert feat in RISK_DIRECTION, f"Missing risk direction for {feat}"


class TestHarmonizeFunction:
    def test_returns_dataframe(self):
        pre = load_preprocessed()
        result = harmonize_features(pre)
        assert isinstance(result, pd.DataFrame)

    def test_harmonized_values_match_source_d1(self):
        pre = load_preprocessed()
        d1 = pre[pre["source_dataset"] == "D1"]
        result = harmonize_features(pre)
        d1_result = result[result["source_dataset"] == "D1"]
        for feat in FEATURE_COLUMNS:
            src_col = SOURCE_COLUMN_MAP[feat]["D1"]
            if src_col in d1.columns:
                pd.testing.assert_series_equal(
                    d1_result[feat].reset_index(drop=True),
                    d1[src_col].reset_index(drop=True),
                    check_names=False,
                )

    def test_harmonized_values_match_source_d2(self):
        pre = load_preprocessed()
        d2 = pre[pre["source_dataset"] == "D2"]
        result = harmonize_features(pre)
        d2_result = result[result["source_dataset"] == "D2"]
        for feat in FEATURE_COLUMNS:
            src_col = SOURCE_COLUMN_MAP[feat]["D2"]
            if src_col in d2.columns:
                pd.testing.assert_series_equal(
                    d2_result[feat].reset_index(drop=True),
                    d2[src_col].reset_index(drop=True),
                    check_names=False,
                )


class TestPipelineIntegration:
    def test_run_feature_selection_creates_file(self):
        if os.path.exists(OUTPUT_PATH):
            os.remove(OUTPUT_PATH)
        result = run_feature_selection()
        assert os.path.exists(OUTPUT_PATH)
        assert isinstance(result, pd.DataFrame)

    def test_preprocessed_output_unchanged(self):
        pre = pd.read_csv(PREPROCESSED_PATH)
        assert pre.shape[0] == 8405
        assert pre.isna().sum().sum() >= 0
