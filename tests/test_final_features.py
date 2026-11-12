import os
import pytest
import pandas as pd
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "feature_selection"))
from final_features import (
    create_final_features,
    FINAL_FEATURES,
    KEEP_COLUMNS,
    INPUT_PATH,
    OUTPUT_PATH,
)


class TestFinalFeaturesOutputs:
    def test_output_csv_exists(self):
        assert os.path.exists(OUTPUT_PATH), f"Output file not found: {OUTPUT_PATH}"

    def test_output_shape(self):
        df = pd.read_csv(OUTPUT_PATH)
        assert df.shape[0] == 8405, f"Expected 8405 rows, got {df.shape[0]}"

    def test_output_columns(self):
        df = pd.read_csv(OUTPUT_PATH)
        expected = KEEP_COLUMNS + FINAL_FEATURES
        assert list(df.columns) == expected, f"Columns mismatch: {list(df.columns)}"
        assert len(df.columns) == 10, f"Expected 10 columns, got {len(df.columns)}"

    def test_no_missing_values(self):
        df = pd.read_csv(OUTPUT_PATH)
        for col in FINAL_FEATURES:
            assert df[col].isna().sum() == 0, f"{col} has missing values"

    def test_values_in_range(self):
        df = pd.read_csv(OUTPUT_PATH)
        for col in FINAL_FEATURES:
            vals = df[col].dropna()
            assert (vals >= 0).all() and (vals <= 100).all(), f"{col} has values outside [0, 100]"

    def test_source_dataset_preserved(self):
        df = pd.read_csv(OUTPUT_PATH)
        assert set(df["source_dataset"].unique()) == {"D1", "D2"}
        assert len(df[df["source_dataset"] == "D1"]) == 6293
        assert len(df[df["source_dataset"] == "D2"]) == 2112

    def test_year_coverage(self):
        df = pd.read_csv(OUTPUT_PATH)
        years = sorted(df["Year"].unique())
        assert years == list(range(2008, 2020)), f"Year coverage mismatch: {years}"

    def test_no_duplicates(self):
        df = pd.read_csv(OUTPUT_PATH)
        dupes = df.duplicated(subset=["State", "District", "Year", "source_dataset"], keep=False)
        assert dupes.sum() == 0, f"Found {dupes.sum()} duplicates"

    def test_state_count(self):
        df = pd.read_csv(OUTPUT_PATH)
        assert df["State"].nunique() == 36, f"Expected 36 states, got {df['State'].nunique()}"


class TestFinalFeaturesContent:
    def test_severe_anemia_median_difference(self):
        df = pd.read_csv(OUTPUT_PATH)
        d1 = df[df["source_dataset"] == "D1"]["Severe_Anemia_Pct"]
        d2 = df[df["source_dataset"] == "D2"]["Severe_Anemia_Pct"]
        assert d1.median() < d2.median(), "D1 median should differ from D2 median"
        assert d2.median() / d1.median() > 5, "D2 median should be substantially higher"

    def test_feature_values_unchanged_from_selected(self):
        sel = pd.read_csv(INPUT_PATH)
        final = pd.read_csv(OUTPUT_PATH)
        for col in KEEP_COLUMNS + FINAL_FEATURES:
            pd.testing.assert_series_equal(
                final[col].reset_index(drop=True),
                sel[col].reset_index(drop=True),
                check_names=False,
            )


class TestCreateFinalFeatures:
    def test_creates_file(self):
        if os.path.exists(OUTPUT_PATH):
            os.remove(OUTPUT_PATH)
        result = create_final_features()
        assert os.path.exists(OUTPUT_PATH)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 8405

    def test_preprocessed_output_unchanged(self):
        pre = pd.read_csv("outputs/preprocessed_output.csv")
        assert pre.shape[0] == 8405
