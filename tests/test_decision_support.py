import os
import pytest
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "decision_support"))
from planning_rules import (
    FEATURES,
    FEATURE_PLANNING_MAP,
    RISK_TO_PRIORITY,
)

DSS_DIR = "outputs/decision_support"


class TestOutputFiles:
    def test_district_decision_support_exists(self):
        assert os.path.exists(os.path.join(DSS_DIR, "district_decision_support.csv"))

    def test_district_priority_summary_exists(self):
        assert os.path.exists(os.path.join(DSS_DIR, "district_priority_summary.csv"))

    def test_planning_rules_exists(self):
        assert os.path.exists(os.path.join(DSS_DIR, "planning_rules.csv"))

    def test_decision_support_report_exists(self):
        assert os.path.exists(os.path.join(DSS_DIR, "decision_support_report.md"))


class TestDSSRecordCount:
    def test_all_8405_records(self):
        df = pd.read_csv(os.path.join(DSS_DIR, "district_decision_support.csv"))
        assert len(df) == 8405

    def test_required_columns(self):
        df = pd.read_csv(os.path.join(DSS_DIR, "district_decision_support.csv"))
        required = [
            "State", "District", "Year", "source_dataset",
            "risk_class", "priority_level",
            "top_contributing_feature_1", "top_contributing_feature_2", "top_contributing_feature_3",
            "planning_focus_1", "planning_focus_2", "planning_focus_3",
        ]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_no_duplicates(self):
        df = pd.read_csv(os.path.join(DSS_DIR, "district_decision_support.csv"))
        dupes = df.duplicated(subset=["State", "District", "Year", "source_dataset"]).sum()
        assert dupes == 0


class TestPriorityMapping:
    def test_high_risk_to_high_priority(self):
        df = pd.read_csv(os.path.join(DSS_DIR, "district_decision_support.csv"))
        high = df[df["risk_class"] == "High Risk"]
        assert set(high["priority_level"].unique()) == {"High Priority"}

    def test_medium_risk_to_medium_priority(self):
        df = pd.read_csv(os.path.join(DSS_DIR, "district_decision_support.csv"))
        medium = df[df["risk_class"] == "Medium Risk"]
        assert set(medium["priority_level"].unique()) == {"Medium Priority"}

    def test_low_risk_to_low_priority(self):
        df = pd.read_csv(os.path.join(DSS_DIR, "district_decision_support.csv"))
        low = df[df["risk_class"] == "Low Risk"]
        assert set(low["priority_level"].unique()) == {"Low Priority"}

    def test_no_missing_priority(self):
        df = pd.read_csv(os.path.join(DSS_DIR, "district_decision_support.csv"))
        assert df["priority_level"].isna().sum() == 0

    def test_no_missing_risk_class(self):
        df = pd.read_csv(os.path.join(DSS_DIR, "district_decision_support.csv"))
        assert df["risk_class"].isna().sum() == 0


class TestPlanningRules:
    def test_all_features_have_rules(self):
        rules = pd.read_csv(os.path.join(DSS_DIR, "planning_rules.csv"))
        for feat in FEATURES:
            assert feat in rules["feature"].values, f"Missing rule for {feat}"

    def test_all_features_have_planning_focus(self):
        rules = pd.read_csv(os.path.join(DSS_DIR, "planning_rules.csv"))
        for _, row in rules.iterrows():
            assert len(str(row["planning_focus"])) > 5, f"Empty planning focus for {row['feature']}"

    def test_planning_focus_in_dss(self):
        dss = pd.read_csv(os.path.join(DSS_DIR, "district_decision_support.csv"))
        rules = pd.read_csv(os.path.join(DSS_DIR, "planning_rules.csv"))
        planning_set = set(rules["planning_focus"].tolist())
        for col in ["planning_focus_1", "planning_focus_2", "planning_focus_3"]:
            for val in dss[col].dropna().unique():
                assert val in planning_set, f"Unknown planning focus: {val}"


