"""Investigation Engine for AI Software Investigator.

The central orchestration engine implementing the full forensic lifecycle:
Hypothesis -> Experiment -> Evidence -> Minimal Fix -> Statistical Verification -> Report.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import platform
import sys

from investigator.engine.confidence import ConfidenceAssessment, ConfidenceCalculator
from investigator.engine.protocol import (
    CaseCategory,
    ClaimStatus,
    ConfidenceLevel,
    ExperimentOutcome,
    HypothesisStatus,
    InvestigationStage,
    InvestigationVerdict,
    Reliability,
)
from investigator.engine.state import CaseMetadata, InvestigationState
from investigator.evidence.model import Evidence
from investigator.experiments.model import ExperimentRecord
from investigator.experiments.runner import ExperimentRunner
from investigator.hypotheses.model import Hypothesis
from investigator.reporting.diff_analyzer import DiffAnalysisResult, DiffAnalyzer, FileDiffSummary
from investigator.reporting.generator import ReportGenerator
from investigator.sandbox.directory import DirectorySandbox
from investigator.sandbox.safety import SafetyGuard


class InvestigationEngine:
    """Core autonomous forensic investigation engine."""

    def __init__(
        self,
        project_dir: Path,
        use_sandbox: bool = True,
        approval_callback: Optional[Callable[[str, str], bool]] = None,
    ):
        self.project_dir = Path(project_dir).resolve()
        self.use_sandbox = use_sandbox
        self.state = InvestigationState(self.project_dir)
        self.safety_guard = SafetyGuard(require_approval_callback=approval_callback)
        self.runner = ExperimentRunner(
            artifacts_dir=self.state.artifacts_dir,
            ledger_path=self.state.experiments_file
        )
        self.sandbox: Optional[DirectorySandbox] = None
        self.active_work_dir = self.project_dir

        if self.use_sandbox:
            self.sandbox = DirectorySandbox(source_dir=self.project_dir)
            self.active_work_dir = self.sandbox.enter()

        self._env_info: Dict[str, Any] = {}
        self._root_cause_details: Dict[str, str] = {}
        self._diff_analysis: Optional[DiffAnalysisResult] = None
        self._file_snapshots: Dict[str, str] = {}

    def intake(
        self,
        case_id: str,
        title: str,
        problem_statement: str,
        category: CaseCategory = CaseCategory.BUG,
    ) -> CaseMetadata:
        """Step 1: Project Intake."""
        case = self.state.initialize_case(
            case_id=case_id,
            title=title,
            problem_statement=problem_statement,
            category=category,
        )
        return case

    def discover_environment(self) -> Dict[str, Any]:
        """Step 2: Environment Discovery."""
        self.state.set_stage(InvestigationStage.ENVIRONMENT_DISCOVERY)

        env = {
            "os": platform.platform(),
            "os_name": platform.system(),
            "architecture": platform.machine(),
            "python_version": sys.version.split()[0],
            "working_directory": str(self.active_work_dir),
            "is_sandbox": self.use_sandbox,
        }
        self._env_info = env

        # Record environment as first evidence
        ev = self.state.evidence_ledger.record(
            source="environment_probe",
            type="runtime_environment",
            claim_status=ClaimStatus.OBSERVED,
            description=f"Environment discovered: {env['os_name']} {env['architecture']}, Python {env['python_version']}",
            reliability=Reliability.HIGH,
            metadata=env,
        )

        self.state.append_finding(
            "Environment Discovery",
            f"Host platform: `{env['os']}` | Python: `{env['python_version']}`"
        )
        return env

    def reproduce_problem(
        self,
        repro_command: str,
        runs: int = 1,
        expected_exit_code: int = 0,
        timeout_sec: float = 30.0,
    ) -> Dict[str, Any]:
        """Step 3 & 4: Evidence Collection and Problem Reproduction."""
        self.safety_guard.authorize_or_raise(repro_command)
        self.state.set_stage(InvestigationStage.REPRODUCTION)

        if runs == 1:
            res = self.runner.execute_raw(
                command=repro_command,
                cwd=self.active_work_dir,
                timeout_sec=timeout_sec,
            )
            is_failure = (res.exit_code != expected_exit_code) or res.timed_out
            repro_rate = 1.0 if is_failure else 0.0
            repro_summary = {
                "total_runs": 1,
                "failures": 1 if is_failure else 0,
                "failure_rate": repro_rate,
                "exit_code": res.exit_code,
                "timed_out": res.timed_out,
                "duration_ms": res.duration_ms,
                "sample_stderr": res.stderr[:300] if res.stderr else "",
            }
        else:
            repro_summary = self.runner.run_statistical(
                command=repro_command,
                runs=runs,
                cwd=self.active_work_dir,
                timeout_sec=timeout_sec,
                expected_exit_code=expected_exit_code,
            )
            repro_rate = repro_summary["failure_rate"]

        if self.state.case:
            self.state.case.reproduction_command = repro_command
            self.state.case.reproduction_rate = repro_rate
            self.state.save_case()

        # Record reproduction evidence
        status_label = "successfully reproduced" if repro_rate > 0 else "failed to trigger failure"
        ev = self.state.evidence_ledger.record(
            source="reproduction_harness",
            type="runtime_reproduction",
            claim_status=ClaimStatus.OBSERVED,
            description=f"Reproduction attempt {status_label}: {repro_rate*100:.1f}% failure rate across {runs} trial(s). (Command: `{repro_command}`)",
            reliability=Reliability.HIGH,
            metadata=repro_summary,
        )

        self.state.append_finding(
            "Problem Reproduction",
            f"Reproduction run on `{repro_command}` yielded **{repro_rate*100:.1f}%** failure rate ({repro_summary.get('failures', 0)}/{runs} failures)."
        )

        return repro_summary

    def formulate_hypothesis(
        self,
        title: str,
        description: str,
        category: str = "logic",
        hypothesis_id: Optional[str] = None,
    ) -> Hypothesis:
        """Step 5: Hypothesis Generation."""
        self.state.set_stage(InvestigationStage.HYPOTHESIS_GENERATION)
        hypo = self.state.hypothesis_manager.create(
            title=title,
            description=description,
            category=category,
            hypothesis_id=hypothesis_id,
            initial_status=HypothesisStatus.PLAUSIBLE,
        )
        self.state.append_finding(
            "Hypothesis Formulated",
            f"**{hypo.hypothesis_id}:** {hypo.title}\n*{hypo.description}*"
        )
        return hypo

    def execute_experiment(
        self,
        title: str,
        objective: str,
        expected_prediction: str,
        command: str,
        hypothesis_id: Optional[str] = None,
        timeout_sec: float = 30.0,
        statistical_runs: int = 1,
        expected_pass_code: int = 0,
        expect_failure: bool = False,
        outcome: Optional[ExperimentOutcome] = None,
    ) -> ExperimentRecord:
        """Step 6 & 7: Sandbox Experiment Execution and Evidence Analysis."""
        self.safety_guard.authorize_or_raise(command)
        self.state.set_stage(InvestigationStage.EXPERIMENT_EXECUTION)

        if statistical_runs > 1:
            stats = self.runner.run_statistical(
                command=command,
                runs=statistical_runs,
                cwd=self.active_work_dir,
                timeout_sec=timeout_sec,
                expected_exit_code=expected_pass_code,
            )
            actual_text = f"Executed {statistical_runs} runs: failure_rate={stats['failure_rate']*100:.1f}%, avg_duration={stats['avg_duration_ms']}ms."
            exit_code = 0 if stats['failures'] == 0 else 1
            metrics = stats
            raw_stdout = f"Statistical Summary:\n{stats}"
            raw_stderr = "\n".join(stats.get("sample_errors", []))
            duration = stats.get("avg_duration_ms", 0.0)
        else:
            res = self.runner.execute_raw(
                command=command,
                cwd=self.active_work_dir,
                timeout_sec=timeout_sec,
            )
            actual_text = (
                f"Exit code: {res.exit_code}, Duration: {res.duration_ms}ms. "
                f"Stderr snippet: {res.stderr.strip()[:150] if res.stderr else 'none'}"
            )
            exit_code = res.exit_code
            metrics = {"peak_memory_mb": res.peak_memory_mb, "timed_out": res.timed_out}
            raw_stdout = res.stdout
            raw_stderr = res.stderr
            duration = res.duration_ms

        # Determine outcome: does observation match prediction?
        if outcome is None:
            if expect_failure:
                # If we predicted failure, seeing failure means the hypothesis is SUPPORTED
                outcome = ExperimentOutcome.SUPPORTED if exit_code != expected_pass_code else ExperimentOutcome.WEAKENED
            else:
                outcome = ExperimentOutcome.SUPPORTED if exit_code == expected_pass_code else ExperimentOutcome.WEAKENED

        exp = self.runner.record_experiment(
            title=title,
            objective=objective,
            expected_prediction=expected_prediction,
            command=command,
            actual_result=actual_text,
            outcome=outcome,
            hypothesis_id=hypothesis_id,
            cwd=str(self.active_work_dir),
            exit_code=exit_code,
            duration_ms=duration,
            metrics=metrics,
            raw_stdout=raw_stdout,
            raw_stderr=raw_stderr,
        )

        # Record Evidence linking to experiment
        ev = self.state.evidence_ledger.record(
            source=f"experiment:{exp.experiment_id}",
            type="experiment_observation",
            claim_status=ClaimStatus.OBSERVED,
            description=f"Experiment '{title}' executed: {actual_text}",
            raw_reference=exp.artifacts[0] if exp.artifacts else None,
            reliability=Reliability.HIGH,
            related_hypotheses=[hypothesis_id] if hypothesis_id else [],
            metadata={"outcome": outcome.value, "command": command},
        )

        if hypothesis_id:
            self.state.hypothesis_manager.link_experiment(hypothesis_id, exp.experiment_id)
            self.state.hypothesis_manager.link_evidence(
                hypothesis_id,
                ev.evidence_id,
                supports=(outcome == ExperimentOutcome.SUPPORTED)
            )

        return exp

    def reject_hypothesis(self, hypothesis_id: str, rationale: str, evidence_id: Optional[str] = None) -> Hypothesis:
        """Step 8: Hypothesis Elimination."""
        self.state.set_stage(InvestigationStage.HYPOTHESIS_ELIMINATION)
        hypo = self.state.hypothesis_manager.update_status(
            hypothesis_id=hypothesis_id,
            new_status=HypothesisStatus.REJECTED,
            rationale=rationale,
            evidence_id=evidence_id,
        )
        self.state.append_finding(
            "Hypothesis Rejected",
            f"**{hypothesis_id} REJECTED:** {rationale}"
        )
        return hypo

    def identify_root_cause(
        self,
        hypothesis_id: str,
        what: str,
        why: str,
        where: str,
        how_confirmed: str,
    ) -> Hypothesis:
        """Step 9: Root Cause Identification."""
        self.state.set_stage(InvestigationStage.ROOT_CAUSE_IDENTIFICATION)

        # Guarded confirmation
        hypo = self.state.hypothesis_manager.update_status(
            hypothesis_id=hypothesis_id,
            new_status=HypothesisStatus.CONFIRMED,
            rationale=f"Empirically validated as Root Cause: {what}",
        )

        self._root_cause_details = {
            "what": what,
            "why": why,
            "where": where,
            "how_confirmed": how_confirmed,
        }

        if self.state.case:
            self.state.case.root_cause_hypothesis_id = hypothesis_id
            self.state.case.root_cause_summary = what
            self.state.save_case()

        # Record verified Root Cause evidence
        ev = self.state.evidence_ledger.record(
            source=f"root_cause_deduction:{hypothesis_id}",
            type="root_cause_conclusion",
            claim_status=ClaimStatus.VERIFIED,
            description=f"Root Cause Confirmed for {hypothesis_id}: {what}. (Located at: {where})",
            reliability=Reliability.HIGH,
            related_hypotheses=[hypothesis_id],
            metadata=self._root_cause_details,
        )

        self.state.append_finding(
            "Root Cause Confirmed",
            f"**Hypothesis {hypothesis_id} CONFIRMED**\n- **What:** {what}\n- **Why:** {why}\n- **Where:** {where}\n- **Proof:** {how_confirmed}"
        )
        return hypo

    def apply_minimal_fix(
        self,
        file_modifications: Dict[str, str],
        rationales: Dict[str, str],
    ) -> DiffAnalysisResult:
        """Step 10: Minimal Fix with Diff-based Reasoning."""
        self.state.set_stage(InvestigationStage.MINIMAL_FIX)

        diff_summaries: List[FileDiffSummary] = []
        changed_files_list: List[str] = []

        for rel_path, new_content in file_modifications.items():
            target_path = self.active_work_dir / rel_path
            before_content = ""
            if target_path.exists():
                before_content = target_path.read_text(encoding="utf-8")
                self._file_snapshots[rel_path] = before_content

            diff_summary = DiffAnalyzer.compare_texts(
                filepath=rel_path,
                before_text=before_content,
                after_text=new_content,
                rationale=rationales.get(rel_path, "Targeted surgical fix")
            )
            diff_summaries.append(diff_summary)

            # Apply change
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(new_content, encoding="utf-8")
            changed_files_list.append(rel_path)

        diff_analysis = DiffAnalyzer.evaluate_changes(diff_summaries)
        self._diff_analysis = diff_analysis

        if self.state.case:
            self.state.case.changed_files = changed_files_list
            self.state.save_case()

        # Record diff evidence
        self.state.evidence_ledger.record(
            source="minimal_fix_engine",
            type="code_diff",
            claim_status=ClaimStatus.OBSERVED,
            description=f"Minimal fix applied to {len(changed_files_list)} file(s). Blast radius: {diff_analysis.blast_radius}.",
            reliability=Reliability.HIGH,
            metadata=diff_analysis.to_dict(),
        )

        self.state.append_finding(
            "Minimal Fix Applied",
            f"Modified {len(changed_files_list)} file(s). Lines added: +{diff_analysis.total_added}, removed: -{diff_analysis.total_removed}. Blast radius: **{diff_analysis.blast_radius}**."
        )

        return diff_analysis

    def verify_fix(
        self,
        reproduction_command: Optional[str] = None,
        verification_runs: int = 10,
        regression_commands: Optional[List[str]] = None,
        expected_exit_code: int = 0,
        timeout_sec: float = 30.0,
    ) -> Dict[str, Any]:
        """Step 11 & 12: Independent Verification & Regression Testing."""
        self.state.set_stage(InvestigationStage.INDEPENDENT_VERIFICATION)

        cmd = reproduction_command or (self.state.case.reproduction_command if self.state.case else None)
        if not cmd:
            raise ValueError("No reproduction command provided for verification.")

        self.safety_guard.authorize_or_raise(cmd)

        # Statistical or deterministic verification
        if verification_runs > 1:
            stats = self.runner.run_statistical(
                command=cmd,
                runs=verification_runs,
                cwd=self.active_work_dir,
                timeout_sec=timeout_sec,
                expected_exit_code=expected_exit_code,
            )
            failures = stats["failures"]
            failure_rate = stats["failure_rate"]
        else:
            res = self.runner.execute_raw(cmd, cwd=self.active_work_dir, timeout_sec=timeout_sec)
            failures = 1 if (res.exit_code != expected_exit_code or res.timed_out) else 0
            failure_rate = 1.0 if failures > 0 else 0.0
            stats = {"total_runs": 1, "failures": failures, "failure_rate": failure_rate}

        # Run regression test suite if provided
        reg_passed = True
        regression_results = []
        if regression_commands:
            for reg_cmd in regression_commands:
                self.safety_guard.authorize_or_raise(reg_cmd)
                reg_res = self.runner.execute_raw(reg_cmd, cwd=self.active_work_dir, timeout_sec=timeout_sec)
                passed = (reg_res.exit_code == 0) and not reg_res.timed_out
                if not passed:
                    reg_passed = False
                regression_results.append({"cmd": reg_cmd, "passed": passed, "exit_code": reg_res.exit_code})

        verification_passed = (failures == 0) and reg_passed

        if self.state.case:
            self.state.case.verification_runs = verification_runs
            self.state.case.verification_passed = verification_passed
            self.state.save_case()

        # Compute empirical confidence score
        confidence = ConfidenceCalculator.evaluate(
            evidence_ledger=self.state.evidence_ledger,
            hypothesis_manager=self.state.hypothesis_manager,
            reproduction_rate=self.state.case.reproduction_rate if self.state.case else None,
            reproduction_runs=1,
            verification_runs=verification_runs,
            verification_failures=failures,
            regression_passed=reg_passed,
        )

        if self.state.case:
            self.state.case.confidence_score = confidence.score
            self.state.case.confidence_level = confidence.level
            self.state.case.confidence_basis = confidence.basis
            self.state.save_case()

        # Record verification evidence
        ev = self.state.evidence_ledger.record(
            source="independent_verification",
            type="verification_metric",
            claim_status=ClaimStatus.VERIFIED,
            description=f"Verification completed: {failures} failures across {verification_runs} runs ({failure_rate*100:.1f}% failure rate). Confidence: {confidence.level.value} ({confidence.score*100:.1f}%).",
            reliability=Reliability.HIGH,
            metadata={
                "verification_runs": verification_runs,
                "failures": failures,
                "confidence_score": confidence.score,
                "regression_passed": reg_passed,
            }
        )

        self.state.append_finding(
            "Independent Verification Completed",
            f"Post-fix execution: **{failures} failures** in {verification_runs} trials. Confidence: **{confidence.level.value}** ({confidence.score*100:.1f}%)."
        )

        return {
            "passed": verification_passed,
            "verification_runs": verification_runs,
            "failures": failures,
            "confidence": confidence.model_dump(),
            "regression_results": regression_results,
        }

    def conclude(
        self,
        verdict: InvestigationVerdict = InvestigationVerdict.SUCCESS,
        remaining_uncertainties: Optional[List[str]] = None,
    ) -> str:
        """Step 13: Conclude Investigation and Generate Final Report."""
        self.state.set_stage(InvestigationStage.REPORT_GENERATION)

        if self.state.case:
            self.state.case.verdict = verdict
            self.state.case.status = InvestigationStage.CLOSED
            self.state.case.closed_at = datetime.now(timezone.utc).isoformat()
            self.state.save_case()

        # Generate comprehensive markdown report
        reporter = ReportGenerator(self.state)
        report_md = reporter.generate_markdown(
            environment_info=self._env_info,
            root_cause_details=self._root_cause_details,
            diff_analysis=self._diff_analysis,
            remaining_uncertainties=remaining_uncertainties,
        )

        # If sandbox was used and verdict is SUCCESS, sync changes back to original project if desired
        if self.use_sandbox and self.sandbox:
            # We preserve changes in sandbox and report; user can sync or keep isolated
            pass

        return report_md

    def cleanup(self) -> None:
        """Clean up sandbox resources."""
        if self.sandbox:
            self.sandbox.exit(clean=True)
            self.sandbox = None
