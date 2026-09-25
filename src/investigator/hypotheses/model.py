"""Hypothesis data model for AI Software Investigator.

Represents an explicitly formulated, falsifiable hypothesis with state transitions.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from investigator.engine.protocol import HypothesisStatus


class HypothesisTransition(BaseModel):
    """Record of a hypothesis status transition."""

    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    from_status: HypothesisStatus
    to_status: HypothesisStatus
    rationale: str
    evidence_id: Optional[str] = None


class Hypothesis(BaseModel):
    """Falsifiable hypothesis tracked during an investigation."""

    hypothesis_id: str = Field(..., description="Unique hypothesis ID (e.g. H1, H2)")
    title: str = Field(..., description="Concise statement of the hypothesis")
    description: str = Field(..., description="Detailed mechanism explaining the failure")
    category: str = Field(default="general", description="Category: logic, concurrency, memory, io, etc.")
    status: HypothesisStatus = Field(default=HypothesisStatus.UNTESTED)
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Estimated probability (0.0 to 1.0) derived from evidence"
    )
    supporting_evidence: List[str] = Field(
        default_factory=list,
        description="List of evidence IDs that support this hypothesis"
    )
    contradicting_evidence: List[str] = Field(
        default_factory=list,
        description="List of evidence IDs that contradict this hypothesis"
    )
    experiments: List[str] = Field(
        default_factory=list,
        description="List of experiment IDs executed to test this hypothesis"
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    history: List[HypothesisTransition] = Field(
        default_factory=list,
        description="Audit log of state transitions"
    )

    def record_transition(
        self,
        new_status: HypothesisStatus,
        rationale: str,
        evidence_id: Optional[str] = None
    ) -> None:
        """Record status transition with rationale."""
        if self.status != new_status:
            transition = HypothesisTransition(
                from_status=self.status,
                to_status=new_status,
                rationale=rationale,
                evidence_id=evidence_id
            )
            self.history.append(transition)
            self.status = new_status
            self.updated_at = datetime.now(timezone.utc).isoformat()
