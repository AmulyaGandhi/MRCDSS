import os
import sys
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "preprocessing"))

from config import OUTPUT_CSV, DATASET1_PATH, DATASET2_PATH
import preprocess


@pytest.fixture(scope="module")
def pipeline_results():
    return preprocess.run_pipeline()


@pytest.fixture(scope="module")
def cleaned_df(pipeline_results):
    return pd.read_csv(OUTPUT_CSV)


class TestPipelineOutputs:
    def test_output_csv_exists(self, pipeline_results):
        assert os.path.exists(OUTPUT_CSV), f"Output CSV not found at {OUTPUT_CSV}"

    def test_output_csv_not_empty(self, cleaned_df):
        assert len(cleaned_df) > 0, "Cleaned DataFrame is empty"

    def test_has_source_dataset_column(self, cleaned_df):
        assert "source_dataset" in cleaned_df.columns, "Missing source_dataset column"

    def test_source_datasets(self, cleaned_df):
        sources = cleaned_df["source_dataset"].unique()
        assert "D1" in sources, "D1 not in source_dataset"
        assert "D2" in sources, "D2 not in source_dataset"


class TestDataShape:
    def test_shape_tuple(self, pipeline_results):
        shape = pipeline_results["shape"]
        assert isinstance(shape, tuple), "Shape should be a tuple"
        assert len(shape) == 2, "Shape should have 2 dimensions"
        assert shape[0] > 0, "Row count should be positive"
        assert shape[1] > 0, "Column count should be positive"

    def test_rows_at_least_one_thousand(self, pipeline_results):
        assert pipeline_results["shape"][0] >= 1000, "Expected at least 1000 rows"


class TestMissingValues:
    def test_missing_before_is_int(self, pipeline_results):
        val = pipeline_results["missing_before"]
        assert isinstance(val, int), "Missing before should be int"
        assert val >= 0, "Missing before should be non-negative"

    def test_remaining_missing_equals_zero(self, pipeline_results):
        assert pipeline_results["remaining_missing"] == 0, f"Remaining missing: {pipeline_results['remaining_missing']}"

    def test_total_imputed_positive(self, pipeline_results):
        assert pipeline_results["total_imputed"] > 0, "Should have imputed some values"


class TestInvalidPercentages:
    def test_invalid_pct_is_dict(self, pipeline_results):
        assert isinstance(pipeline_results["invalid_pct"], dict), "Invalid pct should be dict"

    def test_no_invalid_in_cleaned(self, cleaned_df):
        for col in cleaned_df.columns:
            if "(%)" in col or "%" in col:
                vals = pd.to_numeric(cleaned_df[col], errors="coerce")
                invalid = ((vals < 0) | (vals > 100)).sum()
                assert invalid == 0, f"{col} has {invalid} invalid percentage values"


class TestDeduplication:
    def test_duplicates_is_int(self, pipeline_results):
        val = pipeline_results["duplicates"]
        assert isinstance(val, int), "Duplicates should be int"

    def test_no_exact_duplicates(self, cleaned_df):
        dup_cols = ["State", "District", "Year", "source_dataset"]
        assert cleaned_df.duplicated(subset=dup_cols, keep=False).sum() == 0, "Duplicates remain"


class TestCoverage:
    def test_coverage_has_years(self, pipeline_results):
        cov = pipeline_results["coverage"]
        assert "D1_years" in cov, "Missing D1_years"
        assert "D2_years" in cov, "Missing D2_years"

    def test_d1_has_2016(self, pipeline_results):
        assert 2016 in pipeline_results["coverage"]["D1_years"], "D1 should have 2016"

    def test_d2_has_2017(self, pipeline_results):
        assert 2017 in pipeline_results["coverage"]["D2_years"], "D2 should have 2017"

    def test_d1_has_2008(self, pipeline_results):
        assert 2008 in pipeline_results["coverage"]["D1_years"], "D1 should have 2008"

    def test_d2_has_2019(self, pipeline_results):
        assert 2019 in pipeline_results["coverage"]["D2_years"], "D2 should have 2019"

    def test_d1_districts_positive(self, pipeline_results):
        assert pipeline_results["coverage"]["D1_num_districts"] > 0, "D1 should have districts"

    def test_d2_districts_positive(self, pipeline_results):
        assert pipeline_results["coverage"]["D2_num_districts"] > 0, "D2 should have districts"


class TestRawDataIntegrity:
    def test_d1_not_modified(self):
        df = pd.read_csv(DATASET1_PATH)
        assert len(df) == 6293, f"D1 row count changed: {len(df)}"

    def test_d2_not_modified(self):
        df = pd.read_csv(DATASET2_PATH)
        assert len(df) == 2112, f"D2 row count changed: {len(df)}"


class TestNegativeValues:
    def test_no_negatives_in_pct(self, cleaned_df):
        pct_cols = [c for c in cleaned_df.columns if "(%)" in c or "%" in c]
        for col in pct_cols:
            vals = pd.to_numeric(cleaned_df[col], errors="coerce")
            neg = (vals < 0).sum()
            assert neg == 0, f"{col} has {neg} negative values"


class TestYearFormat:
    def test_year_is_numeric(self, cleaned_df):
        vals = pd.to_numeric(cleaned_df["Year"], errors="coerce")
        assert vals.notna().all(), "Year has non-numeric values"

    def test_no_year_gap_anomalies(self, cleaned_df):
        years = sorted(cleaned_df["Year"].dropna().unique())
        assert 2008 in years, "2008 not in years"
        assert 2019 in years, "2019 not in years"
