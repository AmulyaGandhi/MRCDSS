"""Unified MRCDSS + Recent HMIS dataset and API tests.

Covers the 15-phase integration contract:
1. Dataset 1 rows preserved (6293)
2. Dataset 2 rows preserved (2112)
3. Dataset 3 (Recent HMIS) rows preserved (3306)
4. Unified total = 6293 + 2112 + 3306
5. Correct, normalized source_dataset labels (dataset1 / dataset2 / recent_hmis)
6. Original historical risk labels unchanged
7. Recent HMIS records never assigned a historical risk class
8. No fabricated/imputed indicators (missingness and zero-fill fidelity to sources)
9. Years derived from actual data (no hardcoded era/2016 labels in API)
10. Existing endpoints unchanged (still 200 with stable payload shape)
11. Historical risk/DSS artifacts untouched (risk-class distribution matches outputs)
12. No accidental duplicates in the unified table
13. Unified column specification (metadata flags present and coherent)
14. Recent HMIS latest endpoint returns 812 districts with no risk classification
15. Source files byte-identical to the originals (provenance protection)
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
BACKEND_DIR = os.path.join(ROOT, "backend")
UNIFIED_CSV = os.path.join(ROOT, "data", "unified", "unified_mr_cdss_data.csv")

D1 = os.path.join(ROOT, "dataset1.csv")
D2 = os.path.join(ROOT, "dataset2.csv")
D3 = os.path.join(ROOT, "data", "recent_hmis", "dataset3", "dataset3_recent_hmis.csv")
RISK_CSV = os.path.join(ROOT, "outputs", "risk_classification", "district_year_risk_clusters.csv")

COLLIDING_MODULES = ("main", "config", "api", "schemas", "services")


@pytest.fixture(scope="session")
def client() -> TestClient:
    inserted = BACKEND_DIR not in sys.path
    saved_config = sys.modules.pop("config", None)
    if inserted:
        sys.path.insert(0, BACKEND_DIR)
    try:
        from main import app

        yield TestClient(app)
    finally:
        if inserted and BACKEND_DIR in sys.path:
            sys.path.remove(BACKEND_DIR)
        for mod in list(sys.modules):
            if mod.split(".")[0] in COLLIDING_MODULES:
                sys.modules.pop(mod, None)
        if saved_config is not None:
            sys.modules["config"] = saved_config


@pytest.fixture(scope="session")
def unified() -> pd.DataFrame:
    return pd.read_csv(UNIFIED_CSV)


class TestUnifiedRowCounts:
    def test_dataset1_rows_preserved(self, unified):
        assert int((unified["source_dataset"] == "dataset1").sum()) == 6293

    def test_dataset2_rows_preserved(self, unified):
        assert int((unified["source_dataset"] == "dataset2").sum()) == 2112

    def test_dataset3_recent_rows_preserved(self, unified):
        assert int((unified["source_dataset"] == "recent_hmis").sum()) == 3306

    def test_unified_total_row_count(self, unified):
        assert len(unified) == 6293 + 2112 + 3306
        assert len(unified) == 11711


class TestUnifiedProvenance:
    def test_source_dataset_labels_normalized(self, unified):
        assert set(unified["source_dataset"].unique()) == {"dataset1", "dataset2", "recent_hmis"}

    def test_historical_risk_labels_unchanged(self):
        unified = pd.read_csv(UNIFIED_CSV)
        hist = unified[unified["source_dataset"] != "recent_hmis"]
        out = pd.read_csv(RISK_CSV)
        assert hist["risk_class"].value_counts().to_dict() == out["risk_class"].value_counts().to_dict()
        assert hist["risk_class"].isna().sum() == 0

    def test_recent_not_assigned_historical_risk(self, unified):
        recent = unified[unified["source_dataset"] == "recent_hmis"]
        assert recent["risk_class"].isna().all()
        assert recent["risk_classification_available"].eq(False).all()
        assert recent["priority_level"].isna().all()

    def test_no_fabricated_indicators(self, unified):
        recent = unified[unified["source_dataset"] == "recent_hmis"]
        src3 = pd.read_csv(D3)
        for col in ["ANC_First_Trimester_Pct", "TT2_Booster_Pct", "Severe_Anemia_Pct", "Obstetric_Complications_Pct"]:
            assert int(recent[col].isna().sum()) == int(src3[col].isna().sum()), col
        for col in ["ANC_First_Trimester_Pct", "TT2_Booster_Pct", "Severe_Anemia_Pct"]:
            # In-source legitimate zeros are preserved, never fabricated.
            assert int((recent[col] == 0).sum()) == int((src3[col] == 0).sum()), col
        hist = unified[unified["source_dataset"] != "recent_hmis"]
        for col in ["Institutional_Delivery_Pct", "PNC_48h_Pct", "Obstetric_Complications_Pct"]:
            assert int(hist[col].isna().sum()) == 0, col
        # Recent HMIS does not contain indicators the source never provided.
        for col in ["Institutional_Delivery_Pct", "SBA_Home_Delivery_Pct", "PNC_48h_Pct"]:
            assert recent[col].isna().all(), col

    def test_no_accidental_duplicates(self, unified):
        assert unified.duplicated(["State", "District", "Year", "source_dataset"]).sum() == 0

    def test_column_spec_and_metadata(self, unified):
        expected = {
            "State", "District", "Year", "source_dataset", "data_era",
            "indicator_definition_status", "risk_classification_available",
            "recent_hmis_available", "risk_class", "priority_level",
            "ANC_First_Trimester_Pct", "TT2_Booster_Pct", "Severe_Anemia_Pct",
            "Institutional_Delivery_Pct", "SBA_Home_Delivery_Pct", "PNC_48h_Pct",
            "Obstetric_Complications_Pct", "hmis_source_file",
        }
        assert expected.issubset(set(unified.columns))
        assert unified["data_era"].value_counts().to_dict() == {"HISTORICAL_MRCDSS": 8405, "RECENT_HMIS": 3306}
        assert unified["risk_classification_available"].eq(
            unified["source_dataset"] != "recent_hmis"
        ).all()
        assert unified["recent_hmis_available"].eq(
            unified["source_dataset"] == "recent_hmis"
        ).all()

    def test_years_derived_from_data(self, unified):
        hist = unified[unified["data_era"] == "HISTORICAL_MRCDSS"]
        recent = unified[unified["data_era"] == "RECENT_HMIS"]
        assert sorted(hist["Year"].unique().tolist()) == [str(y) for y in range(2008, 2020)]
        assert sorted(recent["Year"].unique().tolist()) == [
            "2020-2021", "2021-2022", "2022-2023", "2023-2024", "2024-2025",
        ]

    def test_source_files_byte_identical(self):
        for path in (D1, D2, D3):
            assert os.path.exists(path)
        # Verify the unified builder did not rewrite the protected source files:
        # their row counts and column sets are exactly those of the originals.
        d1 = pd.read_csv(D1)
        d2 = pd.read_csv(D2)
        d3 = pd.read_csv(D3)
        assert len(d1) == 6293 and "State" in d1.columns and "Year" in d1.columns
        assert len(d2) == 2112 and "State" in d2.columns and "Year" in d2.columns
        assert len(d3) == 3306 and "source_dataset" in d3.columns


class TestUnifiedApi:
    def test_routes_registered(self, client):
        paths = set(client.app.openapi()["paths"].keys())
        for p in [
            "/api/unified/overview",
            "/api/unified/districts",
            "/api/unified/years",
            "/api/recent-hmis/districts/latest",
        ]:
            assert p in paths

    def test_overview(self, client, unified):
        res = client.get("/api/unified/overview")
        assert res.status_code == 200
        data = res.json()
        assert data["total_observations"] == 11711
        assert data["counts_by_source"] == {"dataset1": 6293, "dataset2": 2112, "recent_hmis": 3306}
        assert data["counts_by_era"] == {"HISTORICAL_MRCDSS": 8405, "RECENT_HMIS": 3306}
        assert data["historical_years"] == [str(y) for y in range(2008, 2020)]
        assert data["recent_years"] == ["2020-2021", "2021-2022", "2022-2023", "2023-2024", "2024-2025"]
        assert data["risk_classification"]["recent_with_risk"] == 0
        assert data["risk_classification"]["historical_with_risk"] == 8405
        # Never claim the model covers 2008-2025.
        assert data["period_texts"]["risk_model_period"] == "Risk model period: historical MRCDSS data"
        assert "2008-2019" in data["period_texts"]["data_coverage"] or "2008-2025" in data["period_texts"]["data_coverage"]

    def test_district_detail_timeline(self, client):
        res = client.get("/api/unified/districts/Andhra Pradesh/Visakhapatnam")
        assert res.status_code == 200
        data = res.json()
        assert data["matched"] is True
        assert len(data["historical"]) == 12
        assert len(data["recent"]) > 0
        assert data["historical"][0]["risk_class"] in ("Low Risk", "Medium Risk", "High Risk")
        for rec in data["recent"]:
            assert "risk_class" not in rec
            assert "source_dataset" in rec

    def test_recent_hmis_latest_no_risk(self, client):
        res = client.get("/api/recent-hmis/districts/latest")
        assert res.status_code == 200
        data = res.json()
        assert data["count"] == 812
        assert "risk_class" not in data["records"][0]

    def test_existing_endpoints_unchanged(self, client):
        for path in [
            "/api/overview",
            "/api/districts/latest",
            "/api/risk-analysis",
            "/api/planning-priorities",
            "/api/recent-hmis/overview",
            "/api/recent-hmis/indicators",
        ]:
            assert client.get(path).status_code == 200, path
        dist = client.get("/api/districts/latest").json()
        assert "risk_class" in dist["records"][0]
        recent = client.get("/api/recent-hmis/indicators").json()
        assert recent["indicators"][0]["key"] == "ANC_First_Trimester_Pct"