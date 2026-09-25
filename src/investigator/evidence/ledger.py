"""Evidence Ledger implementation for AI Software Investigator.

Manages persistent append-only storage in evidence.jsonl, indexing,
and causal chain validation.
"""

from pathlib import Path
from typing import Dict, List, Optional
import json

from investigator.engine.protocol import ClaimStatus, Reliability
from investigator.evidence.model import Evidence


class EvidenceLedger:
    """Persistent evidence ledger ensuring complete auditability and chain of custody."""

    def __init__(self, ledger_path: Path):
        self.ledger_path = Path(ledger_path)
        self._evidence_list: List[Evidence] = []
        self._by_id: Dict[str, Evidence] = {}
        self._counter: int = 0
        self.load()

    def load(self) -> None:
        """Load existing ledger entries from disk if file exists."""
        self._evidence_list.clear()
        self._by_id.clear()
        self._counter = 0

        if not self.ledger_path.exists():
            return

        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    ev = Evidence.model_validate(data)
                    self._evidence_list.append(ev)
                    self._by_id[ev.evidence_id] = ev
                    # Track highest numerical ID
                    if ev.evidence_id.startswith("E-"):
                        try:
                            num = int(ev.evidence_id[2:])
                            if num > self._counter:
                                self._counter = num
                        except ValueError:
                            pass
                except Exception:
                    continue

    def next_id(self) -> str:
        """Generate next sequential evidence ID (e.g. E-001)."""
        self._counter += 1
        return f"E-{self._counter:03d}"

    def record(
        self,
        source: str,
        type: str,
        description: str,
        claim_status: ClaimStatus = ClaimStatus.OBSERVED,
        raw_reference: Optional[str] = None,
        reliability: Reliability = Reliability.HIGH,
        related_hypotheses: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        evidence_id: Optional[str] = None,
    ) -> Evidence:
        """Record a verified piece of evidence into the ledger and persist to disk.

        Enforces that any claim must have an explicit source and description.
        """
        if not source or not description:
            raise ValueError("Evidence must have both a non-empty source and description.")

        if evidence_id is None:
            evidence_id = self.next_id()

        ev = Evidence(
            evidence_id=evidence_id,
            source=source,
            type=type,
            claim_status=claim_status,
            description=description,
            raw_reference=raw_reference,
            reliability=reliability,
            related_hypotheses=related_hypotheses or [],
            metadata=metadata or {},
        )

        self._evidence_list.append(ev)
        self._by_id[ev.evidence_id] = ev

        # Ensure directory exists and append directly to file
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev.to_ledger_dict(), ensure_ascii=False) + "\n")

        return ev

    def get(self, evidence_id: str) -> Optional[Evidence]:
        """Retrieve evidence by ID."""
        return self._by_id.get(evidence_id)

    def all(self) -> List[Evidence]:
        """Return all recorded evidence items."""
        return list(self._evidence_list)

    def by_hypothesis(self, hypothesis_id: str) -> List[Evidence]:
        """Return all evidence items linked to a given hypothesis."""
        return [ev for ev in self._evidence_list if hypothesis_id in ev.related_hypotheses]

    def by_reliability(self, reliability: Reliability) -> List[Evidence]:
        """Filter evidence items by reliability rating."""
        return [ev for ev in self._evidence_list if ev.reliability == reliability]

    def by_claim_status(self, claim_status: ClaimStatus) -> List[Evidence]:
        """Filter evidence items by claim status."""
        return [ev for ev in self._evidence_list if ev.claim_status == claim_status]

    def trace_chain(self, hypothesis_id: str) -> List[Dict]:
        """Trace the causal evidence chain for a hypothesis.

        Returns evidence items, their source experiments, and raw references.
        """
        related = self.by_hypothesis(hypothesis_id)
        chain = []
        for ev in related:
            chain.append({
                "evidence_id": ev.evidence_id,
                "type": ev.type,
                "status": ev.claim_status.value,
                "source": ev.source,
                "description": ev.description,
                "reliability": ev.reliability.value,
                "raw_reference": ev.raw_reference,
                "metadata": ev.metadata
            })
        return chain

    def count(self) -> int:
        """Return total evidence count."""
        return len(self._evidence_list)
