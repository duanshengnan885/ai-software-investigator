"""Evidence data model for AI Software Investigator.

Implements the forensic Evidence record with anti-hallucination tracking.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from investigator.engine.protocol import ClaimStatus, Reliability


class Evidence(BaseModel):
    """Forensic evidence ledger record."""

    evidence_id: str = Field(..., description="Unique evidence ID (e.g. E-001)")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 timestamp when evidence was collected"
    )
    source: str = Field(..., description="Source of evidence (e.g., experiment:EXP-01, static_code, logs)")
    type: str = Field(
        ...,
        description="Evidence type (e.g., runtime_observation, log_trace, memory_profile, return_code, diff, boundary_measurement)"
    )
    claim_status: ClaimStatus = Field(
        default=ClaimStatus.OBSERVED,
        description="Epistemological status: Observed, Inferred, Hypothesized, Verified, or Unknown"
    )
    description: str = Field(..., description="Clear, factual summary of the evidence")
    raw_reference: Optional[str] = Field(
        default=None,
        description="Path to artifact file or verbatim excerpt containing the raw data"
    )
    reliability: Reliability = Field(
        default=Reliability.HIGH,
        description="Reliability score: HIGH (sandbox confirmed), MEDIUM (indirect log), LOW (unverified report)"
    )
    related_hypotheses: List[str] = Field(
        default_factory=list,
        description="Hypotheses directly informed or impacted by this evidence"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional structured payload (e.g., metrics, exit codes, thread count)"
    )

    def to_ledger_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary for evidence.jsonl."""
        return self.model_dump()
