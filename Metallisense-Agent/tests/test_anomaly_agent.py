"""
Unit tests for AnomalyDetectionAgent (ML model class — no wrapper, no server).

These tests require no trained models for the pure-logic methods.
The predict() tests use a trained model fixture and are skipped automatically
if the model file is not present.

Run: pytest tests/test_anomaly_agent.py
"""
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock

from agents.anomaly_agent import AnomalyDetectionAgent


class TestAnomalyAgentScoreMethods:
    """Tests for deterministic helper methods — no trained model needed."""

    def setup_method(self):
        self.agent = AnomalyDetectionAgent()

    # ── _normalize_score ─────────────────────────────────────────────────────

    def test_normalize_score_at_min_gives_one(self):
        # score == score_min → normalized = 1.0 (maximally anomalous)
        result = self.agent._normalize_score(-0.5, score_min=-0.5, score_max=0.0)
        assert result == pytest.approx(1.0)

    def test_normalize_score_at_max_gives_zero(self):
        # score == score_max → normalized = 0.0 (normal)
        result = self.agent._normalize_score(0.0, score_min=-0.5, score_max=0.0)
        assert result == pytest.approx(0.0)

    def test_normalize_score_midpoint(self):
        result = self.agent._normalize_score(-0.25, score_min=-0.5, score_max=0.0)
        assert result == pytest.approx(0.5)

    def test_normalize_score_clipped_below_zero(self):
        # score above score_max → clipped to 0
        result = self.agent._normalize_score(0.1, score_min=-0.5, score_max=0.0)
        assert result == pytest.approx(0.0)

    def test_normalize_score_clipped_above_one(self):
        # score below score_min → clipped to 1
        result = self.agent._normalize_score(-1.0, score_min=-0.5, score_max=0.0)
        assert result == pytest.approx(1.0)

    # ── _get_severity ────────────────────────────────────────────────────────

    @pytest.mark.parametrize("score,expected", [
        (0.00, "NORMAL"),
        (0.04, "NORMAL"),
        (0.05, "LOW"),
        (0.19, "LOW"),
        (0.20, "MEDIUM"),
        (0.49, "MEDIUM"),
        (0.50, "HIGH"),
        (0.99, "HIGH"),
        (1.00, "HIGH"),
    ])
    def test_get_severity_thresholds(self, score, expected):
        assert self.agent._get_severity(score) == expected


class TestAnomalyAgentPredict:
    """Tests that require a trained model — skipped if model file absent."""

    MODEL_PATH = Path(__file__).parent.parent / "app" / "models" / "anomaly_model.pkl"

    @pytest.fixture(autouse=True)
    def skip_if_no_model(self):
        if not self.MODEL_PATH.exists():
            pytest.skip("anomaly_model.pkl not found — run setup.py first")

    @pytest.fixture(scope="class")
    def trained_agent(self):
        agent = AnomalyDetectionAgent()
        agent.load(str(self.MODEL_PATH))
        return agent

    # Standard SG-IRON composition used in README examples
    NORMAL_COMP = {"Fe": 86.0, "C": 3.5, "Si": 2.3, "Mn": 0.65, "P": 0.045, "S": 0.02}
    DEVIATED_COMP = {"Fe": 78.0, "C": 5.5, "Si": 4.5, "Mn": 1.8, "P": 0.20, "S": 0.30}

    def test_predict_returns_required_keys(self, trained_agent):
        result = trained_agent.predict(self.NORMAL_COMP)
        assert "anomaly_score" in result
        assert "severity" in result
        assert "message" in result

    def test_predict_score_in_range(self, trained_agent):
        result = trained_agent.predict(self.NORMAL_COMP)
        assert 0.0 <= result["anomaly_score"] <= 1.0

    def test_predict_severity_is_valid(self, trained_agent):
        valid = {"NORMAL", "LOW", "MEDIUM", "HIGH"}
        result = trained_agent.predict(self.NORMAL_COMP)
        assert result["severity"] in valid

    def test_predict_deterministic(self, trained_agent):
        """Same input must produce identical output every call."""
        results = [trained_agent.predict(self.NORMAL_COMP) for _ in range(3)]
        scores = [r["anomaly_score"] for r in results]
        assert len(set(scores)) == 1, f"Non-deterministic scores: {scores}"

    def test_predict_deviated_higher_than_normal(self, trained_agent):
        """Deviated composition should score higher than clearly normal one."""
        normal_score = trained_agent.predict(self.NORMAL_COMP)["anomaly_score"]
        deviated_score = trained_agent.predict(self.DEVIATED_COMP)["anomaly_score"]
        assert deviated_score > normal_score, (
            f"Expected deviated ({deviated_score:.3f}) > normal ({normal_score:.3f})"
        )
