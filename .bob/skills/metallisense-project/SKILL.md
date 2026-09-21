---
name: metallisense-project
description: Use when working on the Metallisense-1M1B repository — provides structured knowledge about the architecture, agents, policies, data pipeline, API contracts, conventions, and implementation constraints so you can make changes without rediscovering the codebase.
---

# Metallisense-1M1B Project Skill

Activate this skill whenever you are asked to read, understand, or modify code in this repository.

---

## Project Identity

**MetalliSense** is an industrial AI system for metal foundry quality control. It analyses spectrometer readings (elemental composition of molten metal), detects anomalies, and recommends alloy additions to bring composition back into grade specification. All agent decisions are **advisory only** — human approval is always required.

---

## Repository Structure

Four sub-projects, each independently deployable:

```
Metallisense-1M1B/
├── Metallisense-Agent/     # Python 3.11 / FastAPI  — Agent + Copilot layer  (port 8001)
├── Metallisense-AI/        # Python 3.11 / FastAPI  — Base ML layer           (port 8000)
├── MetalliSense-Node-Backend/  # Node.js / Express  — API gateway             (port 3000)
└── Metallisense-frontend/  # React 19 / Vite        — SPA (Firebase Auth)
```

`Metallisense-Agent` is the **newer, more complete** Python service. `Metallisense-AI` is the older base ML service without the agent wrapper or Copilot. They are intentionally separate with different configs.

---

## Agent Architecture (Metallisense-Agent)

```
Incoming Data → Node.js Rule Engine → AgentManager → Agents
```

### Components

| File | Class | Role |
|---|---|---|
| `app/agents/agent_manager.py` | `AgentManager` | Orchestrator — sole coordinator of agents |
| `app/agents/anomaly_agent_wrapper.py` | `AnomalyDetectionAgentWrapper` | Production wrapper for anomaly model |
| `app/agents/alloy_agent_wrapper.py` | `AlloyCorrectionAgentWrapper` | Production wrapper for alloy model |
| `app/agents/anomaly_agent.py` | `AnomalyDetectionAgent` | ML model (Isolation Forest) |
| `app/agents/alloy_agent.py` | `AlloyCorrectionAgent` | ML model (MultiOutput GradientBoosting) |
| `app/policies/decision_policy.py` | `DecisionPolicy` | All static methods — controls invocation rules |
| `app/copilot/groq_explainer.py` | `ExplainableAICopilot` | Groq LLM explanations + chat history |
| `app/copilot/voice_service.py` | `VoiceService` | Groq Whisper STT + gTTS TTS |

### Orchestration Flow (`AgentManager.analyze`)

1. `DecisionPolicy.should_check_anomaly()` — **always returns True**
2. Run `AnomalyDetectionAgentWrapper.analyze(composition)` → returns `{agent, anomaly_score, severity, confidence, explanation}`
3. `DecisionPolicy.should_recommend_alloy(anomaly_result, grade)` → True only if severity is **MEDIUM or HIGH**
4. If True: run `AlloyCorrectionAgentWrapper.recommend(grade, composition)` → returns `{agent, recommended_additions, confidence, explanation}`
5. If False: alloy agent response is `{recommended_additions: {}, confidence: 0.0, explanation: "Not invoked..."}`
6. `DecisionPolicy.requires_human_approval()` — **always returns True**
7. Return aggregated `{anomaly_agent, alloy_agent, final_note, timestamp}`

### Safety Invariants (do not break)

- Agents never call each other — only `AgentManager` coordinates them
- `DecisionPolicy.is_action_allowed()` always returns `False`
- Every agent response includes `{"agent": <name>, "confidence": float, "explanation": str}` — required by `validate_agent_response()`
- Error handling in wrappers catches all exceptions and returns a structured dict (never raises)

---

## Decision & Policy Layer

`DecisionPolicy` (all static methods, no state):
- `should_check_anomaly()` → always `True`
- `should_recommend_alloy(anomaly_result, grade)` → `True` if `severity in ["MEDIUM", "HIGH"]`
- `requires_human_approval()` → always `True`
- `is_action_allowed(action)` → always `False`
- `validate_agent_response(agent_name, response)` → checks `["agent", "confidence", "explanation"]` and confidence ∈ [0,1]
- `log_decision(decision, reason)` → prints to stdout (no logging framework)

---

## Data & ML

### Elements tracked (fixed, hardcoded)
`ELEMENTS = ["Fe", "C", "Si", "Mn", "P", "S"]` — in `app/config.py`. Must match dataset columns.

