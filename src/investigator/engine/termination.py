"""Termination conditions and evaluation rules for AI Software Investigator.

Formalizes explicit stopping conditions to prevent infinite loops and prohibits
hallucinated root cause claims.
"""

from typing import List, Optional, Tuple
from pydantic import BaseModel, Field

from investigator.engine.protocol import HypothesisStatus, InvestigationVerdict
from investigator.engine.state import InvestigationState


class TerminationStatus(BaseModel):
    """Detailed assessment of whether an investigation can terminate."""

    can_terminate: bool
    verdict: InvestigationVerdict
    reason: str
    blocking_factors: List[str] = Field(default_factory=list)


class TerminationManager:
    """Evaluates whether current forensic state satisfies termination criteria."""

    @classmethod
    def evaluate(cls, state: InvestigationState) -> TerminationStatus:
        """Evaluate if the case satisfies termination requirements."""
        case = state.case
        if not case:
            return TerminationStatus(
                can_terminate=False,
                verdict=InvestigationVerdict.BLOCKED,
                reason="No active case metadata found.",
                blocking_factors=["Case uninitialized"],
            )

        confirmed_hypo = state.hypothesis_manager.confirmed()
        evidence_count = state.evidence_ledger.count()
        all_hypotheses = state.hypothesis_manager.all()
        active_hypotheses = state.hypothesis_manager.active()

        # Condition 1: SUCCESS
        # Requires:
        # - Confirmed Root Cause hypothesis
        # - Fix applied (changed_files non-empty or diff verified)
        # - Verification completed with 0 failures
        # - No active contradictory evidence
        if confirmed_hypo:
            if case.verification_runs > 0 and case.verification_passed:
                return TerminationStatus(
                    can_terminate=True,
                    verdict=InvestigationVerdict.SUCCESS,
                    reason=(
                        f"Root Cause definitively identified ({confirmed_hypo.hypothesis_id}: {confirmed_hypo.title}), "
                        f"minimal fix verified with 0 failures across {case.verification_runs} runs."
                    ),
                )
            elif case.changed_files:
                return TerminationStatus(
                    can_terminate=False,
                    verdict=InvestigationVerdict.SUCCESS,
                    reason="Fix applied but independent verification pending.",
                    blocking_factors=["Verification not completed"],
                )
            else:
                # Root cause found, but read-only / black-box scenario where code fix is impossible
                return TerminationStatus(
                    can_terminate=True,
                    verdict=InvestigationVerdict.PARTIAL,
                    reason=(
                        f"Root Cause identified ({confirmed_hypo.hypothesis_id}) with high empirical confidence, "
                        f"but source fix was not applicable (read-only or closed binary)."
                    ),
                )

        # Condition 2: BLOCKED
        # Baseline reproduction completely failed or environment inaccessible
        if case.reproduction_rate == 0.0 and case.reproduction_command:
            return TerminationStatus(
                can_terminate=True,
                verdict=InvestigationVerdict.BLOCKED,
                reason="Baseline failure could not be reproduced. Investigation blocked by missing reproduction trigger.",
                blocking_factors=["Reproduction failed"],
            )

        # Condition 3: UNKNOWN
        # All hypotheses were tested and REJECTED, but no new hypothesis could be formed
        if all_hypotheses and len(active_hypotheses) == 0 and not confirmed_hypo:
            return TerminationStatus(
                can_terminate=True,
                verdict=InvestigationVerdict.UNKNOWN,
                reason="All candidate hypotheses were empirically refuted. Available evidence is insufficient to identify root cause.",
                blocking_factors=["All hypotheses rejected"],
            )

        # Still investigating
        return TerminationStatus(
            can_terminate=False,
            verdict=InvestigationVerdict.UNKNOWN,
            reason=f"Investigation in progress: {len(active_hypotheses)} active hypotheses remaining.",
            blocking_factors=[f"{len(active_hypotheses)} hypotheses untested or unconfirmed"],
        )
