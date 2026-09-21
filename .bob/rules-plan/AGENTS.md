# Plan Mode — Architecture Constraints

## Hard architectural constraints

1. **Agents must remain stateless and advisory.** `DecisionPolicy.is_action_allowed()` always returns `False` by design. No agent may be given tools to modify furnace state or make autonomous decisions — this is a safety invariant, not a missing feature.

2. **AgentManager is the only orchestrator.** Agents must never call each other directly. Only `AgentManager.analyze()` coordinates the two agents. Any new agent must be registered in `AgentManager.__init__()` and invoked only through `AgentManager`.

3. **Policy logic belongs in `decision_policy.py` only.** Conditional invocation rules (e.g., "only call alloy agent on MEDIUM/HIGH") must live in `DecisionPolicy`, not scattered in endpoint handlers or agent code.

4. **Two separate Python services exist by design.** `Metallisense-AI` (port 8000) is a stable base ML layer. `Metallisense-Agent` (port 8001) is the agent+copilot layer that builds on top of it. Do not merge them into one service without explicit user request.

5. **Inference and training are separate layers.** `app/inference/` wraps trained `.pkl` models for serving. `app/training/` produces those models. Never import training code from inference or vice versa.

6. **The Node backend is the system's rule engine and API gateway.** Frontend talks exclusively to Node (`/api/v2/*`). Node calls Python AI services over HTTP. Adding a Python endpoint does nothing for the UI unless a corresponding Node route and `aiService.js` method are also added.

7. **Grade specs define the alloy correction target.** `GradeSpecificationGenerator.get_composition_midpoint()` returns the training target for corrections. Changing grade ranges requires retraining the alloy model.

8. **`Metallisense-AI` and `Metallisense-Agent` have divergent configs.** `Metallisense-AI/app/config.py`: port 8000, contamination 0.35, dataset size 200 000. `Metallisense-Agent/app/config.py`: port 8001, contamination 0.05, dataset size 30 000. These are intentional differences — Agent uses tighter detection thresholds.
