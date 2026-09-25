"""Experiment Planner for AI Software Investigator.

Implements 'Information Gain First' heuristic to prioritize experiments that
efficiently differentiate active hypotheses with minimal cost and risk.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from investigator.hypotheses.model import Hypothesis


class ExperimentCandidate(BaseModel):
    """A proposed experiment awaiting prioritization and execution."""

    candidate_id: str
    title: str
    target_hypothesis_ids: List[str] = Field(
        ...,
        description="Hypotheses this experiment is capable of supporting or refuting"
    )
    command: str
    expected_duration_sec: float = 2.0
    risk_level: str = Field(default="LOW", description="LOW, MEDIUM, HIGH")
    differentiating_power: float = Field(
        default=0.8,
        description="Ability of this experiment to cleanly separate competing hypotheses (0.0 to 1.0)"
    )
    predicted_outcomes: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping from hypothesis_id -> predicted observation"
    )

    def calculate_priority_score(self, total_active_hypotheses: int) -> float:
        """Calculate Information-Gain-to-Cost priority score."""
        # Coverage fraction of active hypotheses
        coverage = len(self.target_hypothesis_ids) / max(1, total_active_hypotheses)
        info_gain = coverage * self.differentiating_power

        risk_penalty = {"LOW": 1.0, "MEDIUM": 1.5, "HIGH": 3.0}.get(self.risk_level.upper(), 1.0)
        cost_factor = max(0.5, self.expected_duration_sec) * risk_penalty

        score = (info_gain * 100.0) / cost_factor
        return round(score, 3)


class ExperimentPlanner:
    """Selects and prioritizes experiments to maximize information gain."""

    def __init__(self, active_hypotheses: List[Hypothesis]):
        self.active_hypotheses = active_hypotheses

    def prioritize(self, candidates: List[ExperimentCandidate]) -> List[ExperimentCandidate]:
        """Rank candidate experiments by Information Gain First."""
        total_active = len(self.active_hypotheses)
        scored = [
            (c.calculate_priority_score(total_active), c)
            for c in candidates
        ]
        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored]

    def select_next(self, candidates: List[ExperimentCandidate]) -> Optional[ExperimentCandidate]:
        """Select the highest-priority experiment candidate."""
        ranked = self.prioritize(candidates)
        return ranked[0] if ranked else None
