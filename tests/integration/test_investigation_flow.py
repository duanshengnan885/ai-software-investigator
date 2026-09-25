"""Integration test for full end-to-end investigation workflow."""

from pathlib import Path
import tempfile
import pytest

from investigator.engine.investigator import InvestigationEngine
from investigator.engine.protocol import CaseCategory, ExperimentOutcome, InvestigationVerdict


BUGGY_SCRIPT = """import sys

def divide(a, b):
    # Bug: crashes when b == 0
    return a / b

if __name__ == '__main__':
    b = int(sys.argv[1])
    try:
        res = divide(10, b)
        print(f"RES: {res}")
        sys.exit(0)
    except Exception as e:
        print(f"CRASH: {e}", file=sys.stderr)
        sys.exit(2)
"""

FIXED_SCRIPT = """import sys

def divide(a, b):
    if b == 0:
        return 0.0
    return a / b

if __name__ == '__main__':
    b = int(sys.argv[1])
    try:
        res = divide(10, b)
        print(f"RES: {res}")
        sys.exit(0)
    except Exception as e:
        print(f"CRASH: {e}", file=sys.stderr)
        sys.exit(2)
"""


def test_full_investigation_pipeline():
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_dir = Path(tmp_dir)
        (project_dir / "calc.py").write_text(BUGGY_SCRIPT, encoding="utf-8")

        # 1. Initialize
        engine = InvestigationEngine(project_dir=project_dir, use_sandbox=False)

        # 2. Intake
        case = engine.intake(
            case_id="CASE-TEST-001",
            title="Division by Zero Crash",
            problem_statement="Calculation crashes when input is 0",
            category=CaseCategory.BUG,
        )
        assert case.case_id == "CASE-TEST-001"

        # 3. Environment Discovery
        env = engine.discover_environment()
        assert "os" in env

        # 4. Reproduction
        repro = engine.reproduce_problem("python calc.py 0", runs=1)
        assert repro["failure_rate"] == 1.0

        # 5. Hypotheses
        h1 = engine.formulate_hypothesis(
            title="Unchecked Zero Denominator",
            description="divide() does not guard against zero divisor",
            category="logic"
        )
        h2 = engine.formulate_hypothesis(
            title="Type Coercion Failure",
            description="Input is parsed as string rather than int",
            category="types"
        )

        # 6. Experiments
        exp1 = engine.execute_experiment(
            title="Non-Zero Divisor Test",
            objective="Test behavior with divisor=2",
            expected_prediction="Exit 0",
            command="python calc.py 2",
            hypothesis_id="H1",
            expected_pass_code=0,
        )
        assert exp1.outcome == ExperimentOutcome.SUPPORTED

        exp2 = engine.execute_experiment(
            title="Type check test",
            objective="Test behavior with integer 5",
            expected_prediction="Exit 0",
            command="python calc.py 5",
            hypothesis_id="H2",
            expected_pass_code=0,
        )

        # 7. Elimination & Root Cause
        engine.reject_hypothesis("H2", rationale="Integer parsing succeeds normally")
        engine.identify_root_cause(
            hypothesis_id="H1",
            what="ZeroDivisionError when b == 0",
            why="Missing guard check on divisor in divide()",
            where="calc.py: line 4",
            how_confirmed="Reproduction and controlled tests confirm crash occurs exclusively when b == 0",
        )

        # 8. Minimal Fix
        diff = engine.apply_minimal_fix(
            file_modifications={"calc.py": FIXED_SCRIPT},
            rationales={"calc.py": "Add guard if b == 0 return 0.0"}
        )
        assert diff.is_minimal_fix is True

        # 9. Verification
        verif = engine.verify_fix(
            reproduction_command="python calc.py 0",
            verification_runs=5,
            regression_commands=["python calc.py 2", "python calc.py 5"]
        )
        assert verif["passed"] is True
        assert verif["failures"] == 0

        # 10. Conclude
        report_md = engine.conclude(verdict=InvestigationVerdict.SUCCESS)
        assert "# Forensic Software Investigation Report" in report_md
        assert "CASE-TEST-001" in report_md
        assert (project_dir / ".investigation" / "report.md").exists()
