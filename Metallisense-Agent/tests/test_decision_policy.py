"""
Unit tests for DecisionPolicy.

These tests require no trained models and no running server.
Run: pytest tests/test_decision_policy.py
"""
import pytest
from policies.decision_policy import DecisionPolicy, SeverityLevel


class TestSeverityLevelEnum:
    def test_all_expected_values_present(self):
        names = {m.value for m in SeverityLevel}
        assert "NORMAL" in names
        assert "LOW" in names
        assert "MEDIUM" in names
        assert "HIGH" in names
        assert "ERROR" in names


class TestDecisionPolicy:
    def setup_method(self):
        self.policy = DecisionPolicy()

    # ── should_check_anomaly ────────────────────────────────────────────────

    def test_should_check_anomaly_always_true(self):
        """Anomaly detection must always run regardless of composition."""
        assert self.policy.should_check_anomaly({}) is True
        assert self.policy.should_check_anomaly({"Fe": 90, "C": 3}) is True

    # ── should_recommend_alloy ──────────────────────────────────────────────

    def test_should_recommend_alloy_none_result(self):
        assert self.policy.should_recommend_alloy(None, "SG-IRON") is False

    def test_should_recommend_alloy_low_severity(self):
        assert self.policy.should_recommend_alloy({"severity": "LOW"}, "SG-IRON") is False

    def test_should_recommend_alloy_normal_severity(self):
        assert self.policy.should_recommend_alloy({"severity": "NORMAL"}, "SG-IRON") is False

    def test_should_recommend_alloy_medium_severity(self):
        assert self.policy.should_recommend_alloy({"severity": "MEDIUM"}, "SG-IRON") is True

    def test_should_recommend_alloy_high_severity(self):
        assert self.policy.should_recommend_alloy({"severity": "HIGH"}, "SG-IRON") is True

    def test_should_recommend_alloy_error_severity(self):
        assert self.policy.should_recommend_alloy({"severity": "ERROR"}, "SG-IRON") is False

    # ── requires_human_approval ─────────────────────────────────────────────

    def test_requires_human_approval_always_true(self):
        assert self.policy.requires_human_approval(None, None) is True
        assert self.policy.requires_human_approval({"severity": "LOW"}, {}) is True

    # ── is_action_allowed ───────────────────────────────────────────────────

    def test_is_action_allowed_always_false(self):
        assert self.policy.is_action_allowed("adjust_furnace") is False
        assert self.policy.is_action_allowed("approve_batch") is False

    # ── validate_agent_response ─────────────────────────────────────────────

    def test_validate_agent_response_valid(self):
        response = {
            "agent": "AnomalyDetectionAgent",
            "confidence": 0.87,
            "explanation": "Significant deviation detected.",
        }
        assert self.policy.validate_agent_response("AnomalyDetectionAgent", response) is True

    def test_validate_agent_response_missing_field(self):
        response = {"agent": "AnomalyDetectionAgent", "confidence": 0.87}
        assert self.policy.validate_agent_response("AnomalyDetectionAgent", response) is False

    def test_validate_agent_response_wrong_agent_name(self):
        response = {
            "agent": "WrongAgent",
            "confidence": 0.87,
            "explanation": "...",
        }
        assert self.policy.validate_agent_response("AnomalyDetectionAgent", response) is False

    def test_validate_agent_response_confidence_out_of_range(self):
        response = {
            "agent": "AnomalyDetectionAgent",
            "confidence": 1.5,
            "explanation": "...",
        }
        assert self.policy.validate_agent_response("AnomalyDetectionAgent", response) is False

    def test_validate_agent_response_confidence_zero(self):
        """confidence=0.0 is valid (e.g. error fallback responses)."""
        response = {
            "agent": "AnomalyDetectionAgent",
            "confidence": 0.0,
            "explanation": "Agent error: model not loaded",
        }
        assert self.policy.validate_agent_response("AnomalyDetectionAgent", response) is True

    # ── get_safety_note ─────────────────────────────────────────────────────

    def test_get_safety_note_not_empty(self):
        note = self.policy.get_safety_note()
        assert isinstance(note, str) and len(note) > 0

    # ── log_decision writes to audit logger without raising ─────────────────

    def test_log_decision_does_not_raise(self):
        self.policy.log_decision("ANOMALY_CHECK", "Severity: HIGH, Score: 0.87")
