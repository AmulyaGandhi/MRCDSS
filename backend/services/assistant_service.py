"""Disha — MRCDSS Decision Assistant (natural-language, retrieval-grounded).

Disha uses natural-language understanding to map a question to a MRCDSS topic,
retrieves the relevant evidence from the existing MRCDSS services (unified
dataset, methodology, model comparison, SHAP, planning, Recent HMIS), and then
lets an optional LLM provider phrase/answer the question. When the LLM is
unavailable every grounded question is still answered deterministically from
the retrieved evidence, so MRCDSS functionality never depends on the LLM.

Key properties:
  * The LLM is a reasoning/conversation layer, never the source of facts.
  * Keyword rules are lightweight fallbacks only; the primary gate is
    natural-language understanding (LLM-driven when available).
  * Conversation memory is short-lived: the client echoes the previous turn's
    resolved scope (district + topic), which is used to resolve follow-ups
    such as "its recent HMIS" or "does that change the classification?".
  * Nothing is written and no model is trained.

Configuration (environment):
    MRCDSS_LLM_PROVIDER          ollama | groq | off
    GROQ_API_KEY                 Groq Cloud API key (backend only)
    GROQ_MODEL                   Groq model name (default: openai/gpt-oss-120b)
    GROQ_BASE_URL                Groq API base URL (default: https://api.groq.com/openai/v1)
    MRCDSS_OLLAMA_MODEL          Ollama model name; empty => deterministic only
    MRCDSS_OLLAMA_BASE_URL       default http://localhost:11434
"""
from __future__ import annotations

import json
import os
import re
import urllib.request

from services import (
    methodology_service,
    overview_service,
    planning_service,
    recent_hmis_service,
    risk_analysis_service,
    unified_service,
)

NOT_AVAILABLE = "That information is not available in the current MRCDSS evidence."

SOURCE_DISTRICT = "District Decision Support"
SOURCE_SHAP = "SHAP Explainability"
SOURCE_RECENT = "Recent HMIS"
SOURCE_METHODOLOGY = "MRCDSS Methodology"
SOURCE_PLANNING = "Planning Priorities"

SYSTEM_PROMPT = (
    "You are Disha, the MRCDSS Decision Assistant.\n"
    "Answer only from the supplied MRCDSS evidence.\n"
    "Answer the exact question first, using simple, natural, conversational English.\n"
    "Prefer 1–4 short sentences. Use bullet points only when listing items.\n"
    "Avoid unnecessary introductions, explanations, or repeating information.\n"
    "Never dump multiple statistics or entire backend responses.\n"
    "Avoid excessive technical terminology unless explicitly requested.\n"
    "Never provide unrelated information just because it exists in retrieved context.\n"
    "Do not treat SHAP as causal evidence.\n"
    "Do not provide patient-level diagnosis, treatment, or emergency medical advice.\n"
    "Recent HMIS evidence is contextual evidence and was not used to assign the "
    "historical MRCDSS risk classification.\n"
    "Explain technical concepts in simple language when needed.\n"
    "K-Means risk labels are derived analytical classifications, not clinical ground truth.\n"
    "Supervised metrics measure reproduction of derived labels on seen units, not "
    "clinical prediction accuracy.\n"
    "SHAP indicates model attribution, not causation.\n"
    "Severe Anemia has cross-dataset comparability limitations (D1 vs D2 "
    "harmonization uncertainty).\n"
    "Distinguish historical MRCDSS assessments (2008-2019) from recent HMIS "
    "evidence (2020-2025).\n"
    "Never fabricate an answer to appear helpful.\n"
    "If the supplied evidence does not contain the answer, say that the "
    "information is not available in the current MRCDSS evidence."
)

TOPIC_ABOUT = "about"
TOPIC_SYSTEM = "system"
TOPIC_DISTRICT_RISK = "district_risk"
TOPIC_DISTRICT_PRIORITY = "district_priority"
TOPIC_SUMMARY = "summary"
TOPIC_CONTRIBUTING = "contributing"
TOPIC_SHAP = "shap"
TOPIC_PLANNING = "planning"
TOPIC_RECENT_HMIS = "recent_hmis"
TOPIC_RECENT_RISK_CHANGE = "recent_risk_change"
TOPIC_AGGREGATE = "aggregate"
TOPIC_METHODOLOGY = "methodology"
TOPIC_DSS = "dss"
TOPIC_DATASET = "dataset"
TOPIC_PREPROCESSING = "preprocessing"
TOPIC_FEATURES = "features"
TOPIC_LIMITATIONS = "limitations"
TOPIC_CONCEPTUAL = "conceptual"
TOPIC_GENERAL = "general"
TOPIC_UNKNOWN = "unknown"

GROUNDED_TOPICS = {
    TOPIC_ABOUT, TOPIC_SYSTEM, TOPIC_DISTRICT_RISK, TOPIC_DISTRICT_PRIORITY,
    TOPIC_SUMMARY, TOPIC_CONTRIBUTING, TOPIC_SHAP, TOPIC_PLANNING,
    TOPIC_RECENT_HMIS, TOPIC_RECENT_RISK_CHANGE, TOPIC_AGGREGATE,
    TOPIC_METHODOLOGY, TOPIC_DSS, TOPIC_DATASET, TOPIC_PREPROCESSING,
    TOPIC_FEATURES, TOPIC_LIMITATIONS,
}
ALLOWED_TOPICS = GROUNDED_TOPICS | {TOPIC_CONCEPTUAL, TOPIC_GENERAL, TOPIC_UNKNOWN}

_FEATURE_INDEX = None
_STATE_INDEX = None


def _norm(value):
    s = re.sub(r"&", "and", str(value).lower())
    return re.sub(r"[^a-z0-9]", "", s)


def _label(feature):
    if not feature:
        return "—"
    return feature.replace("_Pct", "").replace("_", " ")


def _pct(value):
    if value is None:
        return "not available"
    if isinstance(value, float) and value != value:  # NaN
        return "not available"
    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return "not available"


# --------------------------------------------------------------------------- #
# District index / message parsing
# --------------------------------------------------------------------------- #
def _feature_index():
    global _FEATURE_INDEX
    if _FEATURE_INDEX is None:
        _FEATURE_INDEX = unified_service.get_unified_districts().get("districts", [])
    return _FEATURE_INDEX


def _mentions_district(message) -> str | None:
    """Return a district name from the index mentioned in the message."""
    text = _norm(message)
    for d in _feature_index():
        dn = _norm(d["district"])
        if len(dn) >= 5 and dn in text:
            return d["district"]
    return None


def _district_known(district: str) -> bool:
    target = _norm(district)
    return any(_norm(d["district"]) == target for d in _feature_index())


def _resolve_state(district: str) -> str | None:
    target = _norm(district)
    for d in _feature_index():
        if _norm(d["district"]) == target:
            return d.get("state")
    return None


def _resolve_message_district(message):
    """Return (state, district) mentioned in the message, best-effort."""
    text = _norm(message)
    candidates = [d for d in _feature_index()
                  if len(_norm(d["district"])) >= 5 and _norm(d["district"]) in text]
    if not candidates:
        return None, None
    state_found = "/".join(
        str(d["state"]) for d in _feature_index() if _norm(d["state"]) and _norm(d["state"]) in text
    )
    normalized_state_found = _norm(state_found)
    for d in candidates:
        if _norm(d["state"]) == normalized_state_found:
            return d["state"], d["district"]
    return candidates[0]["state"], candidates[0]["district"]


def _resolve_entities(message, state, district, scope):
    """Message mention > UI/map selection > previous-turn scope."""
    msg_state, msg_district = _resolve_message_district(message)
    if msg_district:
        return (msg_state or state or None), msg_district
    if district:
        return (state or None), district
    if scope and scope.get("district"):
        return (scope.get("state") or None), scope.get("district")
    return (state or None), district or None


# --------------------------------------------------------------------------- #
# Natural-language understanding
# --------------------------------------------------------------------------- #
def _is_general(text: str) -> bool:
    markers = [
        "capital of", "population of", "weather in", "who is the", "president of",
        "prime minister of", "currency of", "national anthem", "joke", "poem",
        "translate", "recipe for", "movie called", "what time", "what day",
        "good night", "sing me", "tell me a joke", "tell me a story",
    ]
    return any(m in text for m in markers)


