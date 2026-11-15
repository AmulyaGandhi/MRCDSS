# MRCDSS — Changelog

## Completed Work Summary

This changelog documents all changes made to bring MRCDSS to a stable, polished, professionally designed, and fully working state ready for academic demonstration.

---

## Phase 1: Research Integrity Corrections

### DSS Priority Terminology
- Replaced "Persistent" priority with "Repeated" priority throughout backend (`planning_service.py`, `districts_service.py`) and frontend (`Assistant.tsx` suggested question).
- Repeated-priority rule (≥2 historical district-year records at the same level) is explicitly described as a historical pattern, not current/latest status.

### Planning-Focus Descriptions
- Labelled "Model-attributed planning focus" with the note that it indicates where the model attributed influence, **not** a verified district needs assessment.

### SHAP Direction
- Removed hardcoded "Increases risk" / "Decreases risk" direction claims.
- `DistrictDetails.tsx` reports "Contribution direction unavailable" and "Attribution does not establish causality."
- `ContributingFactors.tsx` uses neutral "Pushes toward / away from High Risk" wording.

### Clinical Thresholds Removed
- Indicator interpretations state "Observed value; no clinical threshold applied."
- Hardcoded 15/25/50/30-style thresholds removed from rendered UI.

### Historical vs Current Labels
- Overview presents "Latest historical … not current or live status."
- District detail shows assessment year clearly.
- Disha distinguishes historical risk from recent HMIS evidence.
- Recent HMIS never reassigns risk class.

### "Validated" Overclaims Removed
- Removed "validated MRCDSS" risk classes/features/system from backend services and frontend pages.
- "Validated" retained only in disclaimers stating validation does **not** exist, and in preserved historical output reports (not modified).

### Unified State/District Normalization
- `GET /api/unified/overview` reports 36 normalized states and 812 normalized units (39 raw state strings and 850 raw entries reconciled, 38 duplicate normalized entries).
- Raw aliases preserved for provenance.

### API Error Handling
- `backend/main.py`: Added global `FileNotFoundError` → HTTP 404 handler (instead of 500).

### Hardcoded Values Removed
- `risk_analysis_service.py`: Reads silhouette/DBI/CHI and sensitivity sizes from artifacts (no hardcoded fallback 961 / 0.231).

### Recent HMIS Presentation
- Missingness (ANC 158, TT2 158, Severe Anemia 168, Obstetric 1,087), invalid-value flags (1,955 total), partial 2024–25 (17 states), excluded 2025–26 displayed accurately across `/recent-hmis`, Overview, and Risk Analysis.
- Values retained, never clipped.

---

## Phase 2: UI Redesign

### Design System (`frontend/src/index.css`)
- Complete rewrite as a premium design system: navy (`#0e2a47`) & deep teal (`#0f7b78`) foundation, white/cool-grey surfaces, restrained risk data colours, clear typographic hierarchy, consistent spacing scale, subtle borders/shadows, defined corner radii.
- Consolidated all component styling (cards, KPIs, tables, badges, callouts, buttons, empty/loading/error states) into one coherent system.

### Shell & Navigation
- New `Sidebar.tsx`: collapsible fixed left navigation with active states.
- Slimmed `AppHeader.tsx`: top bar within content area.
- `AppLayout.tsx`: shell → sidebar → app-body → content structure.
- Mobile: hamburger toggle + backdrop overlay; sidebar hidden by default on desktop (visible), collapsible on mobile.

### Pages Redesigned
- **Overview**: Executive KPI grid, prominent district risk map, district attention table, risk/priority distribution bars, recent-HMIS evidence strip.
- **Risk Analysis**: Evaluation-disclosure callout, cluster profiles, model comparison table, SHAP table, sensitivity, methodological caveats.
- **Planning**: Priority overview, latest-vs-repeated distinction, decision rules, contributing indicators, filterable historical table.
- **District Details**: Risk/priority profile, historical timeline, indicators (no clinical thresholds), planning focus, contributing factors, recent HMIS.
- **Recent HMIS**: Coverage, indicators, missingness, data-quality flags, distributions, district coverage.
- **Methodology & About**: Structured research sections, pipeline diagram, caveats, disclaimer.

### Disha Assistant UI
- Floating launcher at bottom-right with "Ask Disha" label and chat icon.
- Chat panel above all content: header, message bubbles, source chips, grounded/not-grounded footnotes, input + send.
- Welcoming greeting + suggested questions.
- Responsive on desktop and mobile.

---

## Phase 3: Groq Cloud Integration for Disha

### Backend Provider Abstraction (`backend/services/assistant_service.py`)
- `_groq_active()`: Groq usable only when `MRCDSS_LLM_PROVIDER=groq` and `GROQ_API_KEY` present.
- `_groq_chat()`: Calls Groq OpenAI-compatible `chat/completions` endpoint via `urllib` (no new packages), `Authorization: Bearer <key>`.
- `_llm_active()`, `_llm_chat()`: Dispatch to Groq (when selected) else Ollama.
- All network/parse failures return `None` → deterministic fallback.
- Expanded `SYSTEM_PROMPT` with grounding rules (no invented stats, SHAP ≠ causation, K-Means derived not clinical, Severe Anemia comparability, historical vs recent HMIS, no patient advice).
- `chat()` reports `mode: "groq"` / `"ollama"` / `"fallback"`.

### API Contract
- `backend/api/routes/assistant.py`: `mode` Literal includes `"groq"`.
- `frontend/src/api/assistant.ts`: `mode` type includes `'groq'`.

### Environment
- `.env.example`: Added `GROQ_API_KEY=`, `GROQ_MODEL=openai/gpt-oss-120b`, `GROQ_BASE_URL=https://api.groq.com/openai/v1`, `MRCDSS_LLM_PROVIDER=off`.
- `.gitignore`: Added `.env` and standard ignores.

