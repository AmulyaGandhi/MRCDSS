import os
import sys

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
COLLIDING_MODULES = ("main", "config", "api", "schemas", "services")

NOT_AVAILABLE = "That information is not available in the current MRCDSS evidence."


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Build a TestClient against the FastAPI app without polluting global import state.

    Mirrors tests/recent_hmis/test_recent_hmis_api.py. The root project and the
    backend both expose a top-level `config` module; the root `config` (cached
    during collection) is temporarily ejected so the backend's `config.py` is
    loaded, then restored when the session ends.
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


@pytest.fixture(autouse=True)
def _deterministic_llm(monkeypatch):
    """Force the deterministic (non-Ollama) answer path for every test in this module."""
    monkeypatch.setenv("MRCDSS_LLM_PROVIDER", "off")


def _chat(client, message, state=None, district=None, page_context=None,
          history=None, scope=None):
    body = {"message": message}
    if state is not None:
        body["state"] = state
    if district is not None:
        body["district"] = district
    if page_context is not None:
        body["page_context"] = page_context
    if history is not None:
        body["history"] = history
    if scope is not None:
        body["scope"] = scope
    res = client.post("/api/assistant/chat", json=body)
    assert res.status_code == 200
    return res.json()


class TestAssistantRoutesRegistered:
    def test_chat_route_exists(self, client):
        paths = set(client.app.openapi()["paths"].keys())
        assert "/api/assistant/chat" in paths

    def test_empty_message(self, client):
        data = _chat(client, "")
        assert data["grounded"] is False
        assert data["intent"] == "unknown"
        assert data["mode"] == "fallback"


class TestAssistantDistrictRisk:
    def test_district_risk_from_body(self, client):
        data = _chat(client, "What is the risk classification?", state="Telangana", district="Warangal")
        assert data["intent"] == "district_risk"
        assert data["grounded"] is True
        assert data["mode"] == "fallback"
        assert "Warangal" in data["answer"]
        assert "Low Risk" in data["answer"]
        assert "District Decision Support" in data["sources"]
        assert data["context"]["matched"] is True

    def test_district_risk_from_message(self, client):
        data = _chat(client, "What is the risk classification of Alluri Sitharama Raju in Andhra Pradesh?")
        assert data["intent"] == "district_risk"
        assert "Alluri Sitharama Raju" in data["answer"]
        assert data["sources"][0] == "District Decision Support"

    def test_district_priority_from_body(self, client):
        data = _chat(client, "What is the priority?", state="Telangana", district="Warangal")
        assert data["intent"] == "district_priority"
        assert "Low Priority" in data["answer"]
        assert "District Decision Support" in data["sources"]


class TestAssistantRetrievalIntents:
    def test_shap_explainability(self, client):
        data = _chat(client, "Explain the model with SHAP")
        assert data["intent"] == "shap"
        assert "SHAP Explainability" in data["sources"]
        assert "not causation" in data["answer"] or "do not establish causation" in data["answer"]

    def test_planning_priorities(self, client):
        data = _chat(client, "What should planners focus on?")
        assert data["intent"] == "planning"
        assert "Planning Priorities" in data["sources"]
        assert "planning focus" in data["answer"].lower()

    def test_recent_hmis_general(self, client):
        data = _chat(client, "Give me the latest HMIS evidence")
        assert data["intent"] == "recent_hmis"
        assert "Recent HMIS" in data["sources"]
        assert "record-years" in data["answer"]

    def test_aggregate(self, client):
        data = _chat(client, "How many districts are high risk?")
        assert data["intent"] == "aggregate"
        assert "High Priority" in data["answer"]

    def test_methodology_kmeans(self, client):
        data = _chat(client, "How were the risk classes generated?")
        assert data["intent"] == "methodology"
        assert "MRCDSS Methodology" in data["sources"]
        assert "K-Means" in data["answer"]

    def test_methodology_dataset3_retrain(self, client):
        data = _chat(client, "Why was Dataset 3 not used to retrain the model?")
        assert data["intent"] == "methodology"
        assert "not used to retrain" in data["answer"].lower()

    def test_selected_model(self, client):
        data = _chat(client, "Which model was selected?")
        assert data["intent"] == "methodology"
        assert "Logistic Regression" in data["answer"]

    def test_about(self, client):
        data = _chat(client, "What is MRCDSS?")
        assert data["intent"] == "about"
        assert "MRCDSS Methodology" in data["sources"]


