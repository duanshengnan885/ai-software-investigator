"""Git Worktree Sandbox implementation for AI Software Investigator.

Leverages git worktrees to provide zero-copy branch isolation for repository projects.
"""

from pathlib import Path
from typing import Optional
import shutil
import subprocess
import time

from investigator.sandbox.base import BaseSandbox


class GitWorktreeSandbox(BaseSandbox):
    """Isolates changes in a detached Git worktree."""

    def __init__(self, repo_dir: Path, branch_name: Optional[str] = None):
        self.repo_dir = Path(repo_dir).resolve()
        self.branch_name = branch_name or f"investigation/case_{int(time.time())}"
        self.worktree_dir: Optional[Path] = None
        self._is_git = (self.repo_dir / ".git").exists()

    def is_git_repo(self) -> bool:
        """Check if project is a valid Git repository."""
        return self._is_git

    def enter(self) -> Path:
        """Create and checkout the isolated git worktree."""
        if not self._is_git:
            raise RuntimeError(f"Directory {self.repo_dir} is not a git repository.")

        self.worktree_dir = self.repo_dir.parent / f"wt_{self.repo_dir.name}_{int(time.time())}"
        cmd = f"git worktree add -b {self.branch_name} \"{self.worktree_dir}\""
        res = subprocess.run(cmd, cwd=str(self.repo_dir), shell=True, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Failed to create git worktree: {res.stderr}")

        return self.worktree_dir

    def get_path(self) -> Path:
        if not self.worktree_dir:
            raise RuntimeError("Worktree sandbox has not been entered.")
        return self.worktree_dir

    def snapshot(self, label: str) -> str:
        """Commit current worktree state as a lightweight commit."""
        if not self.worktree_dir:
            raise RuntimeError("Worktree not active.")
        subprocess.run("git add -A", cwd=str(self.worktree_dir), shell=True, capture_output=True)
        subprocess.run(
            f"git commit -m \"Snapshot: {label}\" --allow-empty",
            cwd=str(self.worktree_dir),
            shell=True,
            capture_output=True
        )
        res = subprocess.run("git rev-parse HEAD", cwd=str(self.worktree_dir), shell=True, capture_output=True, text=True)
        return res.stdout.strip()

    def rollback(self, snapshot_id: str) -> None:
        """Revert worktree to commit snapshot."""
        if not self.worktree_dir:
            raise RuntimeError("Worktree not active.")
        subprocess.run(f"git reset --hard {snapshot_id}", cwd=str(self.worktree_dir), shell=True, capture_output=True)
        subprocess.run("git clean -fd", cwd=str(self.worktree_dir), shell=True, capture_output=True)

    def exit(self, clean: bool = True) -> None:
        """Remove worktree and clean branch."""
        if self.worktree_dir and self.worktree_dir.exists():
            subprocess.run(
                f"git worktree remove --force \"{self.worktree_dir}\"",
                cwd=str(self.repo_dir),
                shell=True,
                capture_output=True
            )
            shutil.rmtree(self.worktree_dir, ignore_errors=True)
            self.worktree_dir = None
