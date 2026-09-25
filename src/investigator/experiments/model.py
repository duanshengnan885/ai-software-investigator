"""Experiment data models for AI Software Investigator.

Represents reproducible empirical experiments with predictions and outcomes.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from investigator.engine.protocol import ExperimentOutcome


class ExperimentRecord(BaseModel):
    """Forensic record of an empirical experiment."""

    experiment_id: str = Field(..., description="Unique experiment ID (e.g. EXP-001)")
    title: str = Field(..., description="Concise title of the experiment")
    objective: str = Field(..., description="Specific question or condition being tested")
    hypothesis_id: Optional[str] = Field(None, description="Hypothesis tested by this experiment")
    preconditions: str = Field(default="", description="Required initial state or setup")
    environment: Dict[str, Any] = Field(
        default_factory=dict,
        description="Operating system, runtime, architecture, versions"
    )
    command: str = Field(..., description="Exact command executed")
    cwd: Optional[str] = Field(default=None, description="Working directory")
    inputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Test inputs, flags, environment variables, or payloads"
    )
    expected_prediction: str = Field(
        ...,
        description="Predicted outcome if hypothesis holds true vs false"
    )
    actual_result: str = Field(
        default="",
        description="Observed behavior, outputs, or error patterns"
    )
    exit_code: Optional[int] = Field(default=None, description="Process exit code")
    duration_ms: float = Field(default=0.0, description="Execution duration in milliseconds")
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Quantitative measurements (e.g. failure_rate, peak_memory_mb, thread_count)"
    )
    artifacts: List[str] = Field(
        default_factory=list,
        description="Relative paths to saved stdout/stderr logs or dumps"
    )
    outcome: ExperimentOutcome = Field(
        default=ExperimentOutcome.INCONCLUSIVE,
        description="Experiment conclusion: SUPPORTED, WEAKENED, REJECTED, INCONCLUSIVE"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_ledger_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for experiments.jsonl."""
        return self.model_dump()