class TestAssistantGrounding:
    def test_unknown_district_returns_not_available(self, client):
        data = _chat(client, "What is the risk of Xyzville?", district="Xyzville")
        assert data["grounded"] is False
        assert data["answer"] == NOT_AVAILABLE

    def test_unsupported_question_returns_not_available(self, client):
        data = _chat(client, "Is the moon made of cheese?")
        assert data["grounded"] is False
        assert data["intent"] == "unknown"
        assert data["answer"] == NOT_AVAILABLE

    def test_missing_evidence_no_hardcoded_risk(self, client):
        """Anakapalli has Recent HMIS records but no historical risk class."""
        data = _chat(client, "What is the risk classification?", state="Andhra Pradesh", district="Anakapalli")
        assert data["intent"] == "district_risk"
        assert data["grounded"] is True
        assert "no validated historical MRCDSS risk classification" in data["answer"]

    def test_no_fabricated_risk_from_recent_hmis(self, client):
        data = _chat(client, "Does recent HMIS reassign the risk class?")
        assert data["intent"] == "recent_risk_change"
        assert data["grounded"] is True
        assert "never used to assign" in data["answer"]

    def test_context_aware_generic_question(self, client):
        data = _chat(client, "Tell me about this district", state="Telangana", district="Warangal")
        assert data["intent"] == "summary"
        assert data["grounded"] is True
        assert "Warangal" in data["answer"]
        assert "District Decision Support" in data["sources"]


class TestAssistantOllamaUnavailable:
    def test_ollama_down_falls_back(self, client, monkeypatch):
        monkeypatch.setenv("MRCDSS_LLM_PROVIDER", "ollama")
        monkeypatch.setenv("MRCDSS_OLLAMA_MODEL", "test-model")
        monkeypatch.setenv("MRCDSS_OLLAMA_BASE_URL", "http://127.0.0.1:59999")
        data = _chat(client, "What is the risk classification?", state="Telangana", district="Warangal")
        assert data["mode"] == "fallback"
        assert data["grounded"] is True
        assert "Warangal" in data["answer"]

    def test_ollama_unreachable_model_absent_falls_back(self, client, monkeypatch):
        monkeypatch.setenv("MRCDSS_LLM_PROVIDER", "ollama")
        monkeypatch.setenv("MRCDSS_OLLAMA_MODEL", "some-model")
        monkeypatch.setenv("MRCDSS_OLLAMA_BASE_URL", "http://127.0.0.1:59999")
        data = _chat(client, "What is the risk classification?", state="Telangana", district="Warangal")
        assert data["mode"] == "fallback"
        assert data["answer"].startswith("Warangal")


class TestAssistantOllamaAvailableMocked:
    def test_ollama_available_uses_llm(self, client, monkeypatch):
        from services import assistant_service as svc

        monkeypatch.setattr(svc, "_ollama_active", lambda: True)
        monkeypatch.setattr(svc, "_llm_chat", lambda prompt: "mocked disha answer")

        data = _chat(client, "What is the risk classification?", state="Telangana", district="Warangal")
        assert data["mode"] == "ollama"
        assert data["answer"] == "mocked disha answer"
        assert data["grounded"] is True

    def test_ollama_prompt_contains_system_instructions(self, client, monkeypatch):
        from services import assistant_service as svc

        calls = {}

        def fake_llm(prompt):
            calls["prompt"] = prompt
            return "ok"

        monkeypatch.setattr(svc, "_ollama_active", lambda: True)
        monkeypatch.setattr(svc, "_llm_chat", fake_llm)

        _chat(client, "What is the risk of Warangal?", state="Telangana", district="Warangal")
        prompt = calls["prompt"]
        assert "You are Disha, the MRCDSS Decision Assistant." in prompt
        assert "Do not invent district statistics" in prompt
        assert "Do not treat SHAP as causal evidence" in prompt
        assert "not available in the current MRCDSS evidence" in prompt
        assert "Grounded MRCDSS evidence:" in prompt

    def test_ollama_malformed_response_falls_back(self, client, monkeypatch):
        from services import assistant_service as svc

        monkeypatch.setattr(svc, "_ollama_active", lambda: True)
        monkeypatch.setattr(svc, "_llm_chat", lambda prompt: None)

        data = _chat(client, "What is the risk classification?", state="Telangana", district="Warangal")
        assert data["mode"] == "fallback"
        assert data["grounded"] is True
        assert "Warangal" in data["answer"]

    def test_ollama_exception_falls_back(self, client, monkeypatch):
        from services import assistant_service as svc

        def boom(prompt):
            raise RuntimeError("llm exploded")

        monkeypatch.setattr(svc, "_ollama_active", lambda: True)
        monkeypatch.setattr(svc, "_llm_chat", boom)

        data = _chat(client, "What is the risk classification?", state="Telangana", district="Warangal")
        assert data["mode"] == "fallback"
        assert data["grounded"] is True
        assert "Warangal" in data["answer"]