### Grade Specifications
`GradeSpecificationGenerator` in `app/data/grade_specs.py` — grades are **hardcoded** in `_generate_specifications()`, not loaded from file. Supported: `SG-IRON`, `GREY-IRON`, `LOW-CARBON-STEEL`, `MEDIUM-CARBON-STEEL`, `HIGH-CARBON-STEEL`. Adding a grade requires editing this class AND retraining the alloy model.

### Anomaly Model (Isolation Forest)
- Trained **only on tightly filtered normal samples** (within 1.5σ per element per `train_anomaly.py`)
- Stores `score_min`/`score_max` from training in the `.pkl` for deterministic normalization
- Severity thresholds in `_get_severity()`: NORMAL < 0.05, LOW < 0.20, MEDIUM < 0.50, HIGH ≥ 0.50

### Alloy Model (MultiOutputRegressor + GradientBoostingRegressor)
- Target = positive delta from current composition to grade midpoint
- `grade_encodings` dict is serialized inside the `.pkl` — new grades not in it return `{}`
- Max addition hard-capped at `MAX_ADDITION_PERCENTAGE = 5.0`%

### Model files
Saved as `.pkl` via `joblib` at:
- `app/models/anomaly_model.pkl`
- `app/models/alloy_model.pkl`

These are **not committed** — must be generated by running `setup.py` or training scripts.

### Dataset
`app/data/dataset.csv` — synthetic, generated by `app/data/synthetic_gen.py`. Required columns: `Fe, C, Si, Mn, P, S, grade, is_deviated`.

---

## API Layer (Metallisense-Agent)

Entry point: `app/main.py`. All schemas in `app/schemas.py`.

### Production endpoint
```
POST /agents/analyze
Body: { "composition": {Fe, C, Si, Mn, P, S}, "grade": str }
Response: AgentAnalysisResponse { anomaly_agent, alloy_agent, final_note, timestamp }
```

### Other endpoints
```
GET  /health
POST /anomaly/predict         (legacy)
POST /alloy/recommend         (legacy)
GET  /grades
GET  /grades/{grade}
POST /copilot/explain         (requires GROQ_API_KEY)
POST /copilot/chat            (requires GROQ_API_KEY)
DELETE /copilot/chat/history  (requires GROQ_API_KEY)
POST /copilot/voice/transcribe  (requires GROQ_API_KEY)
POST /copilot/voice/synthesize  (requires GROQ_API_KEY)
GET  /copilot/voice/languages
```

### Schema contract
- `AgentComposition` has `Fe, C, Si, Mn` required; `P, S` optional (default 0.0)
- `AnomalyAgentOutput` requires `agent, anomaly_score, severity, confidence, explanation`
- `AlloyAgentOutput` requires `agent, recommended_additions, confidence, explanation`

---

## Node.js Backend

Entry: `server.js` → `app.js`. Config from `config.env` (not `.env`).

### API routes
- `/api/v1/*` — legacy (users, metal-grades, spectrometer)
- `/api/v2/*` — current: `auth`, `grades`, `training-data`, `synthetic`, `ai`

### AI integration
`services/aiService.js` — singleton. Env vars:
- `AI_SERVICE_INDIVIDUAL_URL` (default `http://localhost:8000`) — for `/anomaly/predict`, `/alloy/recommend`
- `AI_SERVICE_AGENT_URL` (default `http://localhost:8000`) — for `/agents/analyze` — **should be 8001** when running Agent service

### Services
- `opcuaService.js` / `opcuaClient.js` — OPC UA server. Initialized at startup; client connection is frontend-triggered.
- `geminiService.js` — Google Gemini integration
- `userMetadataService.js` — Firebase user metadata

---

## Frontend

- All HTTP calls go through `src/services/api.js` — baseURL `http://localhost:3000/api/v2`
- Every request automatically carries a Firebase ID token (`Authorization: Bearer <token>`)
- Auth state managed via `src/context/AuthContext.jsx`
- OPC UA state managed via `src/context/OPCContext.jsx`
- Grade state managed via `src/context/GradeContext.jsx`
- No test framework is present in the frontend

---

## Configuration

### Metallisense-Agent `app/config.py`
| Key | Value |
|---|---|
| API_PORT | 8001 |
| ANOMALY_CONTAMINATION | 0.05 |
| SYNTHETIC_DATASET_SIZE | 30 000 |
| MAX_ADDITION_PERCENTAGE | 5.0 |
| GROQ_MODEL | `llama-3.3-70b-versatile` |

### Metallisense-AI `app/config.py`
| Key | Value |
|---|---|
| API_PORT | 8000 |
| ANOMALY_CONTAMINATION | 0.35 |
| SYNTHETIC_DATASET_SIZE | 200 000 |

