"""Experiment Runner implementation for AI Software Investigator.

Delegates execution to ProcessSandbox for process tree isolation, resource monitoring,
clean environments, and statistical multi-run evaluations.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import json
import os
import time

try:
    import psutil
except ImportError:
    psutil = None

from investigator.engine.protocol import ExperimentOutcome
from investigator.experiments.model import ExperimentRecord
from investigator.sandbox.process import ProcessSandbox


class ExecutionResult:
    """Standardized result of an experiment execution."""

    def __init__(
        self,
        command: str,
        exit_code: int,
        stdout: str,
        stderr: str,
        duration_ms: float,
        timed_out: bool = False,
        peak_memory_mb: float = 0.0,
    ):
        self.command = command
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.duration_ms = duration_ms
        self.timed_out = timed_out
        self.peak_memory_mb = peak_memory_mb


class ExperimentRunner:
    """Executes empirical experiments via ProcessSandbox and records reproducible outcomes."""

    def __init__(self, artifacts_dir: Path, ledger_path: Optional[Path] = None, default_cwd: Optional[Path] = None):
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path = Path(ledger_path) if ledger_path else None
        self.default_cwd = Path(default_cwd).resolve() if default_cwd else Path.cwd()
        self._counter = 0
        self._load_counter()

    def _load_counter(self) -> None:
        """Infer next experiment ID from existing ledger."""
        if not self.ledger_path or not self.ledger_path.exists():
            return
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    exp_id = data.get("experiment_id", "")
                    if exp_id.startswith("EXP-"):
                        num = int(exp_id[4:])
                        if num > self._counter:
                            self._counter = num
                except Exception:
                    pass

    def next_id(self) -> str:
        """Generate next experiment ID (e.g. EXP-001)."""
        self._counter += 1
        return f"EXP-{self._counter:03d}"

    def execute_raw(
        self,
        command: Union[str, List[str]],
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        stdin_input: Optional[str] = None,
        timeout_sec: float = 30.0,
    ) -> ExecutionResult:
        """Execute command safely via ProcessSandbox with tree-killing and clean environment."""
        work_dir = Path(cwd).resolve() if cwd else self.default_cwd
        sandbox = ProcessSandbox(working_dir=work_dir, sanitize_env=True)

        exit_code, stdout, stderr, timed_out, duration_ms = sandbox.run(
            command=command,
            timeout_sec=timeout_sec,
            stdin_input=stdin_input,
            custom_env=env,
        )

        # Peak memory snapshot if available
        peak_mem = 0.0
        if psutil:
            try:
                peak_mem = round(psutil.Process().memory_info().rss / (1024 * 1024), 2)
            except Exception:
                pass

        cmd_str = " ".join(command) if isinstance(command, list) else command

        return ExecutionResult(
            command=cmd_str,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            timed_out=timed_out,
            peak_memory_mb=peak_mem,
        )

    def run_statistical(
        self,
        command: Union[str, List[str]],
        runs: int = 50,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        timeout_sec: float = 10.0,
        expected_exit_code: int = 0,
    ) -> Dict[str, Any]:
        """Execute a command repeatedly to quantify intermittent/flaky behavior."""
        successes = 0
        failures = 0
        exit_codes: Dict[int, int] = {}
        durations: List[float] = []
        sample_errors: List[str] = []

        for _ in range(runs):
            res = self.execute_raw(command, cwd=cwd, env=env, timeout_sec=timeout_sec)
            durations.append(res.duration_ms)
            exit_codes[res.exit_code] = exit_codes.get(res.exit_code, 0) + 1

            if res.exit_code == expected_exit_code and not res.timed_out:
                successes += 1
            else:
                failures += 1
                if len(sample_errors) < 3 and res.stderr:
                    sample_errors.append(res.stderr.strip()[:200])

        failure_rate = round(failures / runs, 4)
        avg_duration = round(sum(durations) / len(durations), 2) if durations else 0.0

        return {
            "total_runs": runs,
            "successes": successes,
            "failures": failures,
            "failure_rate": failure_rate,
            "exit_codes": exit_codes,
            "avg_duration_ms": avg_duration,
            "sample_errors": sample_errors,
        }

    def record_experiment(
        self,
        title: str,
        objective: str,
        expected_prediction: str,
        command: Union[str, List[str]],
        actual_result: str,
        outcome: ExperimentOutcome,
        hypothesis_id: Optional[str] = None,
        cwd: Optional[str] = None,
        inputs: Optional[Dict] = None,
        exit_code: Optional[int] = None,
        duration_ms: float = 0.0,
        metrics: Optional[Dict] = None,
        raw_stdout: Optional[str] = None,
        raw_stderr: Optional[str] = None,
        experiment_id: Optional[str] = None,
    ) -> ExperimentRecord:
        """Create, save artifacts for, and persist an experiment record."""
        if experiment_id is None:
            experiment_id = self.next_id()

        artifacts: List[str] = []

        if raw_stdout is not None:
            out_file = self.artifacts_dir / f"{experiment_id}_stdout.log"
            out_file.write_text(raw_stdout, encoding="utf-8")
            artifacts.append(f"artifacts/{out_file.name}")

        if raw_stderr is not None:
            err_file = self.artifacts_dir / f"{experiment_id}_stderr.log"
            err_file.write_text(raw_stderr, encoding="utf-8")
            artifacts.append(f"artifacts/{err_file.name}")

        cmd_str = " ".join(command) if isinstance(command, list) else command

        record = ExperimentRecord(
            experiment_id=experiment_id,
            title=title,
            objective=objective,
            hypothesis_id=hypothesis_id,
            command=cmd_str,
            cwd=cwd,
            inputs=inputs or {},
            expected_prediction=expected_prediction,
            actual_result=actual_result,
            exit_code=exit_code,
            duration_ms=duration_ms,
            metrics=metrics or {},
            artifacts=artifacts,
            outcome=outcome,
        )

        if self.ledger_path:
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record.to_ledger_dict(), ensure_ascii=False) + "\n")

        return record
