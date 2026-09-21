"""
conftest.py — shared pytest fixtures for Metallisense-Agent tests.

Run all tests from the Metallisense-Agent/ directory:
    pytest

Run a single test file:
    pytest tests/test_decision_policy.py

Run a single test function:
    pytest tests/test_decision_policy.py::TestDecisionPolicy::test_should_recommend_alloy_medium
"""
import sys
from pathlib import Path

_APP = Path(__file__).parent.parent / "app"

# `app/` on the path so `from schemas import ...`, `from config import ...`,
# `from policies.decision_policy import ...`, `from agents.anomaly_agent import ...` all resolve.
sys.path.insert(0, str(_APP))
