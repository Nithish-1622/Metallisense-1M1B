# Ask Mode — Documentation Context

## Counterintuitive layout facts

- **`Metallisense-Agent/`** is the *newer*, more complete Python service (port 8001). It contains the Agent Manager, Copilot (Groq LLM + voice), and the policy layer. **`Metallisense-AI/`** is the *older* base ML service (port 8000) without the agent wrapper architecture or Copilot. The two are separate deployments with separate `venv`s.

- **PASS/FAIL logic is not in Python.** All grade compliance / pass-fail decisions live in the Node.js backend. The Python services are advisory only — they detect anomalies and suggest additions, but never issue a verdict.

- **`app/data/grade_specs.py`** is not just a data file — it is a class (`GradeSpecificationGenerator`) that generates specs programmatically. The grades are hardcoded in `_generate_specifications()`, not loaded from `grades.json` (that file exists in `Metallisense-AI/app/data/` and is a separate artifact).

- **OPC UA is Node.js only.** `MetalliSense-Node-Backend/services/opcuaService.js` and `opcuaClient.js` handle all industrial protocol communication. The Python layer never touches OPC UA.

- **Frontend auth interceptor always attaches a Firebase token** (`src/services/api.js`). There is no username/password auth flow to the backend — only Firebase JWT.

- **Training scripts are meant to be run directly** (`python app/training/train_anomaly.py`) from within the sub-project root with the venv activated, not via any test runner or task manager.

- **`Metallisense-Agent` README says port 8000 in some places and 8001 in others** — the actual configured port in `app/config.py` is **8001**. The older `Metallisense-AI` service is port 8000.
