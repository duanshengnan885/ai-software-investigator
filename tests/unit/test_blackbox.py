"""Unit tests for Black-box boundary search and mutation engine."""

import pytest
from investigator.experiments.blackbox import BlackboxInvestigator


def test_binary_search_boundary_discovery():
    # Simulate a program that passes when input length <= 64, and crashes when length >= 65
    def mock_runner(cmd: str, stdin_str: str = None):
        # Extract input payload length
        parts = cmd.split()
        payload = parts[-1] if len(parts) > 1 else ""
        length = len(payload)
        if length <= 64:
            return 0, "OK", ""
        else:
            return 139, "", "SIGSEGV: BufferOverflow"

    investigator = BlackboxInvestigator(runner_func=mock_runner)
    result = investigator.binary_search_length_boundary(
        command_template="mock_binary {input}",
        min_len=1,
        max_len=256,
        char="X",
        expected_pass_code=0,
    )

    assert result is not None
    assert result.lower_passing_bound == 64
    assert result.upper_failing_bound == 65
    assert len(result.search_history) > 0
    assert "Exact failure boundary isolated at input length: 64 (OK) -> 65 (CRASH/FAIL)" in result.trigger_description


def test_fuzz_input_permutations():
    def mock_runner(cmd: str, stdin_str: str = None):
        return 0, "OUTPUT", ""

    investigator = BlackboxInvestigator(runner_func=mock_runner)
    mutations = investigator.fuzz_input_permutations("mock_cli {input}")
    assert len(mutations) >= 10
    names = [m["mutation"] for m in mutations]
    assert "control_chars" in names
    assert "format_string" in names
    assert "unicode_emoji" in names
