import os
import sys

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
COLLIDING_MODULES = ("main", "config", "api", "schemas", "services")


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Build a TestClient against the FastAPI app without polluting global import state.

    The root project and the backend both expose a top-level `config` module. To
    import the backend app, the root `config` (already cached during collection)
    is temporarily ejected so the backend's `config.py` is loaded; it is restored
    and all backend modules are dropped when the session ends.
    """
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


class TestRecentHmisRoutesRegistered:
    def test_routes_exist(self, client):
        paths = set(client.app.openapi()["paths"].keys())
        assert "/api/recent-hmis/overview" in paths
        assert "/api/recent-hmis/coverage" in paths
        assert "/api/recent-hmis/indicators" in paths


class TestRecentHmisOverview:
    def test_overview_kpis(self, client):
        res = client.get("/api/recent-hmis/overview")
        assert res.status_code == 200
        data = res.json()
        assert data["dataset"] == "Dataset 3 / Recent HMIS Extension"
        assert data["total_observations"] == 3306
        assert data["n_state_district_units"] == 812
        assert data["n_states"] == 36

    def test_overview_years(self, client):
        data = client.get("/api/recent-hmis/overview").json()
        assert data["years"] == ["2020-2021", "2021-2022", "2022-2023", "2023-2024", "2024-2025"]
        assert data["observations_by_year"] == {
            "2020-2021": 782,
            "2021-2022": 782,
            "2022-2023": 791,
            "2023-2024": 783,
            "2024-2025": 168,
        }

    def test_overview_notes_and_availability(self, client):
        data = client.get("/api/recent-hmis/overview").json()
        assert "17 states with complete UpTo_Mar files" in data["notes"]["partial_2024_2025"]
        assert "HTTP 500" in data["notes"]["not_included_2025_2026"]
        assert len(data["year_availability"]) == 6
        assert data["year_availability"][-1]["fiscal_year"] == "2025-2026"
        assert "HTTP 500" in data["year_availability"][-1]["availability"]


class TestRecentHmisCoverage:
    def test_years_coverage(self, client):
        data = client.get("/api/recent-hmis/coverage").json()
        years = data["years_coverage"]
        assert [y["fiscal_year"] for y in years] == [
            "2020-2021", "2021-2022", "2022-2023", "2023-2024", "2024-2025",
        ]
        assert [y["observations"] for y in years] == [782, 782, 791, 783, 168]
        assert [y["states"] for y in years] == [36, 36, 36, 36, 17]
        assert [y["partial"] for y in years] == [False, False, False, False, True]
        assert sum(y["observations"] for y in years) == 3306

    def test_district_coverage(self, client):
        data = client.get("/api/recent-hmis/coverage").json()
        dc = data["district_coverage"]
        assert dc["reference_707_units"] == 707
        assert dc["dataset_3_distinct_identifiers"] == 812
        assert dc["difference"] == 105
        counts = {entry["type"]: entry["count"] for entry in dc["by_candidate_type"]}
        assert counts == {
            "Format variants": 13,
            "Alias candidates": 7,
            "Possible reorganizations": 77,
            "Possible split": 1,
            "Uncertain": 7,
        }
        assert sum(counts.values()) == 105

    def test_district_coverage_notes(self, client):
        data = client.get("/api/recent-hmis/coverage").json()
        note = data["district_coverage"]["native_representation_note"]
        assert "no automatic district merging was performed" in note


class TestRecentHmisIndicators:
    def test_indicator_availability_counts(self, client):
        data = client.get("/api/recent-hmis/indicators").json()
        counts = {ind["name"]: (ind["valid"], ind["missing"]) for ind in data["indicators"]}
        assert counts["ANC First Trimester"] == (3148, 158)
        assert counts["TT2 / Booster"] == (3148, 158)
        assert counts["Severe Anemia"] == (3138, 168)
        assert counts["Obstetric Complications"] == (2219, 1087)

    def test_obstetric_note(self, client):
        data = client.get("/api/recent-hmis/indicators").json()
        obst = next(i for i in data["indicators"] if i["name"] == "Obstetric Complications")
        assert obst["status"] == "Available through 2022-23"
        assert "does not provide the same aggregate" in obst["note"]

    def test_distributions(self, client):
        data = client.get("/api/recent-hmis/indicators").json()
        dists = data["distributions"]
        assert set(dists.keys()) == {
            "ANC_First_Trimester_Pct",
            "TT2_Booster_Pct",
            "Severe_Anemia_Pct",
        }
        for key, dist in dists.items():
            assert sum(bin_["count"] for bin_ in dist["bins"]) == dist["total_values"]
            labels = [bin_["label"] for bin_ in dist["bins"]]
            assert labels[0] == "0-9"
            assert labels[-1] == "100+"

    def test_harmonization_rows(self, client):
        data = client.get("/api/recent-hmis/indicators").json()
        indicators = [row["indicator"] for row in data["harmonization"]]
        assert indicators == [
            "ANC First Trimester",
            "TT2 / Booster",
            "Severe Anemia",
            "Institutional Delivery",
            "PNC within 48 hours",
            "Obstetric Complications",
        ]
        statuses = {row["indicator"]: row["status"] for row in data["harmonization"]}
        assert statuses["Severe Anemia"] == "Definition changed"
        assert statuses["Institutional Delivery"] == "Not comparable"

    def test_disclaimer(self, client):
        data = client.get("/api/recent-hmis/indicators").json()
        assert "not used to retrain or externally validate" in data["disclaimer"]


class TestExistingEndpointsUnchanged:
    @pytest.mark.parametrize("path", [
        "/api/overview",
        "/api/districts/",
        "/api/risk-analysis",
        "/api/planning-priorities",
        "/api/methodology",
    ])
    def test_existing_endpoints_still_respond(self, client, path):
        res = client.get(path)
        assert res.status_code == 200