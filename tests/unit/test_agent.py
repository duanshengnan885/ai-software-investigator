"""Unit tests for Autonomous Investigation Agent and tools."""

from pathlib import Path
import tempfile
import pytest

from investigator.agent.core import AutonomousInvestigator
from investigator.agent.tools import ForensicToolRegistry, ToolCall
from investigator.agent.llm import HeuristicForensicDriver
from investigator.engine.investigator import InvestigationEngine
from investigator.engine.protocol import CaseCategory, InvestigationVerdict


def test_tool_registry_execution():
    with tempfile.TemporaryDirectory() as tmp_dir:
        engine = InvestigationEngine(project_dir=Path(tmp_dir), use_sandbox=False)
        registry = ForensicToolRegistry(engine)

        # Tool 1: Intake
        r1 = registry.execute_tool("intake", {
            "title": "Division Crash",
            "problem_statement": "Crash on zero divisor",
            "category": "bug",
        })
        assert r1["status"] == "ok"
        assert engine.state.case is not None

        # Tool 2: Discover environment
        r2 = registry.execute_tool("discover_environment", {})
        assert r2["status"] == "ok"
        assert "os" in r2["environment"]

        # Tool 3: Formulate hypothesis
        r3 = registry.execute_tool("formulate_hypothesis", {
            "title": "Zero divisor",
            "description": "Missing guard check on divisor",
            "category": "logic",
        })
        assert r3["status"] == "ok"
        assert r3["hypothesis_id"] == "H1"

        # Tool 4: Conclude
        r4 = registry.execute_tool("conclude", {
            "verdict": "SUCCESS",
            "remaining_uncertainties": ["None"],
        })
        assert r4["status"] == "ok"


def test_autonomous_investigator_loop():
    with tempfile.TemporaryDirectory() as tmp_dir:
        work_dir = Path(tmp_dir)
        (work_dir / "target.py").write_text("import sys; sys.exit(0)\n", encoding="utf-8")

        agent = AutonomousInvestigator(
            project_dir=work_dir,
            provider=HeuristicForensicDriver(),
            use_sandbox=False,
        )

        report = agent.investigate(
            problem_statement="Program fails intermittently",
            title="Automated Test Case",
            category=CaseCategory.BUG,
            repro_command="python target.py",
            max_steps=8,
            verbose=False,
        )

        assert "# Forensic Software Investigation Report" in report
        assert agent.engine.state.evidence_ledger.count() >= 2
        assert len(agent.engine.state.hypothesis_manager.all()) >= 1
