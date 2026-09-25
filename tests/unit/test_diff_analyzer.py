"""Unit tests for DiffAnalyzer and diff-based reasoning."""

import pytest
from investigator.reporting.diff_analyzer import DiffAnalyzer, DiffAnalysisResult, FileDiffSummary


def test_diff_analyzer_minimal_fix():
    before = "def add(a, b):\n    return a - b\n"
    after = "def add(a, b):\n    return a + b\n"

    summary = DiffAnalyzer.compare_texts(
        filepath="math_utils.py",
        before_text=before,
        after_text=after,
        rationale="Fix sign error in addition function"
    )

    assert summary.lines_added == 1
    assert summary.lines_removed == 1
    assert "+    return a + b" in summary.diff_text

    result = DiffAnalyzer.evaluate_changes([summary])
    assert result.is_minimal_fix is True
    assert result.blast_radius == "LOW"
    assert result.total_added == 1
    assert result.total_removed == 1
    assert len(result.side_effect_risks) == 0


def test_diff_analyzer_large_blast_radius():
    # Simulate a large sprawling refactor across many files
    summaries = []
    for i in range(5):
        s = FileDiffSummary(
            filepath=f"module_{i}.py",
            lines_added=25,
            lines_removed=25,
            rationale="Broad refactoring",
            diff_text="",
        )
        summaries.append(s)

    result = DiffAnalyzer.evaluate_changes(summaries)
    assert result.blast_radius == "HIGH"
    assert len(result.side_effect_risks) > 0