class TestAssistantResponseContract:
    def test_frontend_compatible_response_shape(self, client):
        data = _chat(client, "What is MRCDSS?")
        assert set(data.keys()) == {"answer", "grounded", "sources", "mode", "intent", "context"}
        assert isinstance(data["answer"], str) and data["answer"]
        assert isinstance(data["grounded"], bool)
        assert isinstance(data["sources"], list)
        assert data["mode"] in ("ollama", "fallback")
        assert isinstance(data["intent"], str)
        assert isinstance(data["context"], dict) or data["context"] is None

    def test_sources_reflect_actual_answer(self, client):
        data = _chat(client, "What is the risk classification?", state="Telangana", district="Warangal")
        assert "District Decision Support" in data["sources"]
        assert set(data["sources"]) <= {
            "District Decision Support", "SHAP Explainability", "Recent HMIS",
            "Planning Priorities", "MRCDSS Methodology",
        }


class TestAssistantPageContext:
    def test_page_context_accepted(self, client):
        data = _chat(client, "What is the risk classification?", state="Telangana", district="Warangal",
                     page_context="district_explorer")
        assert data["intent"] == "district_risk"
        assert data["grounded"] is True


class TestAssistantNaturalLanguageVariations:
    def test_risk_variation_explicit(self, client):
        data = _chat(client, "What is Warangal's risk?")
        assert data["intent"] == "district_risk"
        assert data["grounded"] is True
        assert "Warangal" in data["answer"]
        assert data["context"]["district"] == "Warangal"

    def test_risk_variation_how_risky(self, client):
        data = _chat(client, "How risky is Warangal?")
        assert data["intent"] == "district_risk"
        assert data["grounded"] is True
        assert "Risk" in data["answer"]

    def test_risk_variation_why_classified(self, client):
        data = _chat(client, "Why was Warangal classified this way?")
        assert data["intent"] == "district_risk"
        assert data["grounded"] is True
        assert data["context"]["district"] == "Warangal"
        assert {"District Decision Support", "SHAP Explainability"} <= set(data["sources"])

    def test_variation_what_made_district_high_risk(self, client):
        data = _chat(client, "What made Warangal high risk?")
        assert data["intent"] == "contributing"
        assert data["grounded"] is True
        assert data["context"]["district"] == "Warangal"
        assert "SHAP Explainability" in data["sources"]

    def test_variation_tell_me_about_district(self, client):
        data = _chat(client, "Tell me about Warangal.")
        assert data["intent"] == "summary"
        assert data["grounded"] is True
        assert "Warangal" in data["answer"]

    def test_variation_planners_focus_with_scope(self, client):
        scope = {"state": "Telangana", "district": "Warangal", "matched": True, "topic": "planning"}
        data = _chat(client, "What should planners focus on there?", scope=scope)
        assert data["intent"] == "planning"
        assert data["grounded"] is True
        assert data["context"]["district"] == "Warangal"
        assert "Planning Priorities" in data["sources"]

    def test_variation_recent_hmis_with_scope(self, client):
        scope = {"state": "Telangana", "district": "Warangal", "matched": True, "topic": "recent_hmis"}
        data = _chat(client, "What is its recent HMIS evidence?", scope=scope)
        assert data["intent"] == "recent_hmis"
        assert data["grounded"] is True
        assert data["context"]["district"] == "Warangal"
        assert "HMIS" in data["answer"]


class TestAssistantMethodologyNL:
    def test_why_logistic_regression(self, client):
        data = _chat(client, "Why Logistic Regression?")
        assert data["intent"] == "methodology"
        assert data["grounded"] is True
        assert "Logistic" in data["answer"] and "Regression" in data["answer"]

    def test_why_kmeans(self, client):
        data = _chat(client, "Why K-Means?")
        assert data["intent"] == "methodology"
        assert data["grounded"] is True
        assert "K-Means" in data["answer"]

    def test_what_does_shap_tell_us(self, client):
        data = _chat(client, "What does SHAP tell us?")
        assert data["intent"] == "shap"
        assert data["grounded"] is True
        assert "SHAP" in data["answer"]

    def test_why_recent_hmis_not_used_for_retraining(self, client):
        data = _chat(client, "Why wasn't recent HMIS used for retraining?")
        assert data["intent"] == "methodology"
        assert data["grounded"] is True
        assert "not used to retrain" in data["answer"].lower()