def _concept_topic(text: str) -> str | None:
    """Map generic-but-project-relevant concept questions to a topic."""
    if any(w in text for w in (
        "difference between classification and clustering", "classification vs clustering",
        "difference between prediction and decision support", "prediction vs decision support",
        "supervised learning", "unsupervised learning", "explainable ai",
        "explainable artificial", "what is machine learning", "what are features",
        "what is a feature", "what is imputation", "what is a model",
    )):
        return TOPIC_CONCEPTUAL
    if any(w in text for w in ("k means", "k-means", "kmeans", "what is clustering", "clustering is")):
        return TOPIC_METHODOLOGY
    if any(w in text for w in ("logistic regression",)):
        return TOPIC_METHODOLOGY
    if any(w in text for w in ("what is shap", "what does shap", "shap is")):
        return TOPIC_SHAP
    if any(w in text for w in ("decision support system", "decision-support system",
                               "what is decision support")):
        return TOPIC_DSS
    if any(w in text for w in ("what is hmis", "what is a health management")):
        return TOPIC_DATASET
    return None


def _follow_up_topic(text: str, scope) -> str | None:
    if not scope or not scope.get("topic"):
        return None
    if any(w in text for w in ("hmis", "dataset 3", "recent data")):
        return TOPIC_RECENT_HMIS
    if any(w in text for w in ("change", "reclassif", "reassign", "update")):
        return TOPIC_RECENT_RISK_CHANGE
    if any(w in text for w in ("planning", "planner", "focus on", "do for")):
        return TOPIC_PLANNING
    if any(w in text for w in ("contribut", "factor", "driving", "made it", "indicators")):
        return TOPIC_CONTRIBUTING
    if any(w in text for w in ("priority",)):
        return TOPIC_DISTRICT_PRIORITY
    if any(w in text for w in ("risk",)):
        return TOPIC_DISTRICT_RISK
    return scope.get("topic") or None


def _understand_deterministic(message: str, page_context: str | None,
                              district: str | None, scope) -> tuple[str, str]:
    """Lightweight NLU fallback. Returns (topic, kind)."""
    text = " ".join((message or "").lower().split())
    has = lambda *words: any(w in text for w in words)  # noqa: E731

    if re.search(r"^(hi|hello|hey|how are you)\b", text) or has(
        "who are you", "what can you do", "how can you help"):
        return TOPIC_ABOUT, "grounded"

    if _is_general(text):
        return TOPIC_GENERAL, "general"

    if has("what is mrcdss", "what does mrcdss", "mrcdss stand for", "explain mrcdss",
           "about mrcdss", "what is this system", "what is this project", "what is this app",
           "tell me about the system", "system purpose"):
        return TOPIC_ABOUT, "grounded"

    if has("how does the whole system", "how does the entire system", "system architecture",
           "how the system fits together", "what is the input", "what is the output",
           "where does ai fit", "role of the", "how does the chatbot get", "how does the assistant",
           "what happens if the llm", "llm is unavailable", "what happens when ollama",
           "how do you get your answers", "how does disha", "what is the role of the"):
        return TOPIC_SYSTEM, "grounded"

    concept = _concept_topic(text)
    if concept:
        kind = "grounded" if concept in GROUNDED_TOPICS else "conceptual"
        return concept, kind

    if has("why was dataset 3 not", "why wasn", "why isn", "not used to retrain", "retrain"):
        return TOPIC_METHODOLOGY, "grounded"

    if has("change the historical risk", "change the risk classification", "hmis change the risk",
           "reassign", "reclassif", "change its risk", "risk change", "new hmis data",
           "new dataset 3", "hmis data change", "change the risk", "does the new hmis",
           "does that change", "does this change", "that change the classification",
           "this change the classification"):
        return TOPIC_RECENT_RISK_CHANGE, "grounded"

    dist_ref = bool(district) or _mentions_district(message) is not None
    if dist_ref:
        if has("hmis", "recent data") and not has("risk"):
            return TOPIC_RECENT_HMIS, "grounded"
        if has("planning", "planner", "focus on there", "what can a", "health planner",
               "do for", "planning focus"):
            return TOPIC_PLANNING, "grounded"
        if has("why"):
            return TOPIC_DISTRICT_RISK, "grounded"
        if has("what made", "what contributed", "contribut", "driving", "drivers",
               "main contributing", "key indicators", "which indicators",
               "contributing factors"):
            return TOPIC_CONTRIBUTING, "grounded"
        if has("priority"):
            return TOPIC_DISTRICT_PRIORITY, "grounded"
        if has("risk", "classified", "class", "category", "placed", "risky"):
            return TOPIC_DISTRICT_RISK, "grounded"
        if has("tell me about", "tell me what", "what is happening", "summary", "overview",
               "profile", "what do you know"):
            return TOPIC_SUMMARY, "grounded"
        return TOPIC_SUMMARY, "grounded"

    if has("risk classification", "what is the risk class", "risk level"):
        return TOPIC_DISTRICT_RISK, "grounded"

    if has("which indicators", "indicators matter", "main indicators", "important indicators",
           "top indicators", "most important"):
        return TOPIC_CONTRIBUTING, "grounded"

    if has("what is shap", "what does shap", "shap tell", "shap tells", "explain shap",
           "explain the model with shap", "feature importance", "explain the model",
           "explain result", "shapley"):
        return TOPIC_SHAP, "grounded"

    if has("planning focus", "planners focus", "planning priority", "what should planners",
           "focus on", "planning rules", "priority system", "priority level",
           "what is high priority", "what does high priority", "dss priority"):
        return TOPIC_PLANNING, "grounded"

    if has("which model", "what model", "model comparison", "selected model", "best model",
           "best performing", "compare", "logistic", "decision tree", "random forest",
           "xgboost", "accuracy", " f1", "roc", "model results", "model eval",
           "data split", "trained", "train/test", "train test", "evaluated",
           "why did you choose", "why logistic"):
        return TOPIC_METHODOLOGY, "grounded"

    if has("repeated priority", "repeated high priority", "repeated medium priority",
           "repeated low priority", "what does repeated", "repeated priority rule"):
        return TOPIC_AGGREGATE, "grounded"

    if has("latest assessment year", "latest year", "assessment year"):
        return TOPIC_AGGREGATE, "grounded"

    if has("clinically validated", "clinical validation", "is the model clinically",
           "clinical accuracy", "external validation"):
        return TOPIC_LIMITATIONS, "grounded"

    if has("k means", "k-means", "kmeans", "clustering", "cluster", "how were the risk",
           "how was the risk", "risk classes generated", "generated the risk",
           "how did you create the risk", "clinical labels", "are these clinical",
           "why three", "why did you use k"):
        return TOPIC_METHODOLOGY, "grounded"

    if has("which features", "feature selection", "final features", "six features",
           "feature set", "why did you remove ifa", "ifa", "sba home delivery",
           "why was severe anemia", "indicators did you use", "selected features",
           "candidate features", "features did you use", "features are used"):
        return TOPIC_FEATURES, "grounded"

    if has("preprocess", "clean the data", "cleaning", "missing values", "imputation",
           "imput", "invalid percentage", "how did you handle", "schemas", "identical",
           "load/combine", "cleaned the data"):
        return TOPIC_PREPROCESSING, "grounded"

    if has("limitations", "limitation", "diagnose a patient", "patient diagnosis",
           "clinical advice", "predict maternal mortality", "predict outcomes",
           "prove causation", "external validation", "can this diagnose",
           "does this diagnose", "is this a clinical"):
        return TOPIC_LIMITATIONS, "grounded"

    if has("what are you doing with the data", "what data are you using", "where did the data",
           "data come from", "data sources", "how many records", "record-years", "how many years",
           "years are covered", "years covered", "how many states", "district-state",
           "district state", "records do you have", "how much data", "what years",
           "what is dataset 3", "dataset 3", "why did you add recent hmis", "why did you add",
           "original datasets", "what happened to the original", "hmis is unavailable",
           "difference between the historical", "what data" ):
        return TOPIC_DATASET, "grounded"

    if has("recent hmis", "hmis evidence", "hmis data", "latest hmis", "latest anc",
           "latest tt2", "anemia", "obstetric complication", "current evidence", "hmis",
           "recent data"):
        return TOPIC_RECENT_HMIS, "grounded"

    if has("decision support", "dss", "decision rules"):
        return TOPIC_DSS, "grounded"

    if has("how many", "which districts", "number of", "most common", "distribution",
           "count", "total districts", "list of districts", "high risk districts",
           "high priority districts", "priorities are high"):
        return TOPIC_AGGREGATE, "grounded"

    if has("tell me about", "about mrcdss", "what is mrcdss"):
        return TOPIC_ABOUT, "grounded"

    return TOPIC_UNKNOWN, "grounded"


