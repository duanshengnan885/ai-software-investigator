"""Unit tests for Evidence data model and ledger."""

from pathlib import Path
import tempfile
import pytest

from investigator.engine.protocol import ClaimStatus, Reliability
from investigator.evidence.model import Evidence
from investigator.evidence.ledger import EvidenceLedger


def test_evidence_model_serialization():
    ev = Evidence(
        evidence_id="E-001",
        source="experiment:EXP-01",
        type="runtime_observation",
        claim_status=ClaimStatus.OBSERVED,
        description="Memory usage grew from 100MB to 500MB",
        reliability=Reliability.HIGH,
        related_hypotheses=["H1"],
    )
    d = ev.to_ledger_dict()
    assert d["evidence_id"] == "E-001"
    assert d["claim_status"] == "Observed"
    assert d["reliability"] == "HIGH"
    assert d["related_hypotheses"] == ["H1"]


def test_evidence_ledger_lifecycle():
    with tempfile.TemporaryDirectory() as tmp_dir:
        ledger_path = Path(tmp_dir) / "evidence.jsonl"
        ledger = EvidenceLedger(ledger_path)

        assert ledger.count() == 0

        # Record evidence
        e1 = ledger.record(
            source="test_source",
            type="exit_code",
            description="Process exited with code 1",
            claim_status=ClaimStatus.OBSERVED,
            related_hypotheses=["H1", "H2"],
        )
        assert e1.evidence_id == "E-001"
        assert ledger.count() == 1

        # Record second evidence
        e2 = ledger.record(
            source="test_source_2",
            type="log_trace",
            description="Null pointer exception in parser.cpp",
            claim_status=ClaimStatus.OBSERVED,
            related_hypotheses=["H2"],
        )
        assert e2.evidence_id == "E-002"
        assert ledger.count() == 2

        # Filter by hypothesis
        h1_evidence = ledger.by_hypothesis("H1")
        assert len(h1_evidence) == 1
        assert h1_evidence[0].evidence_id == "E-001"

        h2_evidence = ledger.by_hypothesis("H2")
        assert len(h2_evidence) == 2

        # Trace chain
        chain = ledger.trace_chain("H1")
        assert len(chain) == 1
        assert chain[0]["evidence_id"] == "E-001"

        # Persistence reload test
        reloaded_ledger = EvidenceLedger(ledger_path)
        assert reloaded_ledger.count() == 2
        assert reloaded_ledger.get("E-001").description == "Process exited with code 1"
        assert reloaded_ledger.next_id() == "E-003"


def test_evidence_ledger_validation():
    with tempfile.TemporaryDirectory() as tmp_dir:
        ledger = EvidenceLedger(Path(tmp_dir) / "evidence.jsonl")
        with pytest.raises(ValueError):
            ledger.record(source="", type="test", description="Missing source")
        with pytest.raises(ValueError):
            ledger.record(source="test", type="test", description="")