class TestDistrictSummary:
    def test_summary_has_required_columns(self):
        df = pd.read_csv(os.path.join(DSS_DIR, "district_priority_summary.csv"))
        required = [
            "State", "District", "years_observed", "high_risk_years",
            "medium_risk_years", "low_risk_years", "high_risk_proportion",
            "latest_year", "latest_risk_class", "persistent_priority",
            "common_contributing_features",
        ]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_summary_row_count(self):
        dss = pd.read_csv(os.path.join(DSS_DIR, "district_decision_support.csv"))
        summary = pd.read_csv(os.path.join(DSS_DIR, "district_priority_summary.csv"))
        assert len(summary) == dss[["State", "District"]].drop_duplicates().shape[0]

    def test_year_counts_add_up(self):
        summary = pd.read_csv(os.path.join(DSS_DIR, "district_priority_summary.csv"))
        for _, row in summary.iterrows():
            total = row["high_risk_years"] + row["medium_risk_years"] + row["low_risk_years"]
            assert total == row["years_observed"], f"Year count mismatch for {row['State']}, {row['District']}"

    def test_proportion_correct(self):
        summary = pd.read_csv(os.path.join(DSS_DIR, "district_priority_summary.csv"))
        for _, row in summary.iterrows():
            expected = round(row["high_risk_years"] / row["years_observed"], 4) if row["years_observed"] > 0 else 0.0
            assert abs(row["high_risk_proportion"] - expected) < 0.001

    def test_persistent_priority_logic(self):
        summary = pd.read_csv(os.path.join(DSS_DIR, "district_priority_summary.csv"))
        for _, row in summary.iterrows():
            if row["persistent_priority"] == "Persistent High Priority":
                assert row["high_risk_years"] >= 2 and row["years_observed"] >= 2
            elif row["persistent_priority"] == "Persistent Medium Priority":
                assert row["medium_risk_years"] >= 2 and row["years_observed"] >= 2
            elif row["persistent_priority"] == "Persistent Low Priority":
                assert row["low_risk_years"] >= 2 and row["years_observed"] >= 2


class TestFeatureContributions:
    def test_top_features_are_valid(self):
        dss = pd.read_csv(os.path.join(DSS_DIR, "district_decision_support.csv"))
        for col in ["top_contributing_feature_1", "top_contributing_feature_2", "top_contributing_feature_3"]:
            for val in dss[col].dropna().unique():
                assert val in FEATURES, f"Invalid feature: {val}"

    def test_planning_focuses_are_valid(self):
        dss = pd.read_csv(os.path.join(DSS_DIR, "district_decision_support.csv"))
        for col in ["planning_focus_1", "planning_focus_2", "planning_focus_3"]:
            for val in dss[col].dropna().unique():
                assert val in FEATURE_PLANNING_MAP.values(), f"Unknown planning focus: {val}"

    def test_no_nan_in_contributions(self):
        dss = pd.read_csv(os.path.join(DSS_DIR, "district_decision_support.csv"))
        for col in dss.columns:
            if "feature" in col or "focus" in col:
                assert not dss[col].isna().any(), f"NaN in {col}"


class TestReportContent:
    def test_report_mentions_derived(self):
        with open(os.path.join(DSS_DIR, "decision_support_report.md")) as f:
            content = f.read()
        assert "derived" in content.lower() or "K-Means" in content

    def test_report_mentions_not_causal(self):
        with open(os.path.join(DSS_DIR, "decision_support_report.md")) as f:
            content = f.read()
        assert "causal" in content.lower() or "NOT" in content

    def test_report_has_priority_counts(self):
        with open(os.path.join(DSS_DIR, "decision_support_report.md")) as f:
            content = f.read()
        assert "High Priority" in content
        assert "Medium Priority" in content
        assert "Low Priority" in content


class TestTestDataIntegrity:
    def test_source_data_unchanged(self):
        d1 = pd.read_csv("dataset1.csv")
        d2 = pd.read_csv("dataset2.csv")
        assert len(d1) == 6293
        assert len(d2) == 2112

    def test_preprocessed_unchanged(self):
        pre = pd.read_csv("outputs/preprocessed_output.csv")
        assert pre.shape[0] == 8405

    def test_clustering_unchanged(self):
        cl = pd.read_csv("outputs/risk_classification/district_year_risk_clusters.csv")
        assert cl.shape[0] == 8405