def _llm_prompt_understand(message, scope, history):
    lines = [
        "You are the question-understanding stage of Disha, the MRCDSS Decision Assistant.",
        "Classify the user's latest message into exactly one topic from this list:",
        ", ".join(sorted(ALLOWED_TOPICS)) + ".",
        "Guidelines:",
        "- Choose 'general' only when the question is unrelated to MRCDSS (e.g. 'What is the capital of France?').",
        "- Choose 'conceptual' for generic ML/AI concepts such as supervised learning or explainable AI.",
        "- For a question about a district, give the district name (and state if known) exactly as it would appear in an index, otherwise null.",
        "- Use the conversation scope to resolve follow-ups like 'its recent HMIS' or 'does that change the classification?'",
        "Return ONLY JSON: {\"topic\": \"...\", \"district\": \"...\" or null, \"state\": \"...\" or null}",
    ]
    if scope:
        lines.append(f"Conversation scope: {json.dumps(scope)}")
    if history:
        lines.append("Conversation history:\n" + "\n".join(
            f"- {h.get('role', '?')}: {h.get('text', '')}" for h in history[-6:]))
    lines.append(f"User message: {message}")
    return "\n".join(lines)


def _safe_llm_json(prompt):
    try:
        raw = _llm_chat(prompt)
    except Exception:
        return None
    if not raw:
        return None
    text = raw.strip()
    text = text.strip("`")
    if text.startswith("json"):
        text = text[4:].strip()
    try:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            return None
        data = json.loads(text[start:end + 1])
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    return data


def _validate_llm_topic(topic, district, state):
    if topic not in ALLOWED_TOPICS:
        topic = None
    if district:
        try:
            if not _district_known(district):
                district = None
        except Exception:
            district = None
        if district and not state:
            state = _resolve_state(district)
    return topic, district, state


def _understand(message, page_context, state, district, scope, history):
    """NLU entry point: LLM-driven when available, deterministic otherwise."""
    topic, kind = _understand_deterministic(message, page_context, district, scope)
    if not _ollama_active():
        return topic, kind, state, district

    data = _safe_llm_json(_llm_prompt_understand(message, scope, history))
    if data is None:
        return topic, kind, state, district

    t, d, s = _validate_llm_topic(data.get("topic"), data.get("district"), data.get("state"))
    if t:
        topic = t
        kind = "grounded" if t in GROUNDED_TOPICS else ("general" if t == TOPIC_GENERAL else "conceptual")
    if d:
        district = d
        if s:
            state = s
    return topic, kind, state, district


def detect_intent(message: str, page_context: str | None = None) -> str:
    """Backwards-compatible classifier (deterministic only)."""
    topic, _kind = _understand_deterministic(message, page_context, None, None)
    return topic


# --------------------------------------------------------------------------- #
# Retrieval
# --------------------------------------------------------------------------- #
def build_district_context(state: str | None, district: str | None) -> dict | None:
    """Retrieve the unified MRCDSS profile for a State+District from the dataset."""
    if not district:
        return None
    if not state:
        state = _resolve_state(district)
    detail = unified_service.get_unified_district(state or "", district)
    if not detail.get("matched"):
        return {
            "matched": False,
            "state": state,
            "district": district,
            "known": bool(state and not detail.get("matched")) or _district_known(district),
        }
    historical = detail.get("historical") or []
    recent = detail.get("recent") or []
    latest_hist = historical[-1] if historical else None
    latest_rec = recent[-1] if recent else None
    context = {
        "matched": True,
        "state": detail.get("state") or state,
        "district": detail.get("district") or district,
        "known": True,
        "historical_records": len(historical),
        "historical_years": sorted({str(r["Year"]) for r in historical}),
        "recent_records": len(recent),
        "recent_years": sorted({str(r["Year"]) for r in recent}),
    }
    if latest_hist is not None:
        context.update({
            "latest_historical_year": str(latest_hist["Year"]),
            "risk_class": latest_hist.get("risk_class"),
            "priority": latest_hist.get("priority_level"),
            "top_contributing": [
                latest_hist.get("top_contributing_feature_1"),
                latest_hist.get("top_contributing_feature_2"),
                latest_hist.get("top_contributing_feature_3"),
            ],
            "planning_focus": [
                latest_hist.get("planning_focus_1"),
                latest_hist.get("planning_focus_2"),
                latest_hist.get("planning_focus_3"),
            ],
        })
    if latest_rec is not None:
        context["latest_recent"] = {
            "year": str(latest_rec["Year"]),
            "ANC_First_Trimester_Pct": latest_rec.get("ANC_First_Trimester_Pct"),
            "TT2_Booster_Pct": latest_rec.get("TT2_Booster_Pct"),
            "Severe_Anemia_Pct": latest_rec.get("Severe_Anemia_Pct"),
            "Obstetric_Complications_Pct": latest_rec.get("Obstetric_Complications_Pct"),
            "indicator_definition_status": latest_rec.get("indicator_definition_status"),
            "hmis_source_file": latest_rec.get("hmis_source_file"),
        }
    return context


def _global_shap_ranking():
    return [r["feature"] for r in (overview_service.get_overview_data().get("feature_ranking") or [])]


def _priority_summary():
    return planning_service.get_planning_priorities().get("repeated_priority_info", {})


def _risk_counts():
    counts = {"High Risk": 0, "Medium Risk": 0, "Low Risk": 0}
    for d in _feature_index():
        rc = d.get("latest_historical_risk_class")
        if rc in counts:
            counts[rc] += 1
    return counts


def _high_priority_district_names(limit=15):
    try:
        from services import districts_service
        res = districts_service.get_latest_district_observations()
    except Exception:
        return []
    latest_high = [
        r for r in res.get("records", [])
        if r.get("priority") == "High Priority"
    ]
    latest_high.sort(key=lambda r: (str(r.get("state")), str(r.get("district"))))
    return [
        f"{r.get('district')} ({r.get('state')})"
        for r in latest_high[:limit]
    ]


def _districts_by_latest_risk_class(risk_class: str, limit: int = 10):
    """Return district names from the latest historical observation, filtered by risk class."""
    try:
        from services import districts_service
        res = districts_service.get_latest_district_observations()
    except Exception:
        return [], 0
    matched = [
        r for r in res.get("records", [])
        if r.get("risk_class") == f"{risk_class} Risk"
    ]
    matched.sort(key=lambda r: (str(r.get("state")), str(r.get("district"))))
    names = [f"{r.get('district')} ({r.get('state')})" for r in matched[:limit]]
    return names, len(matched)


def _latest_assessment_year():
    """Return the latest historical assessment year."""
    try:
        from services import districts_service
        res = districts_service.get_latest_district_observations()
    except Exception:
        return None
    records = res.get("records", [])
    if not records:
        return None
    years = [int(r.get("year", 0)) for r in records if r.get("year")]
    return max(years) if years else None


# --------------------------------------------------------------------------- #
# Deterministic grounded drafts (also used as the LLM's answer scaffolding)
# --------------------------------------------------------------------------- #
def _years_text(years):
    yrs = [str(y) for y in years]
    if len(yrs) == 1:
        return yrs[0]
    if len(yrs) == 2:
        return f"{yrs[0]}–{yrs[1]}"
    return f"{yrs[0]}–{yrs[-1]}"


def _district_line(ctx: dict, include_priority=True) -> str:
    name = f"{ctx['district']} ({ctx['state']})"
    if not ctx.get("risk_class") or not ctx.get("priority"):
        years = ""
        if ctx.get("historical_years"):
            years = ", historical records for " + _years_text(ctx["historical_years"])
        return (f"The unified MRCDSS dataset contains recent HMIS records for {name} but no "
                f"derived historical MRCDSS risk classification{years}.")
    parts = [f"{name} is classified as {ctx['risk_class']}"]
    if include_priority:
        parts.append(f"{ctx['priority']}")
    parts.append(f"at the latest historical assessment year {ctx.get('latest_historical_year')}")
    if ctx.get("historical_years"):
        parts.append(f"covering {_years_text(ctx['historical_years'])}")
    return " ".join(part if part.endswith(".") else part + "." for part in parts) + " "


