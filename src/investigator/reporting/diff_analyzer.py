"""Diff Analyzer for AI Software Investigator.

Implements diff-based reasoning, evaluates minimal fix blast radius,
and prevents unintended side effects.
"""

from typing import Any, Dict, List, Optional
import difflib
import re


class FileDiffSummary:
    """Summary of modifications to an individual file."""

    def __init__(
        self,
        filepath: str,
        lines_added: int,
        lines_removed: int,
        rationale: str,
        diff_text: str,
    ):
        self.filepath = filepath
        self.lines_added = lines_added
        self.lines_removed = lines_removed
        self.rationale = rationale
        self.diff_text = diff_text

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filepath": self.filepath,
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
            "rationale": self.rationale,
            "diff_snippet": self.diff_text[:500],
        }


class DiffAnalysisResult:
    """Holistic analysis of changes between Before and After."""

    def __init__(
        self,
        files: List[FileDiffSummary],
        is_minimal_fix: bool,
        blast_radius: str,
        rationales: Dict[str, str],
        side_effect_risks: List[str],
    ):
        self.files = files
        self.is_minimal_fix = is_minimal_fix
        self.blast_radius = blast_radius  # LOW, MEDIUM, HIGH
        self.rationales = rationales
        self.side_effect_risks = side_effect_risks

    @property
    def total_added(self) -> int:
        return sum(f.lines_added for f in self.files)

    @property
    def total_removed(self) -> int:
        return sum(f.lines_removed for f in self.files)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "files_changed_count": len(self.files),
            "total_lines_added": self.total_added,
            "total_lines_removed": self.total_removed,
            "is_minimal_fix": self.is_minimal_fix,
            "blast_radius": self.blast_radius,
            "files": [f.to_dict() for f in self.files],
            "side_effect_risks": self.side_effect_risks,
        }


class DiffAnalyzer:
    """Analyzes source changes to enforce minimal fix principles."""

    @classmethod
    def compare_texts(
        cls,
        filepath: str,
        before_text: str,
        after_text: str,
        rationale: str = ""
    ) -> FileDiffSummary:
        """Generate unified diff and compute line additions/deletions."""
        before_lines = before_text.splitlines(keepends=True)
        after_lines = after_text.splitlines(keepends=True)

        diff = list(difflib.unified_diff(
            before_lines,
            after_lines,
            fromfile=f"a/{filepath}",
            tofile=f"b/{filepath}",
            n=3
        ))

        added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))
        diff_text = "".join(diff)

        return FileDiffSummary(
            filepath=filepath,
            lines_added=added,
            lines_removed=removed,
            rationale=rationale or f"Surgical modification to {filepath}",
            diff_text=diff_text
        )

    @classmethod
    def evaluate_changes(
        cls,
        file_diffs: List[FileDiffSummary],
        architecture_justification: Optional[str] = None
    ) -> DiffAnalysisResult:
        """Evaluate whether changes adhere to Minimal Fix standards."""
        total_delta = sum(f.lines_added + f.lines_removed for f in file_diffs)
        file_count = len(file_diffs)

        risks = []
        if file_count > 3:
            risks.append(f"More than 3 files modified ({file_count} files). Potential ripple effects.")
        if total_delta > 50 and not architecture_justification:
            risks.append(f"Large diff detected ({total_delta} lines modified) without architectural justification.")

        # Blast radius evaluation
        if file_count <= 2 and total_delta <= 25:
            blast_radius = "LOW"
            is_minimal = True
        elif file_count <= 4 and total_delta <= 80:
            blast_radius = "MEDIUM"
            is_minimal = True
        else:
            blast_radius = "HIGH"
            is_minimal = bool(architecture_justification)

        rationales = {f.filepath: f.rationale for f in file_diffs}

        return DiffAnalysisResult(
            files=file_diffs,
            is_minimal_fix=is_minimal,
            blast_radius=blast_radius,
            rationales=rationales,
            side_effect_risks=risks
        )
