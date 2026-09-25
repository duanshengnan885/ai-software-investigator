"""Investigation State Management for AI Software Investigator.

Manages the persistent .investigation/ repository, case metadata, timelines,
and provides unified access to ledgers and managers.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from pydantic import BaseModel, Field

from investigator.engine.protocol import (
    CaseCategory,
    ConfidenceLevel,
    InvestigationStage,
    InvestigationVerdict,
)
from investigator.evidence.ledger import EvidenceLedger
from investigator.hypotheses.manager import HypothesisManager


class TimelineEvent(BaseModel):
    """Event entry in timeline.jsonl."""

    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    stage: str
    event_type: str
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CaseMetadata(BaseModel):
    """Metadata recorded in case.json."""

    case_id: str
    title: str
    problem_statement: str
    category: CaseCategory = CaseCategory.BUG
    status: InvestigationStage = InvestigationStage.INTAKE
    verdict: Optional[InvestigationVerdict] = None
    target_dir: str
    started_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    closed_at: Optional[str] = None
    root_cause_hypothesis_id: Optional[str] = None
    root_cause_summary: Optional[str] = None
    confidence_score: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.LOW
    confidence_basis: List[str] = Field(default_factory=list)
    reproduction_command: Optional[str] = None
    reproduction_rate: Optional[float] = None
    verification_runs: int = 0
    verification_passed: bool = False
    changed_files: List[str] = Field(default_factory=list)


class InvestigationState:
    """Encapsulates persistent investigation state inside the target's .investigation/ folder."""

    INVESTIGATION_DIR_NAME = ".investigation"

    def __init__(self, root_dir: Path, case_id: Optional[str] = None):
        self.root_dir = Path(root_dir).resolve()
        self.investigation_dir = self.root_dir / self.INVESTIGATION_DIR_NAME
        self.artifacts_dir = self.investigation_dir / "artifacts"
        self.case_file = self.investigation_dir / "case.json"
        self.evidence_file = self.investigation_dir / "evidence.jsonl"
        self.hypotheses_file = self.investigation_dir / "hypotheses.json"
        self.experiments_file = self.investigation_dir / "experiments.jsonl"
        self.timeline_file = self.investigation_dir / "timeline.jsonl"
        self.findings_file = self.investigation_dir / "findings.md"

        self._ensure_structure()

        self.case: Optional[CaseMetadata] = None
        self._load_case(case_id)

        self.evidence_ledger = EvidenceLedger(self.evidence_file)
        self.hypothesis_manager = HypothesisManager(self.hypotheses_file)

    def _ensure_structure(self) -> None:
        """Create directory structure if not present."""
        self.investigation_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def _load_case(self, case_id: Optional[str] = None) -> None:
        """Load case.json if it exists."""
        if self.case_file.exists():
            try:
                with open(self.case_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.case = CaseMetadata.model_validate(data)
            except Exception:
                self.case = None

    def initialize_case(
        self,
        case_id: str,
        title: str,
        problem_statement: str,
        category: CaseCategory = CaseCategory.BUG,
    ) -> CaseMetadata:
        """Create and persist a new investigation case."""
        self.case = CaseMetadata(
            case_id=case_id,
            title=title,
            problem_statement=problem_statement,
            category=category,
            target_dir=str(self.root_dir),
            status=InvestigationStage.INTAKE,
        )
        self.save_case()
        self.record_timeline(
            stage=InvestigationStage.INTAKE.value,
            event_type="CASE_INITIALIZED",
            description=f"Investigation initialized for {case_id}: {title}"
        )
        # Initialize findings.md
        if not self.findings_file.exists():
            self.findings_file.write_text(
                f"# Investigation Findings: {title}\n\n**Case ID:** `{case_id}`\n\n## Initial Problem Statement\n{problem_statement}\n\n---\n",
                encoding="utf-8"
            )
        return self.case

    def save_case(self) -> None:
        """Save case metadata to case.json."""
        if not self.case:
            return
        self.case.updated_at = datetime.now(timezone.utc).isoformat()
        with open(self.case_file, "w", encoding="utf-8") as f:
            json.dump(self.case.model_dump(), f, indent=2, ensure_ascii=False)

    def set_stage(self, stage: InvestigationStage, description: Optional[str] = None) -> None:
        """Transition investigation lifecycle stage."""
        if self.case:
            self.case.status = stage
            self.save_case()
        self.record_timeline(
            stage=stage.value,
            event_type="STAGE_TRANSITION",
            description=description or f"Entered stage: {stage.value}"
        )

    def record_timeline(self, stage: str, event_type: str, description: str, metadata: Optional[Dict] = None) -> None:
        """Append an event to timeline.jsonl."""
        event = TimelineEvent(
            stage=stage,
            event_type=event_type,
            description=description,
            metadata=metadata or {}
        )
        with open(self.timeline_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event.model_dump(), ensure_ascii=False) + "\n")

    def append_finding(self, section: str, text: str) -> None:
        """Append entry to findings.md."""
        with open(self.findings_file, "a", encoding="utf-8") as f:
            f.write(f"\n### {section} ({datetime.now(timezone.utc).strftime('%H:%M:%S')})\n{text}\n")