def _unmatched(ctx) -> bool:
    return ctx is not None and not ctx.get("matched")


def _select_hint() -> tuple:
    return (
        "Ask about a specific district (for example \"What is the risk classification of "
        "Warangal?\") or select a district on the map so the assistant can focus on it.",
        True, [],
    )


def _dispatch(topic: str, message: str, ctx: dict | None):
    if topic == TOPIC_ABOUT:
        return (
            "MRCDSS (Maternal Health Risk Decision Support System) is a district-level maternal-health "
            "decision-support system. It derives risk profiles (Low, Medium, High) from historical "
            "district-year records (2008–2019) using K-Means clustering and supervised models, and maps "
            "them to planning priorities. Dataset 3 adds Recent HMIS evidence (2020–2025) as context. "
            "It supports district health planning, not clinical diagnoses.",
            True, [SOURCE_METHODOLOGY],
        )

    if topic == TOPIC_DISTRICT_RISK:
        return _district_risk_answer(ctx, message)

    if topic == TOPIC_DISTRICT_PRIORITY:
        return _district_priority_answer(ctx)

    if topic == TOPIC_SUMMARY:
        return _district_summary_answer(ctx)

    if topic == TOPIC_CONTRIBUTING:
        return _contributing_answer(ctx)

    if topic == TOPIC_SHAP:
        return _shap_answer(ctx)

    if topic == TOPIC_PLANNING:
        return _planning_answer(ctx)

    if topic == TOPIC_RECENT_HMIS:
        return _recent_hmis_answer(ctx)

    if topic == TOPIC_RECENT_RISK_CHANGE:
        return _recent_risk_change_answer(ctx)

    if topic == TOPIC_AGGREGATE:
        return _aggregate_answer(message)

    if topic == TOPIC_METHODOLOGY:
        return _methodology_answer(message)

    if topic == TOPIC_DSS:
        return (
            "The Decision Support System (DSS) maps each district's risk class and its SHAP contributing "
            "features into a priority level (High / Medium / Low priority) and planning focus areas using "
            "transparent rule-based mappings. Planning focus areas represent district/public-health planning "
            "priorities; they are not individual medical advice, patient diagnosis, or treatment "
            "recommendations.",
            True, [SOURCE_PLANNING],
        )

    if topic == TOPIC_DATASET:
        return _dataset_answer(message)

    if topic == TOPIC_PREPROCESSING:
        return _preprocessing_answer()

    if topic == TOPIC_FEATURES:
        return _features_answer(message)

    if topic == TOPIC_LIMITATIONS:
        return _limitations_answer()

    if topic == TOPIC_SYSTEM:
        return _system_answer()

    if topic == TOPIC_CONCEPTUAL:
        return _conceptual_answer(message)

    if topic == TOPIC_GENERAL:
        return (
            "General AI responses are unavailable because the local LLM (Ollama) is not running. "
            "MRCDSS-related questions can still be answered from the retrieved evidence.",
            False, [],
        )

    return NOT_AVAILABLE, False, []


def _district_summary_answer(ctx):
    if ctx is None:
        return _select_hint()
    if _unmatched(ctx):
        return NOT_AVAILABLE, False, []
    answer = _district_line(ctx)
    if ctx.get("top_contributing"):
        features = ", ".join(_label(f) for f in ctx["top_contributing"] if f)
        answer += f"Key contributing indicators: {features}. "
    if ctx.get("planning_focus"):
        focus = "; ".join(f for f in ctx["planning_focus"] if f)
        answer += f"Planning focus: {focus}. "
    if ctx.get("latest_recent"):
        answer += (f"Latest Recent HMIS evidence for {ctx['district']} ({ctx['state']}) is from "
                   f"{ctx['latest_recent']['year']}; it was not used to assign the historical risk class.")
    return answer, True, [SOURCE_DISTRICT, SOURCE_RECENT]


def _district_risk_answer(ctx, message=""):
    if ctx is None:
        return _select_hint()
    if _unmatched(ctx):
        return NOT_AVAILABLE, False, []
    if ctx.get("risk_class") is None:
        return (_district_line(ctx), True, [SOURCE_DISTRICT])
    answer = _district_line(ctx, include_priority=("priority" not in message.lower()))
    if "why" in message.lower() and ctx.get("top_contributing"):
        features = ", ".join(_label(f) for f in ctx["top_contributing"] if f)
        answer += (f"Key contributing indicators for this classification: {features}. "
                   "SHAP values indicate contribution to the model classification, not causation. ")
    answer += ("Risk classes are derived analytical groups from the historical MRCDSS methodology; "
               "they are not clinical diagnoses.")
    return answer, True, [SOURCE_DISTRICT, *([SOURCE_SHAP] if "why" in message.lower() else [])]


def _district_priority_answer(ctx):
    if ctx is None:
        return _select_hint()
    if _unmatched(ctx):
        return NOT_AVAILABLE, False, []
    if ctx.get("priority") is None:
        return (_district_line(ctx), True, [SOURCE_DISTRICT])
    answer = (f"{ctx['district']} ({ctx['state']}) is assigned {ctx['priority']} by the MRCDSS "
              f"Decision Support System, based on the {ctx['risk_class']} classification at assessment "
              f"year {ctx.get('latest_historical_year')}. Priority reflects district planning attention "
              "within the DSS.")
    return answer, True, [SOURCE_DISTRICT]


def _contributing_answer(ctx):
    if ctx is not None and ctx.get("matched") and ctx.get("top_contributing"):
        features = ", ".join(_label(f) for f in ctx["top_contributing"] if f)
        answer = (f"Based on the MRCDSS model, the indicators that most contributed to the "
                  f"classification of {ctx['district']} ({ctx['state']}) were {features}. ")
        answer += ("SHAP values indicate contribution to the model classification, not causation.")
        return answer, True, [SOURCE_SHAP, SOURCE_DISTRICT]
    top = [r["feature"] for r in overview_service.get_overview_data().get("feature_ranking", [])][:3]
    features = ", ".join(_label(f) for f in top)
    answer = (f"Across the MRCDSS model, the indicators with the highest mean absolute SHAP "
              f"contribution are {features}. ")
    answer += ("SHAP values indicate model attribution; the global summary separates positive and "
               "negative contributions to the High Risk class, but signed district-specific direction "
               "is not stored for this detail. SHAP does not establish causation.")
    return answer, True, [SOURCE_SHAP]


def _shap_answer(ctx):
    top = _global_shap_ranking()[:3]
    answer = (
        "SHAP (SHapley Additive exPlanations) values show how much each feature contributed to the "
        "Logistic Regression model output. The saved global test-set explanation is for the High Risk "
        "class: positive values push toward High Risk and negative values push away from it. "
    )
    if top:
        answer += f"Across all test records, the highest mean absolute SHAP values are for {', '.join(_label(f) for f in top)}. "
    answer += ("SHAP values indicate model attribution, not causation, and global summaries are not "
               "signed explanations for an individual district-year record.")
    if ctx is not None and ctx.get("matched") and ctx.get("top_contributing"):
        features = ", ".join(_label(f) for f in ctx["top_contributing"] if f)
        answer += (f" For {ctx['district']} ({ctx['state']}), the saved top contributors are {features}; "
                   "their signed district-specific direction is not available in this detail view.")
    return answer, True, [SOURCE_SHAP]


def _planning_answer(ctx):
    if ctx is not None and _unmatched(ctx):
        return NOT_AVAILABLE, False, []
    if ctx is not None and ctx.get("matched"):
        if ctx.get("planning_focus"):
            focus = "; ".join(f for f in ctx["planning_focus"] if f)
            answer = (f"The planning focus for {ctx['district']} ({ctx['state']}) is: {focus}. "
                      "Planning focus areas are district/public-health planning priorities from the "
                      "MRCDSS Decision Support System, not individual medical advice or treatment "
                      "recommendations.")
        else:
            answer = (f"The unified MRCDSS dataset has recent HMIS records for {ctx['district']} "
                      f"({ctx['state']}) but no historical DSS planning focus is available.")
        return answer, True, [SOURCE_PLANNING, SOURCE_DISTRICT]
    planning = planning_service.get_planning_priorities()
    focus_parts = []
    for rule in planning.get("planning_rules", [])[:4]:
        focus_parts.append(f"{_label(rule.get('feature', ''))} → {rule.get('planning_focus', '')}")
    answer = "The MRCDSS planning rules map each indicator to a planning focus area: " + "; ".join(focus_parts) + ". "
    counts = planning.get("feature_planning_focus_counts", [])
    if counts:
        top = [c["feature"] for c in counts[:3]]
        answer += ("The indicators appearing most often among the model's top-three contributors "
                   f"across historical district-year records are {', '.join(_label(f) for f in top)}. "
                   "These are model-attributed planning focuses, not a verified needs assessment.")
    return answer, True, [SOURCE_PLANNING]


