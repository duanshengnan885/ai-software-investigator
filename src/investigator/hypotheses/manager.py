"""Hypothesis Manager implementation for AI Software Investigator.

Manages the hypothesis pool, ensures rigorous state transitions, and enforces
that conclusions are mathematically and empirically sound.
"""

from pathlib import Path
from typing import Dict, List, Optional
import json

from investigator.engine.protocol import HypothesisStatus
from investigator.hypotheses.model import Hypothesis


class HypothesisManager:
    """Manages the full lifecycle of falsifiable hypotheses."""

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        self._hypotheses: Dict[str, Hypothesis] = {}
        self._counter: int = 0
        self.load()

    def load(self) -> None:
        """Load hypotheses from JSON file if it exists."""
        self._hypotheses.clear()
        self._counter = 0

        if not self.file_path.exists():
            return

        with open(self.file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                for item in data:
                    hypo = Hypothesis.model_validate(item)
                    self._hypotheses[hypo.hypothesis_id] = hypo
                    if hypo.hypothesis_id.startswith("H"):
                        try:
                            num = int(hypo.hypothesis_id[1:])
                            if num > self._counter:
                                self._counter = num
                        except ValueError:
                            pass
            except Exception:
                pass

    def save(self) -> None:
        """Persist all hypotheses to JSON file."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        serializable = [h.model_dump() for h in self._hypotheses.values()]
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)

    def next_id(self) -> str:
        """Generate next hypothesis ID (e.g. H1, H2, ...)."""
        self._counter += 1
        return f"H{self._counter}"

    def create(
        self,
        title: str,
        description: str,
        category: str = "general",
        hypothesis_id: Optional[str] = None,
        initial_status: HypothesisStatus = HypothesisStatus.UNTESTED,
    ) -> Hypothesis:
        """Create and register a new hypothesis."""
        if not title or not description:
            raise ValueError("Hypothesis must have a title and description.")

        if hypothesis_id is None:
            hypothesis_id = self.next_id()

        hypo = Hypothesis(
            hypothesis_id=hypothesis_id,
            title=title,
            description=description,
            category=category,
            status=initial_status,
            confidence=0.5,
        )
        self._hypotheses[hypo.hypothesis_id] = hypo
        self.save()
        return hypo

    def get(self, hypothesis_id: str) -> Optional[Hypothesis]:
        """Get hypothesis by ID."""
        return self._hypotheses.get(hypothesis_id)

    def all(self) -> List[Hypothesis]:
        """Return all hypotheses."""
        return list(self._hypotheses.values())

    def active(self) -> List[Hypothesis]:
        """Return hypotheses that are not REJECTED."""
        return [
            h for h in self._hypotheses.values()
            if h.status not in (HypothesisStatus.REJECTED, HypothesisStatus.CONFIRMED)
        ]

    def confirmed(self) -> Optional[Hypothesis]:
        """Return the CONFIRMED hypothesis if one exists."""
        for h in self._hypotheses.values():
            if h.status == HypothesisStatus.CONFIRMED:
                return h
        return None

    def update_status(
        self,
        hypothesis_id: str,
        new_status: HypothesisStatus,
        rationale: str,
        evidence_id: Optional[str] = None,
    ) -> Hypothesis:
        """Transition hypothesis status with forensic integrity checks.

        Enforces:
        - Cannot CONFIRM if contradicting evidence exists.
        - Cannot CONFIRM without supporting evidence.
        - Cannot REJECT without explicit rationale/evidence.
        """
        hypo = self.get(hypothesis_id)
        if not hypo:
            raise KeyError(f"Hypothesis {hypothesis_id} not found.")

        # Forensic Integrity Guardrails
        if new_status == HypothesisStatus.CONFIRMED:
            if not hypo.supporting_evidence and not evidence_id:
                raise ValueError(
                    f"Forensic violation: Cannot CONFIRM {hypothesis_id} without verified supporting evidence."
                )
            if hypo.contradicting_evidence:
                raise ValueError(
                    f"Forensic violation: Cannot CONFIRM {hypothesis_id} while contradictory evidence {hypo.contradicting_evidence} remains unrefuted."
                )

        if new_status == HypothesisStatus.REJECTED:
            if not hypo.contradicting_evidence and not evidence_id and not hypo.experiments:
                raise ValueError(
                    f"Forensic violation: Cannot REJECT {hypothesis_id} without empirical evidence or experiment."
                )

        hypo.record_transition(new_status, rationale, evidence_id)
        self._recalculate_confidence(hypo)
        self.save()
        return hypo

    def link_evidence(
        self,
        hypothesis_id: str,
        evidence_id: str,
        supports: bool = True
    ) -> None:
        """Link an evidence item to a hypothesis and recalculate confidence."""
        hypo = self.get(hypothesis_id)
        if not hypo:
            raise KeyError(f"Hypothesis {hypothesis_id} not found.")

        if supports:
            if evidence_id not in hypo.supporting_evidence:
                hypo.supporting_evidence.append(evidence_id)
        else:
            if evidence_id not in hypo.contradicting_evidence:
                hypo.contradicting_evidence.append(evidence_id)

        self._recalculate_confidence(hypo)
        self.save()

    def link_experiment(self, hypothesis_id: str, experiment_id: str) -> None:
        """Associate an experiment with a hypothesis."""
        hypo = self.get(hypothesis_id)
        if not hypo:
            raise KeyError(f"Hypothesis {hypothesis_id} not found.")

        if experiment_id not in hypo.experiments:
            hypo.experiments.append(experiment_id)
        self.save()

    def _recalculate_confidence(self, hypo: Hypothesis) -> None:
        """Calculate dynamic confidence score based on supporting vs contradicting evidence."""
        if hypo.status == HypothesisStatus.CONFIRMED:
            hypo.confidence = 0.95
            return
        if hypo.status == HypothesisStatus.REJECTED:
            hypo.confidence = 0.05
            return

        supp_count = len(hypo.supporting_evidence)
        cont_count = len(hypo.contradicting_evidence)

        if supp_count == 0 and cont_count == 0:
            hypo.confidence = 0.50
            return

        # Bayesian-inspired confidence adjustment
        score = 0.50 + (supp_count * 0.15) - (cont_count * 0.25)
        hypo.confidence = max(0.05, min(0.90, round(score, 3)))
