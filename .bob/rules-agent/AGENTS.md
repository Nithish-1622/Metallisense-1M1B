# Agent Mode — Coding Rules (Non-Obvious)

## Mandatory: Read before modifying any Python module

1. **`sys.path.append(str(Path(__file__).parent.parent))`** must be present at the top of every module that imports from sibling packages. Without it, the module fails when run directly (training/test scripts all run as `__main__`).

2. **Agent error handling returns a dict, never raises.** Both wrappers catch all exceptions and return a structured `{"agent": ..., "confidence": 0.0, "explanation": "Agent error: ..."}` dict. Do not refactor error paths to raise — the AgentManager calls `.get("anomaly_agent")` on whatever comes back.

3. **Singleton factory pattern is used everywhere.** `get_anomaly_agent()`, `get_alloy_agent()`, `get_agent_manager()`, `get_copilot()`, `get_voice_service()` all follow the module-level `_instance = None` pattern. `main.py` initializes them at startup via `initialize_models()`. New services must follow this pattern.

4. **The alloy model stores `grade_encodings` as part of the serialized `.pkl`.** When you add a grade to `GradeSpecificationGenerator`, the encoding dict in the loaded model will not contain it — the agent returns `{"recommended_additions": {}, "confidence": 0.0}` for unknown grades. Retrain after adding grades.

5. **Anomaly model stores `score_min`/`score_max` for determinism.** The normalization in `_normalize_score()` uses training-time stats, not per-batch stats. If you retrain with different data, `score_min`/`score_max` will change and predictions will shift. This is expected behavior.

6. **`DecisionPolicy` is entirely static methods.** Do not add instance state to it. The `AgentManager` constructs it once but calls static methods.

7. **Node backend `aiService.js` sends to port 8000 by default for BOTH service URLs.** The Agent service (with Copilot) runs on **8001**. Always set `AI_SERVICE_AGENT_URL=http://localhost:8001` in `config.env` when running both Python services.

8. **Frontend API calls go to `/api/v2/*` only.** V1 routes exist on the backend for legacy but frontend uses v2 exclusively. New endpoints must be added to v2 routes.

9. **`config.env` (not `.env`) is the Node backend dotenv file.** `dotenv.config({ path: './config.env' })` in `server.js`. Standard `.env` is silently ignored.

10. **Max alloy addition is hard-capped at 5% per element** in `config.py` (`MAX_ADDITION_PERCENTAGE = 5.0`) and enforced in `alloy_agent.py` `predict()`. Do not bypass this constraint.