def _recent_hmis_answer(ctx):
    if ctx is not None and ctx.get("matched") and ctx.get("latest_recent"):
        rec = ctx["latest_recent"]
        parts = [f"The latest Recent HMIS evidence for {ctx['district']} ({ctx['state']}) is from {rec['year']}:"]
        rows = [
            ("ANC First Trimester", rec.get("ANC_First_Trimester_Pct")),
            ("TT2 / Booster", rec.get("TT2_Booster_Pct")),
            ("Severe Anemia", rec.get("Severe_Anemia_Pct")),
            ("Obstetric Complications", rec.get("Obstetric_Complications_Pct")),
        ]
        parts.append("; ".join(f"{label} {_pct(v)}" for label, v in rows))
        if rec.get("indicator_definition_status"):
            parts.append(rec["indicator_definition_status"])
        if rec.get("hmis_source_file"):
            parts.append(f"Source file: {rec['hmis_source_file']}")
        answer = " ".join(parts) + ". "
        if ctx.get("risk_class"):
            answer += (f"This recent HMIS evidence was not used to assign the historical MRCDSS risk "
                       f"class ({ctx['risk_class']}) and does not change it.")
        else:
            answer += "Recent HMIS records carry no High / Medium / Low MRCDSS risk label."
        return answer, True, [SOURCE_RECENT, SOURCE_DISTRICT]

    if ctx is not None and ctx.get("matched"):
        return (f"No Recent HMIS observations are currently available for {ctx['district']} "
                f"({ctx['state']}) in the unified dataset.", True, [SOURCE_RECENT])

    if ctx is not None:
        return NOT_AVAILABLE, False, []

    overview = unified_service.get_unified_overview()
    availability = {f["key"]: f["recent_valid"] for f in overview.get("feature_availability", [])}
    answer = (
        "The Recent HMIS extension (Dataset 3, 2020–2025) provides district-level indicator evidence: "
        f"ANC First Trimester is available for {availability.get('ANC_First_Trimester_Pct', 0):,} "
        f"record-years, TT2 / Booster for {availability.get('TT2_Booster_Pct', 0):,}, Severe Anemia for "
        f"{availability.get('Severe_Anemia_Pct', 0):,}, and Obstetric Complications through 2022-23 for "
        f"{availability.get('Obstetric_Complications_Pct', 0):,}. "
        "Recent HMIS is reported as indicator evidence only and was not used to retrain the historical "
        "model."
    )
    return answer, True, [SOURCE_RECENT]


def _recent_risk_change_answer(ctx):
    base = ("No. Recent HMIS evidence was not used to retrain the historical MRCDSS model and is never "
            "used to assign or change a district's historical risk classification.")
    if ctx is not None and ctx.get("matched"):
        if ctx.get("risk_class"):
            return (f"{base} {ctx['district']} ({ctx['state']}) retains its historical MRCDSS class of "
                    f"{ctx['risk_class']}. Recent HMIS records carry no High / Medium / Low MRCDSS risk label.",
                    True, [SOURCE_RECENT, SOURCE_DISTRICT])
        return (f"{base} Historical risk classes (Low / Medium / High) come only from the derived "
                "historical MRCDSS methodology (Datasets 1 and 2).", True, [SOURCE_RECENT, SOURCE_METHODOLOGY])
    return (f"{base} Historical risk classes (Low / Medium / High) come only from the derived "
            "historical MRCDSS methodology (Datasets 1 and 2); Dataset 3 adds evidence without new "
            "risk labels.", True, [SOURCE_RECENT, SOURCE_METHODOLOGY])


def _aggregate_answer(message):
    text = " ".join((message or "").lower().split())
    counts = _risk_counts()
    latest_year = _latest_assessment_year()
    period = f"latest historical assessment ({latest_year})" if latest_year else "latest historical assessment"

    # --- District list questions ---
    if "low risk" in text and ("which" in text or "districts" in text or "list" in text):
        names, total = _districts_by_latest_risk_class("Low")
        if not names:
            return (f"No Low Risk districts found in {period}.", True, [SOURCE_DISTRICT])
        listed = ", ".join(names)
        extra = f" Showing first {len(names)} of {total:,}." if total > len(names) else ""
        return (
            f"Low Risk districts in {period}: {listed}.{extra} "
            f"{'Would you like the remaining districts?' if total > len(names) else ''}",
            True, [SOURCE_DISTRICT],
        )

    if "high risk" in text and ("which" in text or "districts" in text or "list" in text):
        names, total = _districts_by_latest_risk_class("High")
        if not names:
            return (f"No High Risk districts found in {period}.", True, [SOURCE_DISTRICT])
        listed = ", ".join(names)
        extra = f" Showing first {len(names)} of {total:,}." if total > len(names) else ""
        return (
            f"High Risk districts in {period}: {listed}.{extra} "
            f"{'Would you like the remaining districts?' if total > len(names) else ''}",
            True, [SOURCE_DISTRICT],
        )

    # --- Count questions ---
    if "medium risk" in text and ("how many" in text or "count" in text):
        return (
            f"{counts['Medium Risk']:,} of {sum(counts.values()):,} districts are Medium Risk "
            f"in {period}.",
            True, [SOURCE_DISTRICT],
        )

    if "high risk" in text and ("how many" in text or "count" in text):
        return (
            f"{counts['High Risk']:,} of {sum(counts.values()):,} districts are High Risk "
            f"in {period}.",
            True, [SOURCE_DISTRICT],
        )

    if "low risk" in text and ("how many" in text or "count" in text):
        return (
            f"{counts['Low Risk']:,} of {sum(counts.values()):,} districts are Low Risk "
            f"in {period}.",
            True, [SOURCE_DISTRICT],
        )

    # --- Repeated priority question ---
    if "repeated" in text and "high priority" in text:
        summary = _priority_summary()
        total = summary.get("total_units", 0)
        repeated_high = summary.get("repeated_high", 0)
        return (
            f"Repeated High Priority means a district was classified High Priority in at least "
            f"two historical district-year records. It does not require consecutive years, and "
            f"it is not the latest priority. {repeated_high:,} of {total:,} units meet this rule.",
            True, [SOURCE_PLANNING],
        )

    # --- Latest assessment year ---
    if ("latest" in text and "year" in text) or "assessment year" in text:
        if latest_year:
            return (
                f"The latest historical MRCDSS assessment year is {latest_year}.",
                True, [SOURCE_DISTRICT],
            )
        return (NOT_AVAILABLE, False, [])

    # --- General aggregate summary (only when no specific intent detected) ---
    summary = _priority_summary()
    total = summary.get("total_units", 0)
    parts = []
    if total:
        parts.append(
            f"{total:,} State–District units are covered historically. "
            f"{summary.get('repeated_high', 0):,} meet the repeated High Priority rule, "
            f"{summary.get('repeated_medium', 0):,} repeated Medium, "
            f"{summary.get('repeated_low', 0):,} repeated Low."
        )
    parts.append(
        f"By latest historical risk classification: {counts['High Risk']:,} High Risk, "
        f"{counts['Medium Risk']:,} Medium Risk, {counts['Low Risk']:,} Low Risk."
    )
    answer = " ".join(parts)
    return answer, True, [SOURCE_DISTRICT]


def _model_comparison_text():
    try:
        analysis = risk_analysis_service.get_risk_analysis()
    except Exception:
        return None
    models = analysis.get("model_comparison", [])
    if not models:
        return None
    lines = []
    for m in models:
        parts = [m.get("model", "?")]
        if m.get("accuracy") is not None:
            parts.append(f"accuracy {float(m['accuracy']):.4f}")
        if m.get("f1") is not None:
            parts.append(f"F1 {float(m['f1']):.4f}")
        if m.get("roc_auc") is not None:
            parts.append(f"ROC-AUC {float(m['roc_auc']):.6f}")
        lines.append("; ".join(parts))
    return "; ".join(lines)


