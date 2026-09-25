"""Protocol definitions, enums, and constants for AI Software Investigator.

Defines lifecycle stages, hypothesis statuses, evidence claim types,
investigation verdicts, and safety classifications.
"""

from enum import Enum


class InvestigationStage(str, Enum):
    """Investigation lifecycle stages."""
    INTAKE = "intake"
    ENVIRONMENT_DISCOVERY = "environment_discovery"
    EVIDENCE_COLLECTION = "evidence_collection"
    REPRODUCTION = "reproduction"
    HYPOTHESIS_GENERATION = "hypothesis_generation"
    EXPERIMENT_PLANNING = "experiment_planning"
    EXPERIMENT_EXECUTION = "experiment_execution"
    EVIDENCE_ANALYSIS = "evidence_analysis"
    HYPOTHESIS_ELIMINATION = "hypothesis_elimination"
    ROOT_CAUSE_IDENTIFICATION = "root_cause_identification"
    MINIMAL_FIX = "minimal_fix"
    REGRESSION_TESTING = "regression_testing"
    INDEPENDENT_VERIFICATION = "independent_verification"
    REPORT_GENERATION = "report_generation"
    CLOSED = "closed"


class InvestigationVerdict(str, Enum):
    """Final investigation outcome/termination status."""
    SUCCESS = "SUCCESS"          # Root Cause identified + Fix applied + Verification passed
    PARTIAL = "PARTIAL"          # Strong evidence exists but complete verification impossible
    BLOCKED = "BLOCKED"          # Missing environment / dependency / repro / permissions
    UNKNOWN = "UNKNOWN"          # Available evidence is insufficient after exhaustive search


class HypothesisStatus(str, Enum):
    """Hypothesis lifecycle statuses."""
    UNTESTED = "UNTESTED"        # Newly generated, no experimental test performed yet
    PLAUSIBLE = "PLAUSIBLE"      # Consistent with initial observations, awaiting direct test
    SUPPORTED = "SUPPORTED"      # Evidence matches predictions from experiments
    WEAKENED = "WEAKENED"        # Some evidence contradicts predictions or weak correlation
    REJECTED = "REJECTED"        # Controlled experiment definitively disproved prediction
    CONFIRMED = "CONFIRMED"      # Irrefutably validated as root cause with causal proof


class ClaimStatus(str, Enum):
    """Epistemological status of an evidence claim. Prohibits hallucination."""
    OBSERVED = "Observed"        # Directly witnessed runtime output, exit code, log line
    INFERRED = "Inferred"        # Logically deduced from observed evidence
    HYPOTHESIZED = "Hypothesized"# Proposed explanation awaiting validation
    VERIFIED = "Verified"        # Proven via controlled independent test / fix validation
    UNKNOWN = "Unknown"          # Unverified or ambiguous data


class Reliability(str, Enum):
    """Evidence reliability rating."""
    HIGH = "HIGH"                # Directly measured, reproducible, sandbox validated
    MEDIUM = "MEDIUM"            # Inferred from indirect logs or single-run observation
    LOW = "LOW"                  # User hearsay or unconfirmed report


class ExperimentOutcome(str, Enum):
    """Outcome of an empirical experiment."""
    SUPPORTED = "SUPPORTED"      # Observations matched experiment prediction
    WEAKENED = "WEAKENED"        # Observations weakly contradict prediction
    REJECTED = "REJECTED"        # Observations definitively contradict prediction
    INCONCLUSIVE = "INCONCLUSIVE"# Experiment timed out, crashed unexpectedly, or gave ambiguous signal


class ConfidenceLevel(str, Enum):
    """Categorical confidence level derived from mathematical evidence score."""
    HIGH = "HIGH"                # >= 0.85
    MEDIUM = "MEDIUM"            # 0.60 .. 0.84
    LOW = "LOW"                  # < 0.60


class CaseCategory(str, Enum):
    """Category of investigation."""
    BUG = "bug"                  # Crash, exception, logic bug, wrong output, hang
    PERFORMANCE = "performance"  # High CPU/RAM, memory leak, slow latency
    RELIABILITY = "reliability"  # Intermittent failure, race condition, timeout
    BEHAVIORAL = "behavioral"    # Reverse engineering, explaining unexpected behavior
    BLACKBOX = "blackbox"        # Binary or closed box without source code
