"""
Unit tests for Pydantic schemas — validates request/response contracts.

These tests require no trained models and no running server.
Run: pytest tests/test_schemas.py
"""
import pytest
from pydantic import ValidationError

from schemas import Composition, AgentComposition, AlloyAgentOutput


class TestCompositionSumValidation:
    """Verify the 85–100% sum rule on both composition schemas."""

    VALID = {"Fe": 81.2, "C": 4.4, "Si": 3.1, "Mn": 0.4, "P": 0.04, "S": 0.02}

    def test_valid_composition_accepted(self):
        c = Composition(**self.VALID)
        assert c.Fe == pytest.approx(81.2)

    def test_sum_too_low_rejected(self):
        bad = {**self.VALID, "Fe": 10.0}  # total ≈ 18%
        with pytest.raises(ValidationError):
            Composition(**bad)

    def test_sum_too_high_rejected(self):
        bad = {**self.VALID, "Fe": 99.0}  # total > 100%
        with pytest.raises(ValidationError):
            Composition(**bad)

    def test_sum_exactly_at_lower_bound_accepted(self):
        # Construct a composition that sums to exactly 85
        c = Composition(Fe=79.9, C=3.0, Si=1.0, Mn=0.5, P=0.5, S=0.1)
        total = c.Fe + c.C + c.Si + c.Mn + c.P + c.S
        assert 85.0 <= total <= 100.0

    def test_agent_composition_sum_too_low_rejected(self):
        bad = {"Fe": 10.0, "C": 1.0, "Si": 0.5, "Mn": 0.1}  # total ≈ 11.6%
        with pytest.raises(ValidationError):
            AgentComposition(**bad)

    def test_agent_composition_valid(self):
        comp = AgentComposition(**{k: v for k, v in self.VALID.items()})
        assert comp.Fe == pytest.approx(81.2)

    def test_agent_composition_p_s_default_to_zero(self):
        """P and S are optional — default 0.0 — but total must still be ≥ 85."""
        # Without P and S (both 0), Fe+C+Si+Mn must be ≥ 85
        comp = AgentComposition(Fe=92.0, C=2.0, Si=1.5, Mn=0.5)
        assert comp.P == 0.0
        assert comp.S == 0.0


class TestAlloyAgentOutputDeviations:
    """Verify the optional deviations field on AlloyAgentOutput."""

    BASE = {
        "agent": "AlloyCorrectionAgent",
        "recommended_additions": {"Si": 0.22, "Mn": 0.15},
        "confidence": 0.91,
        "explanation": "Adjusting toward grade midpoint.",
    }

    def test_output_without_deviations_accepted(self):
        out = AlloyAgentOutput(**self.BASE)
        assert out.deviations is None

    def test_output_with_deviations_accepted(self):
        out = AlloyAgentOutput(**self.BASE, deviations={"Fe": 1.2, "C": -0.3, "Si": 0.8})
        assert out.deviations["Fe"] == pytest.approx(1.2)
        assert out.deviations["C"] == pytest.approx(-0.3)

    def test_output_confidence_out_of_range_rejected(self):
        with pytest.raises(ValidationError):
            AlloyAgentOutput(**{**self.BASE, "confidence": 1.5})