def _methodology_answer(message):
    text = " ".join((message or "").lower().split())

    if any(w in text for w in ("retrain", "why wasn", "why not", "not used to retrain", "dataset 3")):
        return (
            "Dataset 3 (Recent HMIS) was not used to retrain the historical MRCDSS model because several "
            "indicator definitions are not directly comparable across the periods — for example the "
            "Severe Anemia Hb threshold changed (<7 g/dl to <=7 g/dl from 2023-24), and Institutional "
            "Delivery and PNC within 48h are not available in a comparable form in Dataset 3. This keeps "
            "the historical analytical artifacts unchanged while recent HMIS adds contextual evidence; "
            "it also avoids implying that the historical labels are clinically validated.",
            True, [SOURCE_METHODOLOGY],
        )

    if any(w in text for w in ("logistic", "model comparison", "selected", "evaluated", "accuracy",
                               "which model", "what model", "data split", "trained", "best")):
        return _model_methodology_answer()

    if any(w in text for w in ("k means", "k-means", "kmeans", "cluster", "generated",
                               "how was risk", "how were the risk", "risk class", "clinical")):
        return _clustering_methodology_answer()

    if any(w in text for w in ("feature set", "six feature", "what data", "dataset 1",
                               "dataset 2", "indicators used", "features")):
        return _data_methodology_answer()

    if any(w in text for w in ("shap", "shapley")):
        return _shap_methodology_answer()

    overview = overview_service.get_overview_data()
    answer = (
        "MRCDSS processes district-level maternal-health records into selected analytical features, derives "
        "risk profiles with K-Means, replicates them with supervised models, explains classifications with "
        "SHAP, and maps results to planning priorities via a rule-based Decision Support System. "
    )
    answer += (f"The historical dataset covers {overview.get('year_coverage', {}).get('start')}"
               f"–{overview.get('year_coverage', {}).get('end')} with 7 documented methodology "
               "components.")
    return answer, True, [SOURCE_METHODOLOGY]


def _model_methodology_answer():
    metrics = {}
    try:
        analysis = risk_analysis_service.get_risk_analysis()
        for m in analysis.get("model_comparison", []):
            if m.get("model") == "Logistic Regression":
                metrics = m
                break
    except Exception:
        metrics = {}
    answer = (
        "Logistic Regression was selected by macro-F1. It was trained to replicate the K-Means-derived "
        "risk classes using the same six-feature space on a record-level 80/20 split. The reported "
        "metrics measure label reproduction on seen units, not clinical prediction accuracy."
    )
    if metrics.get("accuracy") is not None:
        answer += (
            f" Logistic Regression reports accuracy {metrics['accuracy']:.4f} "
            f"(macro-F1 {metrics.get('f1', 0):.4f}, macro ROC-AUC {metrics.get('roc_auc', 0):.6f})."
        )
    answer += " Grouped or temporal validation and external clinical validation have not been performed."
    return answer, True, [SOURCE_METHODOLOGY]


def _clustering_methodology_answer():
    answer = (
        "Risk classes were derived using K-Means clustering (K=3, random_state=42, n_init=10) on "
        "StandardScaler-normalized features from six selected maternal-health indicators. K=3 was fixed "
        "for the Low/Medium/High design rather than selected through a full K-selection diagnostic. The "
        "clusters are derived analytical groups, not clinical diagnoses."
    )
    val = next((i["value"] for i in methodology_service.get_methodology().get("items", [])
                if i.get("title") == "K-Means Clustering"), "")
    m = re.search(r"Silhouette=([0-9.]+)", val)
    if m:
        answer += (f" Silhouette {m.group(1)} indicates weak-to-moderate separation, not strong cluster "
                   "structure. Excluding Severe Anemia changes the risk class of 54.35% of records, so "
                   "the labels are sensitive to feature choice.")
    return answer, True, [SOURCE_METHODOLOGY]


def _data_methodology_answer():
    answer = (
        "MRCDSS uses district-level maternal-health records. Six final features are used: ANC First "
        "Trimester, TT2 / Booster, Severe Anemia, Institutional Delivery, PNC within 48h, and Obstetric "
        "Complications. Dataset 1 + Dataset 2 form the historical modelling period (2008–2019); Dataset 3 "
        "extends the system with Recent HMIS evidence (2020–2025)."
    )
    return answer, True, [SOURCE_METHODOLOGY]


def _shap_methodology_answer():
    return (
        "SHAP (SHapley Additive exPlanations) explains how much each feature contributed to the Logistic "
        "Regression model's classification of each district-year record. SHAP values indicate "
        "contribution direction and magnitude to the model classification, not causation.",
        True, [SOURCE_SHAP, SOURCE_METHODOLOGY],
    )


def _dataset_answer(message):
    text = " ".join((message or "").lower().split())
    parts = []
    overview = unified_service.get_unified_overview()
    counts = overview.get("counts_by_source", {})
    parts.append(
        "The unified MRCDSS dataset combines the historical MRCDSS records (Dataset 1 + Dataset 2, "
        f"{_years_text(overview.get('historical_years') or [])}) with a Recent HMIS extension "
        f"(Dataset 3, {_years_text(overview.get('recent_years') or [])})."
    )
    units = overview.get("n_state_district_units")
    states = overview.get("n_states")
    if units is not None and states is not None:
        parts.append(f"It holds {overview.get('total_observations', 0):,} district-year observations across "
                     f"{states:,} states and {units:,} district-state units.")
    if counts:
        parts.append(
            "Composition: " + ", ".join(
                f"{k} {v:,}" for k, v in counts.items() if isinstance(v, int)
            ) + "."
        )
    if "difference between the historical" in text or "differences between" in text:
        parts.append(
            "Historical records (Datasets 1/2) carry their original derived High/Medium/Low MRCDSS risk "
            "class and the full six-feature signal; Recent HMIS (Dataset 3) carries current indicator values only — no "
            "risk classes are assigned — and several indicator definitions differ (Severe Anemia Hb "
            "threshold changed from <7 to <=7; Institutional Delivery and PNC within 48h are not "
            "comparable in Dataset 3; Obstetric Complications only through 2022-23)."
        )
    if "unavailable" in text or "not available" in text:
        parts.append(
            "When Recent HMIS values are unavailable — an excluded indicator, a district without coverage, "
            "the partial 2024-25 year (17 states), or the excluded 2025-26 downloads — the indicator is "
            "reported as not available and no inference or risk re-assignment is made."
        )
    coverage = recent_hmis_service.get_recent_hmis_overview()
    notes = coverage.get("notes", {})
    if notes:
        parts.append(
            f"Dataset 3 coverage notes: {notes.get('partial_2024_2025', '')}; {notes.get('not_included_2025_2026', '')}."
        )
    try:
        cov = recent_hmis_service.get_recent_hmis_coverage()
        cand = cov.get("district_coverage", {})
        if cand:
            identity = overview.get("identity_reconciliation", {})
            parts.append(
                f"After alias/format normalization, Dataset 3 uses {cand.get('dataset_3_distinct_identifiers', '')} "
                f"distinct State–District units vs the {cand.get('reference_707_units', '')} historical "
                f"reference units; the difference includes newly reported districts and genuine coverage "
                f"change, not just spelling variants. The unified dataset has "
                f"{identity.get('raw_state_district_entries', '')} raw State/District entries collapsing "
                f"to {identity.get('normalized_state_district_units', '')} normalized units."
            )
    except Exception:
        pass
    answer = " ".join(p for p in parts if p)
    if not answer:
        return NOT_AVAILABLE, False, []
    return answer, True, [SOURCE_METHODOLOGY, SOURCE_RECENT]


def _preprocessing_answer():
    answer = (
        "Cleaning: duplicates and empty rows were removed, and all-null columns were dropped. "
        "The final cleaned dataset has 8,405 rows × 290 columns. "
        "Missing values before cleaning: 126,911 (Dataset 1: 104,715; Dataset 2: 22,196). "
        "Invalid percentage values (outside 0–100) — 33,012 cells — were set to null. "
        "Before imputation, 1,117,706 cells were null (original missing 126,911 + invalid→null 33,012 + "
        "Dataset 1/2 column misalignment 957,783). "
        "All remaining nulls were filled with the column median; remaining missing values: 0. "
        "Dataset 1 and Dataset 2 use different column layouts and spellings, so each feature was "
        "reconstructed by mapping the equivalent indicators across the two schemas into a shared space."
    )
    return answer, True, [SOURCE_METHODOLOGY]


