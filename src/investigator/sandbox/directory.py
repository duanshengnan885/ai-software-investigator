"""Directory Sandbox implementation for AI Software Investigator.

Provides filesystem isolation via isolated workspaces, snapshotting, and rollback.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set
import shutil
import tempfile
import time

from investigator.sandbox.base import BaseSandbox


class DirectorySandbox(BaseSandbox):
    """Isolates investigation and patching in a segregated directory."""

    IGNORE_DIRS: Set[str] = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        "venv",
        ".venv",
        "dist",
        "build",
        ".investigation",
    }

    def __init__(self, source_dir: Path, target_dir: Optional[Path] = None):
        self.source_dir = Path(source_dir).resolve()
        self._custom_target = Path(target_dir).resolve() if target_dir else None
        self._temp_dir: Optional[tempfile.TemporaryDirectory] = None
        self.active_path: Optional[Path] = None
        self._snapshots: Dict[str, Path] = {}

    def _copy_filtered(self, src: Path, dst: Path) -> None:
        """Copy directory tree while skipping heavy or cache directories."""
        dst.mkdir(parents=True, exist_ok=True)
        for item in src.iterdir():
            if item.name in self.IGNORE_DIRS:
                continue
            dest_item = dst / item.name
            if item.is_dir():
                self._copy_filtered(item, dest_item)
            else:
                shutil.copy2(item, dest_item)

    def enter(self) -> Path:
        """Create sandbox copy and set active path."""
        if self._custom_target:
            self.active_path = self._custom_target
            if not self.active_path.exists():
                self._copy_filtered(self.source_dir, self.active_path)
        else:
            self._temp_dir = tempfile.TemporaryDirectory(prefix="investigator_sandbox_")
            self.active_path = Path(self._temp_dir.name)
            self._copy_filtered(self.source_dir, self.active_path)

        return self.active_path

    def get_path(self) -> Path:
        """Return active sandbox path."""
        if not self.active_path:
            raise RuntimeError("Sandbox has not been entered.")
        return self.active_path

    def snapshot(self, label: str) -> str:
        """Snapshot current sandbox state for rollback."""
        if not self.active_path:
            raise RuntimeError("Sandbox not active.")

        snap_id = f"snap_{int(time.time())}_{label}"
        snap_dir = Path(tempfile.gettempdir()) / f"investigator_snap_{snap_id}"
        self._copy_filtered(self.active_path, snap_dir)
        self._snapshots[snap_id] = snap_dir
        return snap_id

    def rollback(self, snapshot_id: str) -> None:
        """Roll back sandbox filesystem to specified snapshot."""
        if not self.active_path:
            raise RuntimeError("Sandbox not active.")
        if snapshot_id not in self._snapshots:
            raise KeyError(f"Snapshot '{snapshot_id}' not found.")

        snap_dir = self._snapshots[snapshot_id]
        # Clear sandbox contents
        for item in self.active_path.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                try:
                    item.unlink()
                except Exception:
                    pass

        # Restore from snapshot
        self._copy_filtered(snap_dir, self.active_path)

    def write_file(self, rel_path: str, content: str) -> Path:
        """Safely write/modify a file inside sandbox."""
        if not self.active_path:
            raise RuntimeError("Sandbox not active.")
        target = self.active_path / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def read_file(self, rel_path: str) -> str:
        """Read a file from within sandbox."""
        if not self.active_path:
            raise RuntimeError("Sandbox not active.")
        target = self.active_path / rel_path
        return target.read_text(encoding="utf-8")

    def exit(self, clean: bool = True) -> None:
        """Clean up snapshots and temporary directory."""
        for snap_dir in self._snapshots.values():
            shutil.rmtree(snap_dir, ignore_errors=True)
        self._snapshots.clear()

        if clean and self._temp_dir:
            self._temp_dir.cleanup()
            self._temp_dir = None
        self.active_path = None
