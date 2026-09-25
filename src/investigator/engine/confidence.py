"""Evidence-based Confidence and Statistical Significance Engine for AI Software Investigator.

Combines multi-factor forensic empirical scoring with mathematical Binomial Confidence Intervals
(Rule of Three for zero-failure verification and Wilson score interval for failure rates).
"""

from typing import Any, Dict, List, Optional, Tuple
import math
from pydantic import BaseModel, Field

from investigator.engine.protocol import ConfidenceLevel, HypothesisStatus, Reliability
from investigator.evidence.ledger import EvidenceLedger
from investigator.hypotheses.manager import HypothesisManager


class StatisticalInterval(BaseModel):
    """Rigorous binomial confidence interval for failure probability."""

    trials: int
    observed_failures: int
    observed_rate: float
    confidence_level_pct: float = 95.0
    upper_bound: float
    lower_bound: float
    method: str
    description: str


class ConfidenceFactor(BaseModel):
    """An individual empirical factor contributing to the overall forensic audit score."""

    name: str
    weight: float
    achieved: bool
    explanation: str


class ConfidenceAssessment(BaseModel):
    """Formal confidence assessment report combining empirical scoring and statistical bounds."""

    score: float = Field(..., ge=0.0, le=1.0, description="Empirical audit completeness score (0.0 to 1.0)")
    level: ConfidenceLevel
    statistical_interval: Optional[StatisticalInterval] = None
    factors: List[ConfidenceFactor]
    basis: List[str] = Field(..., description="Human-readable justification points")


