"""Unit tests for Hypothesis data model and HypothesisManager."""

from pathlib import Path
import tempfile
import pytest

from investigator.engine.protocol import HypothesisStatus
from investigator.hypotheses.model import Hypothesis
from investigator.hypotheses.manager import HypothesisManager


def test_hypothesis_model_and_transitions():
    h = Hypothesis(
        hypothesis_id="H1",
        title="Cache Leak",
        description="Cache does not evict entries",
        category="memory",
    )
    assert h.status == HypothesisStatus.UNTESTED

    h.record_transition(
        new_status=HypothesisStatus.SUPPORTED,
        rationale="Memory growth matched prediction",
        evidence_id="E-001"
    )
    assert h.status == HypothesisStatus.SUPPORTED
    assert len(h.history) == 1
    assert h.history[0].from_status == HypothesisStatus.UNTESTED
    assert h.history[0].to_status == HypothesisStatus.SUPPORTED
    assert h.history[0].evidence_id == "E-001"


def test_hypothesis_manager_guardrails():
    with tempfile.TemporaryDirectory() as tmp_dir:
        hypo_file = Path(tmp_dir) / "hypotheses.json"
        mgr = HypothesisManager(hypo_file)

        h1 = mgr.create(
            title="Deadlock in Worker",
            description="Two threads lock in reverse order",
            category="concurrency",
        )
        assert h1.hypothesis_id == "H1"
        assert len(mgr.all()) == 1

        # GUARD 1: Cannot CONFIRM without supporting evidence
        with pytest.raises(ValueError, match="Cannot CONFIRM H1 without verified supporting evidence"):
            mgr.update_status(
                hypothesis_id="H1",
                new_status=HypothesisStatus.CONFIRMED,
                rationale="Guessing it is confirmed without evidence",
            )

        # GUARD 2: Cannot REJECT without evidence or experiment
        with pytest.raises(ValueError, match="Cannot REJECT H1 without empirical evidence"):
            mgr.update_status(
                hypothesis_id="H1",
                new_status=HypothesisStatus.REJECTED,
                rationale="Guessing it is rejected",
            )

        # Now link evidence and test valid confirmation
        mgr.link_evidence("H1", "E-001", supports=True)
        confirmed = mgr.update_status(
            hypothesis_id="H1",
            new_status=HypothesisStatus.CONFIRMED,
            rationale="Deadlock trace reproduced in sandbox",
            evidence_id="E-001",
        )
        assert confirmed.status == HypothesisStatus.CONFIRMED
        assert mgr.confirmed() is not None
        assert mgr.confirmed().hypothesis_id == "H1"


def test_hypothesis_manager_contradiction_guard():
    with tempfile.TemporaryDirectory() as tmp_dir:
        hypo_file = Path(tmp_dir) / "hypotheses.json"
        mgr = HypothesisManager(hypo_file)

        mgr.create("Race Condition", "Missing lock", category="concurrency")
        mgr.link_evidence("H1", "E-001", supports=True)
        mgr.link_evidence("H1", "E-002", supports=False) # Contradiction!

        # Cannot CONFIRM while contradictory evidence remains
        with pytest.raises(ValueError, match="Cannot CONFIRM H1 while contradictory evidence"):
            mgr.update_status(
                hypothesis_id="H1",
                new_status=HypothesisStatus.CONFIRMED,
                rationale="Attempting to confirm despite contradiction",
            )