def _features_answer(message):
    text = " ".join((message or "").lower().split())
    answer = (
        "The final feature set is six selected maternal-health indicators: ANC First Trimester, "
        "TT2 / Booster, Severe Anemia, Institutional Delivery, PNC within 48h, and Obstetric Complications. "
    )
    if any(w in text for w in ("ifa", "sba")):
        answer += (
            "IFA (100-tablet indicator in Dataset 1 vs 180-tablet in Dataset 2) and SBA Home Delivery "
            "(denominator/definition changed between the two schemas) were evaluated as candidate features "
            "but excluded from the final set because the two source datasets defined them differently. "
        )
    else:
        answer += "These six were chosen because they are present and comparably defined in Datasets 1 and 2. "
    answer += (
        "Severe Anemia was retained despite cross-dataset harmonization uncertainty (D1 median 3.6% vs "
        "D2 median 51.5%). A sensitivity analysis excluding it changes the risk class of 54.35% of "
        "records; the similar silhouette values (0.231 vs 0.238) do not demonstrate label robustness. "
        "Higher values indicate higher risk for Severe Anemia and Obstetric Complications; lower values "
        "indicate higher risk for the ANC, TT2, Institutional Delivery, and PNC indicators."
    )
    return answer, True, [SOURCE_METHODOLOGY]


def _limitations_answer():
    answer = (
        "Documented limitations: risk classes are derived analytical groups, not clinical diagnoses or "
        "ground truth; the system does not diagnose patients, treat anyone, or predict individual "
        "outcomes such as maternal mortality; SHAP explains model behavior, not causation; there is no "
        "external clinical validation of the derived classes; Recent HMIS (Dataset 3) was not used to "
        "retrain or re-classify and is not directly comparable to the historical indicators (definition "
        "and schema changes, partial 2024-25 coverage for 17 states, 2025-26 excluded); planning focus "
        "areas are public-health planning guidance, not individual medical recommendations."
    )
    return answer, True, [SOURCE_METHODOLOGY, SOURCE_RECENT]


def _system_answer():
    answer = (
        "End to end, MRCDSS: (1) preprocesses district-year maternal-health records from Datasets 1 and 2; "
        "(2) selects six selected indicators; (3) derives risk classes with K-Means clustering; "
        "(4) trains supervised models (Logistic Regression, Decision Tree, Random Forest, XGBoost) to "
        "replicate the classes; (5) explains each classification with SHAP; and (6) maps results to "
        "priority levels and planning focus areas via a rule-based Decision Support System. "
        "Input: district-year maternal-health indicator records. Output: risk class, priority level, "
        "planning focus areas, contributing indicators, and evidence for dashboards. "
        "The dashboard and Disha are presentation/interface layers: Disha retrieves the same evidence "
        "services and uses a local LLM only to phrase answers; if the LLM is unavailable, Disha still "
        "answers every MRCDSS question from the evidence."
    )
    return answer, True, [SOURCE_METHODOLOGY, SOURCE_PLANNING]


_CONCEPT_RULES = [
    ("supervised learning",
     "Supervised learning trains a model on labelled examples. In MRCDSS, four supervised models "
     "(Logistic Regression, Decision Tree, Random Forest, XGBoost) were trained on district-year records "
     "labelled with the K-Means-derived risk class to see which classifier best replicates the profiles."),
    ("unsupervised learning",
     "Unsupervised learning finds structure in data without predefined labels. MRCDSS uses K-Means "
     "clustering (K=3, random_state=42) on six standardised maternal-health indicators to derive the "
     "High / Medium / Low risk profiles."),
    ("difference between classification and clustering",
     "Classification assigns each case to a predefined label (supervised); clustering groups cases by "
     "similarity without predefined labels (unsupervised). MRCDSS uses K-Means clustering to derive the "
     "risk classes, then supervised classification models to replicate them."),
    ("difference between prediction and decision support",
     "Prediction forecasts a future outcome; decision support organises evidence and recommendations to "
     "help a human decision-maker. MRCDSS is a decision-support system — it characterises districts and "
     "suggests planning focus areas rather than predicting individual outcomes."),
    ("explainable ai", "Explainable AI (XAI) makes model decisions understandable to humans. MRCDSS uses "
     "SHAP values to show how much each maternal-health indicator contributed to a district's risk "
     "classification, with the caveat that SHAP indicates contribution, not causation."),
    ("machine learning", "Machine learning is a branch of AI that learns patterns from data. MRCDSS "
     "applies it through K-Means clustering and supervised classifiers on district-year maternal-health "
     "records."),
    ("imputation", "Imputation fills missing values before modelling. After cleaning, MRCDSS filled the "
     "remaining nulls with the column median, leaving no missing values in the final features."),
]


def _conceptual_answer(message):
    text = " ".join((message or "").lower().split())
    for key, body in _CONCEPT_RULES:
        if key in text:
            return (
                f"{body} Note: this is a general concept; its specific role in MRCDSS is documented above.",
                True, [SOURCE_METHODOLOGY],
            )
    return (
        "That is a general concept. When I am connected to the local LLM I can answer such general "
        "questions; right now I can only draw on the MRCDSS evidence.",
        False, [],
    )


# --------------------------------------------------------------------------- #
# Evidence assembly for the LLM
# --------------------------------------------------------------------------- #
def _district_evidence_text(ctx):
    if not ctx or not ctx.get("matched"):
        return ""
    lines = [f"District context: {ctx['district']}, {ctx['state']}"]
    if ctx.get("risk_class"):
        lines.append(f"Historical risk class: {ctx['risk_class']}; priority: {ctx['priority']}; "
                     f"latest assessment year {ctx.get('latest_historical_year')}")
    if ctx.get("top_contributing"):
        lines.append("Top contributing features: " + ", ".join(
            _label(f) for f in ctx["top_contributing"] if f))
    if ctx.get("planning_focus"):
        lines.append("Planning focus: " + "; ".join(f for f in ctx["planning_focus"] if f))
    if ctx.get("latest_recent"):
        rec = ctx["latest_recent"]
        lines.append(
            f"Recent HMIS latest ({rec['year']}): ANC {_pct(rec.get('ANC_First_Trimester_Pct'))}, "
            f"TT2/Booster {_pct(rec.get('TT2_Booster_Pct'))}, Severe Anemia "
            f"{_pct(rec.get('Severe_Anemia_Pct'))}, Obstetric Complications "
            f"{_pct(rec.get('Obstetric_Complications_Pct'))}. "
            f"Definitions: {rec.get('indicator_definition_status')}.")
        if rec.get("hmis_source_file"):
            lines.append(f"HMIS source file: {rec['hmis_source_file']}")
    return "\n".join(lines)


def _methodology_fact_digest():
    return " | ".join(f"{i['title']}: {i['value']}"
                      for i in methodology_service.get_methodology().get("items", []))


def _dataset_proof():
    try:
        ovo = unified_service.get_unified_overview()
        return (f"Unified dataset: {ovo.get('total_observations')} observations; {ovo.get('n_states')} states; "
                f"{ovo.get('n_state_district_units')} district-state units; counts by source "
                f"{json.dumps(ovo.get('counts_by_source'))}; historical years {ovo.get('historical_years')}; "
                f"recent years {ovo.get('recent_years')}.")
    except Exception:
        return ""


def _evidence_for(topic, message, ctx):
    district_ev = _district_evidence_text(ctx)
    blocks = []
    if district_ev:
        blocks.append(district_ev)
    if topic in (TOPIC_METHODOLOGY, TOPIC_ABOUT, TOPIC_SYSTEM, TOPIC_LIMITATIONS,
                 TOPIC_DATASET, TOPIC_PREPROCESSING, TOPIC_FEATURES):
        blocks.append("Methodology facts: " + _methodology_fact_digest())
    if topic == TOPIC_METHODOLOGY:
        models = _model_comparison_text()
        if models:
            blocks.append("Model comparison: " + models)
    if topic == TOPIC_SHAP:
        top = _global_shap_ranking()
        if top:
            blocks.append("Global SHAP feature ranking: " + ", ".join(_label(f) for f in top))
    if topic == TOPIC_PLANNING:
        planning = planning_service.get_planning_priorities()
        rules = "; ".join(f"{_label(r.get('feature', ''))} → {r.get('planning_focus', '')}"
                          for r in planning.get("planning_rules", [])[:6])
        if rules:
            blocks.append("DSS planning rules: " + rules)
    if topic in (TOPIC_DATASET, TOPIC_RECENT_HMIS):
        blocks.append("Unified dataset: " + _dataset_proof())
        try:
            cov = recent_hmis_service.get_recent_hmis_coverage()
            period_texts = cov.get("period_texts") or unified_service.get_unified_overview().get("period_texts")
        except Exception:
            period_texts = None
        if period_texts:
            blocks.append("Period text: " + " | ".join(str(v) for v in period_texts.values()))
    return "\n".join(b for b in blocks if b)