class ConfidenceCalculator:
    """Computes empirical confidence and exact statistical binomial intervals."""

    @staticmethod
    def calculate_binomial_bounds(
        trials: int,
        failures: int,
        confidence: float = 0.95,
    ) -> Optional[StatisticalInterval]:
        """Compute statistical upper and lower bounds for failure rate.

        When failures == 0:
            Uses the mathematical 'Rule of Three' (Hanley & Lippman-Hand, 1983):
            Upper 95% bound p <= -ln(1 - 0.95) / N = -ln(0.05) / N ~ 2.996 / N ~ 3 / N.
        When failures > 0:
            Uses Wilson score interval.
        """
        if trials <= 0:
            return None

        p_hat = failures / trials

        if failures == 0:
            # Rule of Three for zero-failure trials
            alpha = 1.0 - confidence
            upper = round(-math.log(alpha) / trials, 4)
            lower = 0.0
            method = "Rule of Three (Zero-Failure Interval)"
            desc = (
                f"No failures observed in {trials} independent trials. "
                f"At {confidence*100:.0f}% confidence, the true failure probability p <= {upper*100:.2f}%."
            )
        else:
            # Wilson Score Interval (z = 1.96 for 95%)
            z = 1.95996 if abs(confidence - 0.95) < 0.01 else 2.576
            denominator = 1.0 + (z**2) / trials
            center = (p_hat + (z**2) / (2 * trials)) / denominator
            spread = (z / denominator) * math.sqrt(
                (p_hat * (1.0 - p_hat) / trials) + ((z**2) / (4 * trials**2))
            )
            lower = max(0.0, round(center - spread, 4))
            upper = min(1.0, round(center + spread, 4))
            method = "Wilson Score Interval"
            desc = (
                f"Observed {failures}/{trials} failures ({p_hat*100:.1f}%). "
                f"True failure probability is within [{lower*100:.2f}%, {upper*100:.2f}%] at {confidence*100:.0f}% confidence."
            )

        return StatisticalInterval(
            trials=trials,
            observed_failures=failures,
            observed_rate=round(p_hat, 4),
            confidence_level_pct=confidence * 100.0,
            upper_bound=upper,
            lower_bound=lower,
            method=method,
            description=desc,
        )

    @classmethod
    def evaluate(
        cls,
        evidence_ledger: EvidenceLedger,
        hypothesis_manager: HypothesisManager,
        reproduction_rate: Optional[float] = None,
        reproduction_runs: int = 1,
        verification_runs: int = 0,
        verification_failures: int = 0,
        regression_passed: bool = False,
    ) -> ConfidenceAssessment:
        """Compute rigorous multi-factor score and statistical bounds."""
        factors: List[ConfidenceFactor] = []
        basis: List[str] = []

        confirmed_hypo = hypothesis_manager.confirmed()
        all_hypotheses = hypothesis_manager.all()
        rejected_hypotheses = [h for h in all_hypotheses if h.status == HypothesisStatus.REJECTED]
        active_hypotheses = hypothesis_manager.active()

        # 1. Baseline Reproduction Factor
        repro_achieved = False
        repro_exp = "No baseline reproduction established."
        if reproduction_rate is not None and reproduction_rate > 0.0:
            repro_achieved = True
            repro_exp = f"Baseline reproduction verified: {reproduction_rate*100:.1f}% failure rate across {reproduction_runs} trial(s)."
            basis.append(f"Problem reproduced with {reproduction_rate*100:.1f}% trigger rate ({reproduction_runs} run(s))")
        factors.append(ConfidenceFactor(
            name="Baseline Reproduction",
            weight=0.20,
            achieved=repro_achieved,
            explanation=repro_exp
        ))

        # 2. Independent Empirical Evidence Factor
        supp_evidence = []
        if confirmed_hypo:
            supp_evidence = [
                evidence_ledger.get(eid) for eid in confirmed_hypo.supporting_evidence
                if evidence_ledger.get(eid) is not None
            ]
        high_rel_count = sum(1 for e in supp_evidence if e and e.reliability == Reliability.HIGH)

        evidence_achieved = (high_rel_count >= 1)
        evidence_exp = f"Confirmed root cause supported by {high_rel_count} high-reliability empirical evidence item(s)."
        if evidence_achieved:
            basis.append(f"Supported by {high_rel_count} verified high-reliability evidence record(s)")
        factors.append(ConfidenceFactor(
            name="Empirical Evidence Support",
            weight=0.20,
            achieved=evidence_achieved,
            explanation=evidence_exp
        ))

        # 3. Multi-experiment Validation
        exp_count = len(confirmed_hypo.experiments) if confirmed_hypo else 0
        multi_exp_achieved = (exp_count >= 2)
        multi_exp_exp = f"{exp_count} experiment(s) directly associated with confirmed hypothesis."
        if multi_exp_achieved:
            basis.append(f"Validated across {exp_count} distinct empirical experiments")
        factors.append(ConfidenceFactor(
            name="Multi-Experiment Validation",
            weight=0.15,
            achieved=multi_exp_achieved,
            explanation=multi_exp_exp
        ))

        # 4. Elimination of Competing Hypotheses
        elimination_achieved = (len(rejected_hypotheses) >= 1)
        elim_exp = f"{len(rejected_hypotheses)} competing hypothesis/hypotheses empirically falsified."
        if elimination_achieved:
            basis.append(f"Systematically eliminated {len(rejected_hypotheses)} competing hypothesis/hypotheses via experiment")
        factors.append(ConfidenceFactor(
            name="Hypothesis Elimination",
            weight=0.15,
            achieved=elimination_achieved,
            explanation=elim_exp
        ))

        # 5. Fix Verification & Statistical Binomial Bounds
        stat_interval = None
        fix_achieved = False
        fix_exp = "Fix verification not yet performed or failed."
        if verification_runs > 0 and verification_failures == 0:
            fix_achieved = True
            stat_interval = cls.calculate_binomial_bounds(verification_runs, 0, confidence=0.95)
            fix_exp = f"Fix verified: 0 failures across {verification_runs} runs."
            if stat_interval:
                basis.append(
                    f"Statistical verification: 0/{verification_runs} failures. "
                    f"At 95% confidence, true failure rate p <= {stat_interval.upper_bound*100:.2f}% ({stat_interval.method})"
                )
            else:
                basis.append(f"Fix verified: 0 failures observed in {verification_runs} execution trial(s)")
        elif verification_runs > 0:
            stat_interval = cls.calculate_binomial_bounds(verification_runs, verification_failures, confidence=0.95)
            fix_exp = f"Fix failed: {verification_failures}/{verification_runs} failures observed."
            if stat_interval:
                basis.append(f"Verification failure: {stat_interval.description}")

        factors.append(ConfidenceFactor(
            name="Fix Verification",
            weight=0.20,
            achieved=fix_achieved,
            explanation=fix_exp
        ))

        # 6. Regression Testing
        reg_exp = "Regression suite passed without regressions." if regression_passed else "Regression suite not run or incomplete."
        if regression_passed:
            basis.append("Full regression test suite passed cleanly")
        factors.append(ConfidenceFactor(
            name="Regression Safety",
            weight=0.10,
            achieved=regression_passed,
            explanation=reg_exp
        ))

        # Compute raw empirical score from achieved factors
        raw_score = sum(f.weight for f in factors if f.achieved)

        # Penalties:
        if confirmed_hypo and confirmed_hypo.contradicting_evidence:
            raw_score -= 0.35
            basis.append(f"PENALTY: {len(confirmed_hypo.contradicting_evidence)} unrefuted contradictory evidence item(s) remain")

        if len(active_hypotheses) > 1 and not confirmed_hypo:
            raw_score -= 0.15
            basis.append(f"PENALTY: {len(active_hypotheses)} plausible hypotheses remain untested")

        score = max(0.05, min(0.99, round(raw_score, 3)))

        # Determine categorical level
        if score >= 0.85:
            level = ConfidenceLevel.HIGH
        elif score >= 0.60:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW

        if not basis:
            basis.append("Preliminary baseline; insufficient experiments performed.")

        return ConfidenceAssessment(
            score=score,
            level=level,
            statistical_interval=stat_interval,
            factors=factors,
            basis=basis
        )