---

## Phase 4: Disha Response Quality Improvements

### Intent Classification
- Added intent detection for: repeated priority rule, latest assessment year, clinical validation, district list queries by risk class.

### Retrieval Helpers
- `_districts_by_latest_risk_class(risk_class, limit)`: District names from latest historical observations with total count.
- `_latest_assessment_year()`: Latest historical year.

### `_aggregate_answer()` Intent-Aware
- District list questions → first 10 names, total count, offer remaining.
- Count questions → count, denominator, reporting period.
- Repeated priority / latest year → direct answers.
- No data dumping on every query.

### Conciseness
- `SYSTEM_PROMPT` and `_build_general_prompt()`: Answer first, 1–4 sentences, simple English, no unrelated statistics.
- Deterministic answers (ABOUT, model methodology) shortened.

---

## Phase 5: Layout & Map Fixes

### Layout (`frontend/src/index.css`, `AppLayout.tsx`)
- Moved `AppHeader` inside `.app-main` so header and content share the same left margin (sidebar width).
- Removed `.header-inner` `max-width` centering — now left-aligned, spans content width.
- Reduced `.content` left padding from 32px to 16px.
- Content expands naturally across available viewport; no excessive gap between sidebar and content.

### Map (`frontend/src/components/DistrictRiskMap.tsx`)
- Switched basemap from CartoDB (`basemaps.cartocdn.com`, requires API key) to OpenStreetMap (`tile.openstreetmap.org`, no key required).

---

## Phase 6: Documentation

### New Files
- `README.md`: Rewritten to reflect actual implementation (backend path, real endpoints, six-feature model, limitations, integrity rules).
- `docs/judge_demo_guide.md`: Startup instructions + 8–12 minute demo sequence.
- `docs/judge_questions_and_answers.md`: 36 technically accurate Q&A including difficult methodology questions.
- `docs/research_paper_draft.md`: Paper draft using only actual project evidence (no fabricated references).
- `reports/final_project_completion_report.md`: Changes, files modified, test/build/API results, limitations, readiness verdict.

---

## Verification Results

### Backend Tests
- `pytest tests/ -q`: **281 passed, 0 failed** (read-only integrity suite).

### Frontend
- `tsc -b`: Clean.
- `npm run build`: **Succeeded** (CSS ~37 kB, JS ~828 kB).
- No frontend test suite configured.

### API Endpoints (live verification)
- `/api/health`, `/api/overview`, `/api/districts/*`, `/api/districts/latest`, `/api/risk-analysis`, `/api/planning-priorities`, `/api/methodology`, `/api/recent-hmis/*`, `/api/unified/*`, `/api/assistant/chat` — all return HTTP 200 with consistent values.

### Disha (10 representative questions)
- All return concise, grounded, directly relevant answers; no unrelated statistics; no "validated" overclaims.

### Preservation
- Raw datasets (`dataset1.csv`, `dataset2.csv`, `data/recent_hmis/raw/*`) unchanged.
- Saved models (`models/*.pkl`) and `outputs/` artifacts unchanged.
- `src/` pipeline code unchanged.
- Six-feature primary model preserved; K=3, random_state=42 unchanged.

---

## Files Modified / Created

### Modified (backend)
- `backend/main.py`
- `backend/api/routes/assistant.py`
- `backend/services/assistant_service.py`
- `backend/services/districts_service.py`
- `backend/services/methodology_service.py`
- `backend/services/planning_service.py`
- `backend/services/recent_hmis_service.py`
- `backend/services/risk_analysis_service.py`
- `backend/services/unified_service.py`

### Modified (frontend)
- `frontend/src/App.tsx`
- `frontend/src/components/AppHeader.tsx`
- `frontend/src/components/AppLayout.tsx`
- `frontend/src/components/Assistant.tsx`
- `frontend/src/components/ContributingFactors.tsx`
- `frontend/src/components/DistrictRiskMap.tsx`
- `frontend/src/components/HealthIndicators.tsx`
- `frontend/src/components/KpiCard.tsx`
- `frontend/src/components/SectionBlock.tsx`
- `frontend/src/index.css`
- `frontend/src/api/assistant.ts`
- `frontend/src/api/districtDetail.ts`
- `frontend/src/api/planning.ts`
- `frontend/src/api/recentHmis.ts`
- `frontend/src/api/riskAnalysis.ts`
- `frontend/src/api/unified.ts`
- `frontend/src/pages/About.tsx`
- `frontend/src/pages/DistrictDetails.tsx`
- `frontend/src/pages/DistrictExplorer.tsx`
- `frontend/src/pages/Methodology.tsx`
- `frontend/src/pages/Overview.tsx`
- `frontend/src/pages/Planning.tsx`
- `frontend/src/pages/RecentHmis.tsx`
- `frontend/src/pages/RiskAnalysis.tsx`

### Created (frontend)
- `frontend/src/components/Sidebar.tsx`

### Created (docs/reports)
- `README.md`
- `docs/judge_demo_guide.md`
- `docs/judge_questions_and_answers.md`
- `docs/research_paper_draft.md`
- `reports/final_project_completion_report.md`

### Modified (tests)
- `tests/assistant/test_assistant_api.py`
- `tests/recent_hmis/test_dataset3.py`

### Configuration
- `.env.example`
- `.gitignore`

---

## Preserved (Not Modified)
- `dataset1.csv`, `dataset2.csv` (raw inputs)
- `data/recent_hmis/raw/*` (source HMIS files)
- `models/*.pkl` (saved trained models)
- `outputs/` (clustering, classification, SHAP, DSS artifacts)
- `src/` pipeline code (preprocessing, clustering, classification, SHAP, DSS)
