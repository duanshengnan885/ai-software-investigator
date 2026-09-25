"""Unit tests for Sandbox and SafetyGuard."""

from pathlib import Path
import tempfile
import pytest

from investigator.sandbox.directory import DirectorySandbox
from investigator.sandbox.safety import SafetyGuard, SafetyViolation


def test_directory_sandbox_snapshots_and_rollback():
    with tempfile.TemporaryDirectory() as src_dir:
        src_path = Path(src_dir)
        (src_path / "app.py").write_text("v1 = True\n", encoding="utf-8")

        sandbox = DirectorySandbox(source_dir=src_path)
        sandbox_path = sandbox.enter()

        assert (sandbox_path / "app.py").exists()
        assert sandbox.read_file("app.py") == "v1 = True\n"

        # Snapshot initial state
        snap_id = sandbox.snapshot("initial")

        # Mutate inside sandbox
        sandbox.write_file("app.py", "v2_mutated = True\n")
        assert sandbox.read_file("app.py") == "v2_mutated = True\n"

        # Rollback
        sandbox.rollback(snap_id)
        assert sandbox.read_file("app.py") == "v1 = True\n"

        sandbox.exit(clean=True)


def test_safety_guard_blocks_destructive_commands():
    guard = SafetyGuard()

    # Blocked catastrophic commands
    with pytest.raises(SafetyViolation, match="Prohibited catastrophic command"):
        guard.authorize_or_raise("rm -rf /")

    with pytest.raises(SafetyViolation, match="Prohibited catastrophic command"):
        guard.authorize_or_raise("del /f /s /q C:\\Windows")

    # Blocked sensitive credentials
    with pytest.raises(SafetyViolation, match="Access to sensitive host target"):
        guard.authorize_or_raise("cat .env")

    # Allowed safe command
    assert guard.check_command("pytest tests/test_app.py")[0] is True