### Environment variables required
- `GROQ_API_KEY` — Copilot and voice endpoints (Metallisense-Agent only)
- `DATABASE` / `DATABASE_PASSWORD` — MongoDB URI (Node backend, `config.env`)
- `VITE_API_BASE_URL` — overrides `http://localhost:3000/api/v2` in frontend

---

## Development Conventions

### Python
- Type hints on all function signatures (`Dict`, `Optional` from `typing`, not built-in generics)
- Docstrings on all public methods with Args/Returns
- Every file that imports from siblings: `sys.path.append(str(Path(__file__).parent.parent))` at top
- Singleton pattern: module-level `_instance = None` + `get_X()` factory function
- Classes use `VERSION = "1.0.0"` class attribute
- `print()` for logging (no `logging` framework)
- `if __name__ == "__main__":` block in every module for standalone testing

### Node.js
- CommonJS (`require`/`module.exports`)
- No TypeScript
- ESLint + Prettier configured
- Error objects via `utils/AppError.js`; global handler in `controllers/errorController.js`

### Frontend
- `.jsx` extensions; React 19; Tailwind CSS utility classes
- No TypeScript; no test framework

---

## Important Constraints — Do Not Break

1. **Never add autonomous actions to agents.** `DecisionPolicy.is_action_allowed()` always returns `False`.
2. **Never let agents call each other.** Only `AgentManager` invokes agents.
3. **Never move PASS/FAIL logic to Python.** It belongs in the Node.js rule engine.
4. **Never import training code from inference modules.**
5. **Always preserve the agent response contract** (`agent`, `confidence`, `explanation` keys).
6. **Never change `ELEMENTS` order** without retraining both models — the feature vector order is positional.
7. **Always retrain models after changing grade specs or ELEMENTS.**
8. **Models must exist before starting the API.** Startup raises `FileNotFoundError` otherwise.

---

## Common Workflows

### Adding a new agent
1. Create `app/agents/<name>_agent.py` (ML model class with `train()`, `predict()`, `save()`, `load()`)
2. Create `app/agents/<name>_agent_wrapper.py` (wrapper class, `get_<name>_agent()` factory)
3. Register in `AgentManager.__init__()` and add invocation logic
4. Add invocation condition to `DecisionPolicy`
5. Add request/response schemas to `app/schemas.py`
6. Add endpoint to `app/main.py`

### Retraining models
```powershell
cd Metallisense-Agent
venv\Scripts\activate
python retrain_models.py      # retrains both on existing dataset.csv
# OR
python setup.py               # full setup including dataset verification
```

### Running the full stack locally
```powershell
# Terminal 1 — Base ML service
cd Metallisense-AI; venv\Scripts\activate; python app/main.py

# Terminal 2 — Agent + Copilot service
cd Metallisense-Agent; venv\Scripts\activate
$env:GROQ_API_KEY="<key>"; python app/main.py

# Terminal 3 — Node backend
cd MetalliSense-Node-Backend; npm start

# Terminal 4 — Frontend
cd Metallisense-frontend; npm run dev
```

### Integration testing (Agent service must be running)
```powershell
cd Metallisense-Agent
venv\Scripts\activate
python test_agent_system.py   # tests /health, /agents/analyze, legacy endpoints
```

### Running individual module tests (no server needed)
```powershell
python app/data/grade_specs.py
python app/policies/decision_policy.py
python app/agents/anomaly_agent_wrapper.py   # requires trained model
python app/inference/anomaly_predict.py      # requires trained model
```

---

## Agent Operating Rules

When working on this repository:

1. **Always inspect existing implementation before proposing changes.**
2. **Never rewrite working modules unnecessarily.**
3. **Never create duplicate functionality when an existing abstraction can be reused.**
4. **Preserve the agent safety and policy mechanisms** — they are safety-critical.
5. **Do not bypass DecisionPolicy** — all invocation logic must go through it.
6. **Do not silently change agent output contracts** — downstream consumers depend on exact key names.
7. **When modifying an agent, inspect**: its wrapper, `AgentManager`, `DecisionPolicy`, `schemas.py`, and calling endpoints.
8. **When modifying inference**, inspect model loading, `prepare_features()`, scaling, and callers.
9. **When modifying training**, verify inference compatibility — both use the same `.pkl` format.
10. **Prefer small, traceable changes.**
11. **Clearly explain what changed and why.**
12. **If requirements conflict with existing architecture, surface the conflict before implementing.**

---

## UNKNOWN / REQUIRES CONFIRMATION

- Whether `Metallisense-AI` is still actively used or has been superseded by `Metallisense-Agent`
- Production deployment configuration (Docker, cloud provider, reverse proxy)
- Whether `config.env` template/example exists (not found in repository)
- Firebase project configuration (`.env` / firebase config files are gitignored)