class TestAssistantConceptual:
    def test_what_is_dss(self, client):
        data = _chat(client, "What is a decision support system?")
        assert data["intent"] == "dss"
        assert data["grounded"] is True
        assert "Decision Support System" in data["answer"]

    def test_what_is_shap(self, client):
        data = _chat(client, "What is SHAP?")
        assert data["intent"] == "shap"
        assert data["grounded"] is True
        assert "SHAP" in data["answer"]

    def test_glossary_offline(self, client):
        data = _chat(client, "What is supervised learning?")
        assert data["intent"] == "conceptual"
        assert data["grounded"] is True
        assert "Supervised" in data["answer"]


class TestAssistantDomainCoverage:
    def test_dataset_question(self, client):
        data = _chat(client, "What data are you using?")
        assert data["intent"] == "dataset"
        assert data["grounded"] is True

    def test_preprocessing_question(self, client):
        data = _chat(client, "How did you clean the data?")
        assert data["intent"] == "preprocessing"
        assert data["grounded"] is True
        assert "missing" in data["answer"].lower()

    def test_features_question(self, client):
        data = _chat(client, "Why did you remove IFA?")
        assert data["intent"] == "features"
        assert data["grounded"] is True
        assert "IFA" in data["answer"]

    def test_limitations_question(self, client):
        data = _chat(client, "What are the limitations of the system?")
        assert data["intent"] == "limitations"
        assert data["grounded"] is True
        assert "clinical" in data["answer"].lower()

    def test_system_overview_question(self, client):
        data = _chat(client, "How does the whole system work?")
        assert data["intent"] == "system"
        assert data["grounded"] is True
        assert "preprocess" in data["answer"].lower()

    def test_historical_vs_recent_question(self, client):
        data = _chat(client, "What is the difference between the historical data and recent HMIS?")
        assert data["intent"] == "dataset"
        assert data["grounded"] is True
        assert "Dataset 3" in data["answer"]


class TestAssistantGeneral:
    def test_general_offline_unavailable(self, client):
        data = _chat(client, "What is the capital of France?")
        assert data["intent"] == "general"
        assert data["grounded"] is False
        assert data["mode"] == "fallback"
        assert data["sources"] == []
        assert "Ollama" in data["answer"] or "LLM" in data["answer"]

    def test_general_online_uses_llm(self, client, monkeypatch):
        from services import assistant_service as svc
        monkeypatch.setattr(svc, "_ollama_active", lambda: True)
        monkeypatch.setattr(svc, "_llm_chat", lambda prompt: "Paris is the capital of France.")
        data = _chat(client, "What is the capital of France?")
        assert data["intent"] == "general"
        assert data["mode"] == "general"
        assert data["grounded"] is False
        assert data["sources"] == []
        assert data["answer"] == "Paris is the capital of France."


class TestAssistantConversationContext:
    def test_follow_up_recent_hmis(self, client):
        history = [
            {"role": "user", "text": "Why is Warangal high risk?"},
            {"role": "assistant", "text": "Warangal (Telangana) is classified as a district-risk answer."},
        ]
        scope = {"state": "Telangana", "district": "Warangal", "matched": True, "topic": "district_risk"}
        data = _chat(client, "What about its recent HMIS data?", scope=scope, history=history)
        assert data["intent"] == "recent_hmis"
        assert data["grounded"] is True
        assert data["context"]["district"] == "Warangal"
        assert "HMIS" in data["answer"]
        assert data["context"]["topic"] == "recent_hmis"

    def test_follow_up_does_not_change_classification(self, client):
        history = [
            {"role": "user", "text": "Why is Warangal high risk?"},
            {"role": "assistant", "text": "Warangal (Telangana) is classified as a district-risk answer."},
            {"role": "user", "text": "What about its recent HMIS data?"},
            {"role": "assistant", "text": "The latest recent HMIS evidence for Warangal."},
        ]
        scope = {"state": "Telangana", "district": "Warangal", "matched": True, "topic": "recent_hmis"}
        data = _chat(client, "Does that change its classification?", scope=scope, history=history)
        assert data["intent"] == "recent_risk_change"
        assert data["grounded"] is True
        assert data["context"]["district"] == "Warangal"
        assert "never used to assign" in data["answer"]