def _build_grounded_prompt(message, topic, ctx, draft, evidence, history):
    lines = [SYSTEM_PROMPT]
    if history:
        lines.append("Conversation history:\n" + "\n".join(
            f"- {h.get('role', '?')}: {h.get('text', '')}" for h in history[-6:]))
    lines.append(f"Grounded MRCDSS evidence:\n{evidence}")
    lines.append(f"User question: {message}")
    if draft:
        lines.append(f"Draft grounded answer to refine (keep facts, improve phrasing, be concise):\n{draft}")
    return "\n".join(lines) + "\n"


def _build_general_prompt(message, history, scope):
    lines = [
        "You are Disha, the MRCDSS Decision Assistant.\n"
        "Answer the exact question first, using simple, natural, conversational English.\n"
        "Prefer 1–4 short sentences.\n"
        "You may answer general questions using general knowledge, and generic ML/AI concept questions "
        "also using general knowledge with an MRCDSS tie-in when natural.\n"
        "Never claim that a general answer came from MRCDSS evidence.\n"
        "For any MRCDSS-specific factual question always answer only from the supplied MRCDSS evidence and "
        "never guess.\n"
        "Keep answers concise and professional.",
    ]
    if scope:
        lines.append(f"Current context: {json.dumps(scope)}")
    if history:
        lines.append("Conversation history:\n" + "\n".join(
            f"- {h.get('role', '?')}: {h.get('text', '')}" for h in history[-6:]))
    lines.append(f"User question: {message}")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# LLM provider abstraction (Groq Cloud primary; Ollama local fallback)
# --------------------------------------------------------------------------- #
def _llm_provider():
    return os.environ.get("MRCDSS_LLM_PROVIDER", "ollama").strip().lower()


def _ollama_base_url():
    return os.environ.get("MRCDSS_OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")


def _ollama_model():
    return os.environ.get("MRCDSS_OLLAMA_MODEL", "").strip()


def _groq_api_key():
    return os.environ.get("GROQ_API_KEY", "").strip()


def _groq_base_url():
    return os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")


def _groq_model():
    return os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b").strip()


def _groq_active() -> bool:
    """Groq is usable only when explicitly selected and an API key is present."""
    return _llm_provider() == "groq" and bool(_groq_api_key())


def _ollama_active() -> bool:
    if _llm_provider() != "ollama":
        return False
    if not _ollama_model():
        return False
    try:
        req = urllib.request.Request(f"{_ollama_base_url()}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=2.0) as resp:  # noqa: S310
            if resp.status != 200:
                return False
            body = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return False
    models = {m.get("name", "") for m in body.get("models", [])}
    if not models:
        return False
    target = _ollama_model()
    return any(m == target or m.split(":")[0] == target.split(":")[0] for m in models)


def _llm_active() -> bool:
    """Any configured LLM provider is available."""
    return _groq_active() or _ollama_active()


def _ollama_chat(prompt: str) -> str | None:
    payload = {
        "model": _ollama_model(),
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2},
    }
    req = urllib.request.Request(
        f"{_ollama_base_url()}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
            body = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    out = (body.get("response") or "").strip()
    return out or None


def _groq_chat(prompt: str) -> str | None:
    """Call Groq Cloud through its OpenAI-compatible chat/completions endpoint."""
    if not _groq_api_key():
        return None
    payload = {
        "model": _groq_model(),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "stream": False,
    }
    req = urllib.request.Request(
        f"{_groq_base_url()}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_groq_api_key()}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
            body = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    choices = body.get("choices") or []
    if not choices:
        return None
    message = choices[0].get("message") or {}
    out = (message.get("content") or "").strip()
    return out or None


def _llm_chat(prompt: str) -> str | None:
    """Route to the configured LLM provider. Groq takes precedence when selected."""
    if _llm_provider() == "groq":
        return _groq_chat(prompt)
    return _ollama_chat(prompt)


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def chat(message: str,
         state: str | None = None,
         district: str | None = None,
         page_context: str | None = None,
         history: list | None = None,
         scope: dict | None = None) -> dict:
    message = (message or "").strip()
    history = [h for h in (history or []) if isinstance(h, dict)]
    if not message:
        return {
            "answer": "Please ask a question about MRCDSS.",
            "grounded": False,
            "sources": [],
            "mode": "fallback",
            "intent": TOPIC_UNKNOWN,
            "context": None,
        }

    # Resolve the district scope (message > UI/map > previous turn).
    state, district = _resolve_entities(message, state, district, scope)
    ctx = build_district_context(state, district)

    # Natural-language understanding (LLM-driven when available).
    topic, kind, state, district = _understand(message, page_context, state, district, scope, history)
    ctx = build_district_context(state, district) if topic in GROUNDED_TOPICS else ctx

    # Resolve incomplete follow-ups using the previous-turn topic.
    if topic == TOPIC_UNKNOWN:
        follow = _follow_up_topic(" ".join((message or "").lower().split()), scope)
        if follow:
            topic, kind = follow, "grounded"

    if kind == "general":
        if _llm_active():
            try:
                answer = _llm_chat(_build_general_prompt(message, history, scope))
            except Exception:
                answer = None
            if answer:
                return {
                    "answer": answer,
                    "grounded": False,
                    "sources": [],
                    "mode": "groq" if _llm_provider() == "groq" else "general",
                    "intent": TOPIC_GENERAL,
                    "context": _context_payload(ctx, topic),
                }
        answer, grounded, sources = _dispatch(TOPIC_GENERAL, message, ctx)
        return {
            "answer": answer,
            "grounded": grounded,
            "sources": sources,
            "mode": "fallback",
            "intent": TOPIC_GENERAL,
            "context": _context_payload(ctx, topic),
        }

    if kind == "conceptual":
        glossary_answer, g_grounded, g_sources = _dispatch(TOPIC_CONCEPTUAL, message, ctx)
        if _llm_active():
            try:
                answer = _llm_chat(_build_general_prompt(message, history, scope))
            except Exception:
                answer = None
            if answer:
                return {
                    "answer": answer,
                    "grounded": False,
                    "sources": [],
                    "mode": "groq" if _llm_provider() == "groq" else "general",
                    "intent": TOPIC_CONCEPTUAL,
                    "context": _context_payload(ctx, topic),
                }
        return {
            "answer": glossary_answer,
            "grounded": g_grounded,
            "sources": g_sources,
            "mode": "fallback",
            "intent": TOPIC_CONCEPTUAL,
            "context": _context_payload(ctx, topic),
        }

    # Grounded path: retrieve evidence, then optionally refine with the LLM.
    answer, grounded, sources = _dispatch(topic, message, ctx)
    if not grounded:
        toast = _follow_up_topic(" ".join((message or "").lower().split()), scope)
        if toast and ctx is not None:
            topic = toast
            answer, grounded, sources = _dispatch(topic, message, ctx)

    mode = "fallback"
    if grounded and _llm_active():
        try:
            evidence = _evidence_for(topic, message, ctx)
            refined = _llm_chat(_build_grounded_prompt(message, topic, ctx, answer, evidence, history))
            if refined:
                answer = refined
                mode = "groq" if _llm_provider() == "groq" else "ollama"
        except Exception:
            pass

    return {
        "answer": answer,
        "grounded": grounded,
        "sources": sources,
        "mode": mode,
        "intent": topic,
        "context": _context_payload(ctx, topic),
    }


def _context_payload(ctx, topic):
    if ctx is None:
        return {"state": None, "district": None, "matched": False, "risk_class": None, "topic": topic}
    return {
        "state": ctx.get("state"),
        "district": ctx.get("district"),
        "matched": bool(ctx.get("matched")),
        "risk_class": ctx.get("risk_class"),
        "topic": topic,
    }