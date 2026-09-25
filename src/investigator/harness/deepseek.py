"""DeepSeek Harness Adapter for AI Software Investigator.

Provides automated batch benchmark execution and evaluation interface compatible
with DeepSeek evaluation harnesses, SWE-bench style benchmarks, and automated test runners.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import time

from investigator.agent.core import AutonomousInvestigator
from investigator.agent.llm import BaseReasoningProvider, DeepSeekReasoningProvider, HeuristicForensicDriver
from investigator.engine.protocol import CaseCategory, InvestigationVerdict


@dataclass
class HarnessTaskSpec:
    """Specification of a benchmark or evaluation task instance."""
    instance_id: str
    problem_statement: str
    repo_dir: Path
    test_command: Optional[str] = None
    category: str = "bug"
    max_steps: int = 15
    timeout_seconds: int = 180
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], base_dir: Optional[Path] = None) -> "HarnessTaskSpec":
        repo_path = Path(data.get("repo_dir", "."))
        if base_dir and not repo_path.is_absolute():
            repo_path = base_dir / repo_path

        return cls(
            instance_id=data.get("instance_id", f"TASK-{int(time.time())}"),
            problem_statement=data.get("problem_statement") or data.get("problem") or "",
            repo_dir=repo_path.resolve(),
            test_command=data.get("test_command") or data.get("test_cmd"),
            category=data.get("category", "bug"),
            max_steps=int(data.get("max_steps", 15)),
            timeout_seconds=int(data.get("timeout_seconds", 180)),
            metadata=data.get("metadata", {}),
        )


@dataclass
class HarnessResult:
    """Evaluation result emitted by DeepSeek Harness."""
    instance_id: str
    verdict: str
    resolved: bool
    confidence_level: str
    confidence_score: float
    rule_of_three_bound: Optional[float]
    evidence_count: int
    hypotheses_tested: int
    patch_diff: str
    duration_seconds: float
    report_path: Optional[str]
    case_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "verdict": self.verdict,
            "resolved": self.resolved,
            "confidence_level": self.confidence_level,
            "confidence_score": round(self.confidence_score, 4),
            "rule_of_three_bound": round(self.rule_of_three_bound, 4) if self.rule_of_three_bound is not None else None,
            "evidence_count": self.evidence_count,
            "hypotheses_tested": self.hypotheses_tested,
            "patch_diff": self.patch_diff,
            "duration_seconds": round(self.duration_seconds, 2),
            "report_path": self.report_path,
            "case_id": self.case_id,
        }


class DeepSeekHarness:
    """Benchmark runner and evaluation harness for DeepSeek models."""

    def __init__(
        self,
        provider: Optional[BaseReasoningProvider] = None,
        use_deepseek_api: bool = False,
        deepseek_model: str = "deepseek-reasoner",
    ):
        if provider:
            self.provider = provider
        elif use_deepseek_api:
            self.provider = DeepSeekReasoningProvider(model=deepseek_model)
        else:
            self.provider = HeuristicForensicDriver()

    def run_task(self, spec: HarnessTaskSpec) -> HarnessResult:
        """Execute autonomous forensic investigation for a single harness task."""
        start_time = time.time()

        agent = AutonomousInvestigator(
            project_dir=spec.repo_dir,
            provider=self.provider,
            use_sandbox=True,
        )

        report_md = agent.investigate(
            problem_statement=spec.problem_statement,
            title=f"Harness Eval: {spec.instance_id}",
            category=CaseCategory(spec.category) if spec.category in [c.value for c in CaseCategory] else CaseCategory.BUG,
            repro_command=spec.test_command,
            max_steps=spec.max_steps,
        )

        state = agent.engine.state
        duration = time.time() - start_time
        case_obj = state.case
        verdict = case_obj.verdict.value if case_obj and case_obj.verdict else InvestigationVerdict.UNKNOWN.value
        resolved = (verdict == InvestigationVerdict.SUCCESS.value)

        # Extract patch diff
        diff_str = ""
        diff_file = state.artifacts_dir / "minimal_fix.patch"
        if diff_file.exists():
            diff_str = diff_file.read_text(encoding="utf-8")

        confidence_level = case_obj.confidence_level.value if case_obj else "UNKNOWN"
        confidence_score = case_obj.confidence_score if case_obj else 0.0
        
        # Calculate Rule of Three bound if verified runs > 0
        rule_of_three = None
        if case_obj and case_obj.verification_runs > 0:
            rule_of_three = 3.0 / float(case_obj.verification_runs)

        evidence_list = state.evidence_ledger.all()
        hypotheses_list = state.hypothesis_manager.all()

        report_file = state.investigation_dir / "report.md"
        report_path_str = str(report_file) if report_file.exists() else None

        return HarnessResult(
            instance_id=spec.instance_id,
            verdict=verdict,
            resolved=resolved,
            confidence_level=confidence_level,
            confidence_score=confidence_score,
            rule_of_three_bound=rule_of_three,
            evidence_count=len(evidence_list),
            hypotheses_tested=len(hypotheses_list),
            patch_diff=diff_str,
            duration_seconds=duration,
            report_path=report_path_str,
            case_id=case_obj.case_id if case_obj else "",
        )

    def run_suite(self, task_specs: List[HarnessTaskSpec]) -> List[HarnessResult]:
        """Execute a batch benchmark suite."""
        results = []
        for spec in task_specs:
            res = self.run_task(spec)
            results.append(res)
        return results
