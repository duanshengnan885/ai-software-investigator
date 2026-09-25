"""Unit tests for Confidence Calculator."""

from pathlib import Path
import tempfile
import pytest

from investigator.engine.confidence import ConfidenceCalculator
from investigator.engine.protocol import ConfidenceLevel, HypothesisStatus, Reliability
from investigator.evidence.ledger import EvidenceLedger
from investigator.hypotheses.manager import HypothesisManager


def test_confidence_calculator_baseline_and_progression():
    with tempfile.TemporaryDirectory() as tmp_dir:
        ledger = EvidenceLedger(Path(tmp_dir) / "evidence.jsonl")
        hypo_mgr = HypothesisManager(Path(tmp_dir) / "hypotheses.json")

        # Initial state: no repro, no evidence -> LOW confidence
        c1 = ConfidenceCalculator.evaluate(
            evidence_ledger=ledger,
            hypothesis_manager=hypo_mgr,
        )
        assert c1.level == ConfidenceLevel.LOW
        assert c1.score <= 0.20

        # Step 1: Create hypotheses
        h1 = hypo_mgr.create("Memory Leak", "Cache not freed")
        h2 = hypo_mgr.create("Race Condition", "Missing mutex")

        # Step 2: Reproduce baseline
        repro_rate = 1.0

        # Step 3: Record supporting evidence and eliminate H1
        e1 = ledger.record("exp:1", "probe", "Lock contention detected", reliability=Reliability.HIGH, related_hypotheses=["H2"])
        e2 = ledger.record("exp:2", "probe", "Repeated runs reproduce deadlock", reliability=Reliability.HIGH, related_hypotheses=["H2"])
        
        hypo_mgr.link_evidence("H2", e1.evidence_id, supports=True)
        hypo_mgr.link_evidence("H2", e2.evidence_id, supports=True)
        hypo_mgr.link_experiment("H2", "EXP-001")
        hypo_mgr.link_experiment("H2", "EXP-002")

        # Falsify H1
        hypo_mgr.link_evidence("H1", "E-003", supports=False)
        hypo_mgr.update_status("H1", HypothesisStatus.REJECTED, rationale="Memory usage stayed under 20MB", evidence_id="E-003")

        # Confirm H2
        hypo_mgr.update_status("H2", HypothesisStatus.CONFIRMED, rationale="Empirically confirmed", evidence_id="E-001")

        # Step 4: Verification 100 runs, 0 failures, regression passed
        c_final = ConfidenceCalculator.evaluate(
            evidence_ledger=ledger,
            hypothesis_manager=hypo_mgr,
            reproduction_rate=repro_rate,
            reproduction_runs=1,
            verification_runs=100,
            verification_failures=0,
            regression_passed=True,
        )

        assert c_final.level == ConfidenceLevel.HIGH
        assert c_final.score >= 0.85
        # Verify no fake confidence: itemized basis and statistical interval present
        assert c_final.statistical_interval is not None
        assert c_final.statistical_interval.upper_bound <= 0.05
        assert any("0/100 failures" in b or "0 failures" in b for b in c_final.basis)
