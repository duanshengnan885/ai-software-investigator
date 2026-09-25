"""Unit tests for multi-platform reasoning providers and DeepSeek Harness."""

import json
from pathlib import Path
from investigator.agent.llm import (
    DeepSeekReasoningProvider,
    DoubaoReasoningProvider,
    LLMReasoningProvider,
    HeuristicForensicDriver,
)
from investigator.harness.deepseek import (
    DeepSeekHarness,
    HarnessResult,
    HarnessTaskSpec,
)


def test_deepseek_reasoning_provider_configuration():
    """Verify DeepSeek provider defaults and endpoint settings."""
    provider = DeepSeekReasoningProvider(api_key="test_deepseek_key")
    assert provider.model == "deepseek-reasoner"
    assert provider.base_url == "https://api.deepseek.com/v1"
    assert provider.api_key == "test_deepseek_key"


def test_doubao_reasoning_provider_configuration():
    """Verify Doubao / Volcano Engine provider defaults."""
    provider = DoubaoReasoningProvider(api_key="test_doubao_key")
    assert provider.model == "doubao-1.5-pro-32k"
    assert "ark.cn-beijing.volces.com" in provider.base_url
    assert provider.api_key == "test_doubao_key"


def test_harness_task_spec_serialization(tmp_path: Path):
    """Verify task spec creation and dictionary loading."""
    spec_dict = {
        "instance_id": "DEEPSEEK-001",
        "problem": "Crash under high concurrency in payment worker",
        "repo_dir": str(tmp_path),
        "test_cmd": "pytest -k payment",
        "category": "reliability",
        "max_steps": 10,
    }
    spec = HarnessTaskSpec.from_dict(spec_dict)
    assert spec.instance_id == "DEEPSEEK-001"
    assert "payment worker" in spec.problem_statement
    assert spec.repo_dir == tmp_path.resolve()
    assert spec.test_command == "pytest -k payment"
    assert spec.category == "reliability"
    assert spec.max_steps == 10


def test_deepseek_harness_execution(tmp_path: Path):
    """Test running an autonomous investigation through the DeepSeek Harness."""
    # Create a dummy problem project
    test_file = tmp_path / "calc.py"
    test_file.write_text("def div(a, b): return a / b\n", encoding="utf-8")

    spec = HarnessTaskSpec(
        instance_id="TEST-HARNESS-001",
        problem_statement="Calculation divides by zero when input b is 0",
        repo_dir=tmp_path,
        max_steps=3,
    )

    harness = DeepSeekHarness(provider=HeuristicForensicDriver())
    result: HarnessResult = harness.run_task(spec)

    assert result.instance_id == "TEST-HARNESS-001"
    assert result.verdict in ["SUCCESS", "PARTIAL", "BLOCKED", "UNKNOWN"]
    assert result.evidence_count >= 1
    assert result.duration_seconds >= 0.0

    # Test dictionary export
    res_dict = result.to_dict()
    assert res_dict["instance_id"] == "TEST-HARNESS-001"
    assert "evidence_count" in res_dict
    assert "duration_seconds" in res_dict
