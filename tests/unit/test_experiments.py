"""Unit tests for Experiment runner, model, and planner."""

from pathlib import Path
import tempfile
import pytest

from investigator.engine.protocol import ExperimentOutcome, HypothesisStatus
from investigator.experiments.model import ExperimentRecord
from investigator.experiments.runner import ExperimentRunner
from investigator.experiments.planner import ExperimentPlanner, ExperimentCandidate
from investigator.hypotheses.model import Hypothesis


def test_experiment_runner_execution():
    with tempfile.TemporaryDirectory() as tmp_dir:
        artifacts_dir = Path(tmp_dir) / "artifacts"
        ledger_path = Path(tmp_dir) / "experiments.jsonl"
        runner = ExperimentRunner(artifacts_dir=artifacts_dir, ledger_path=ledger_path)

        res = runner.execute_raw("python -c \"print('ASI_TEST_OUTPUT')\"")
        assert res.exit_code == 0
        assert "ASI_TEST_OUTPUT" in res.stdout
        assert res.duration_ms > 0

        # Test recording experiment
        exp = runner.record_experiment(
            title="Smoke Test",
            objective="Verify python runtime can execute simple commands",
            expected_prediction="Output should contain ASI_TEST_OUTPUT",
            command="python -c \"print('ASI_TEST_OUTPUT')\"",
            actual_result=res.stdout.strip(),
            outcome=ExperimentOutcome.SUPPORTED,
            hypothesis_id="H1",
            exit_code=res.exit_code,
            raw_stdout=res.stdout,
            raw_stderr=res.stderr,
        )
        assert exp.experiment_id == "EXP-001"
        assert len(exp.artifacts) == 2 # stdout and stderr saved
        assert (artifacts_dir / "EXP-001_stdout.log").exists()


def test_experiment_statistical_runner():
    with tempfile.TemporaryDirectory() as tmp_dir:
        runner = ExperimentRunner(artifacts_dir=Path(tmp_dir) / "artifacts")
        # Run 5 iterations of a successful command
        stats = runner.run_statistical("python -c \"import sys; sys.exit(0)\"", runs=5)
        assert stats["total_runs"] == 5
        assert stats["successes"] == 5
        assert stats["failures"] == 0
        assert stats["failure_rate"] == 0.0

        # Run 5 iterations of a failing command
        stats_fail = runner.run_statistical("python -c \"import sys; sys.exit(1)\"", runs=5)
        assert stats_fail["failures"] == 5
        assert stats_fail["failure_rate"] == 1.0


def test_experiment_planner_information_gain():
    h1 = Hypothesis(hypothesis_id="H1", title="H1", description="desc", status=HypothesisStatus.PLAUSIBLE)
    h2 = Hypothesis(hypothesis_id="H2", title="H2", description="desc", status=HypothesisStatus.PLAUSIBLE)
    h3 = Hypothesis(hypothesis_id="H3", title="H3", description="desc", status=HypothesisStatus.PLAUSIBLE)

    planner = ExperimentPlanner(active_hypotheses=[h1, h2, h3])

    # Candidate A: tests only 1 hypothesis, slow (10s), HIGH risk
    cand_a = ExperimentCandidate(
        candidate_id="EXP_A",
        title="Heavy Stress Test",
        target_hypothesis_ids=["H1"],
        command="stress_test",
        expected_duration_sec=10.0,
        risk_level="HIGH",
        differentiating_power=0.5,
    )

    # Candidate B: tests 2 hypotheses, fast (1s), LOW risk, high power
    cand_b = ExperimentCandidate(
        candidate_id="EXP_B",
        title="Unit Differential Probe",
        target_hypothesis_ids=["H1", "H2"],
        command="probe_test",
        expected_duration_sec=1.0,
        risk_level="LOW",
        differentiating_power=0.9,
    )

    ranked = planner.prioritize([cand_a, cand_b])
    # Candidate B must be prioritized over Candidate A based on Information Gain First
    assert ranked[0].candidate_id == "EXP_B"
    assert planner.select_next([cand_a, cand_b]).candidate_id == "EXP_B"
