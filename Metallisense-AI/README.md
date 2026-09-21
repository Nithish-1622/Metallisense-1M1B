# Metallisense-AI — Base ML Service

> ⚠️ **Status: Superseded by `Metallisense-Agent`**
>
> This directory is the *original* ML service (port 8000). The canonical production service is
> **`Metallisense-Agent`** (port 8001), which extends this codebase with:
> - Agent wrapper architecture (`AgentManager`, `DecisionPolicy`)
> - Explainable AI Copilot (Groq LLM + voice)
> - Persistent audit logging
> - Analysis history persistence
>
> **You should run `Metallisense-Agent` in production, not this service.**
>
> This directory is retained as a reference implementation and for
> comparing model training configurations. The two services intentionally
> use different configs:
>
> | Config | Metallisense-AI (here) | Metallisense-Agent |
> |---|---|---|
> | Port | 8000 | 8001 |
> | `ANOMALY_CONTAMINATION` | 0.35 | 0.05 (tighter) |
> | `SYNTHETIC_DATASET_SIZE` | 200 000 | 30 000 |
> | Agent wrappers | ✗ | ✓ |
> | Copilot | ✗ | ✓ |
> | Audit log | ✗ | ✓ |
>
> If you are setting up the project for the first time, go to
> [`../Metallisense-Agent/`](../Metallisense-Agent/) and follow the README there.

## Running (legacy / reference only)

```powershell
cd Metallisense-AI
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python setup.py        # trains models
python app/main.py     # starts on port 8000
```
