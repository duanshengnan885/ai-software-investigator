"""Abstract base sandbox interface for AI Software Investigator."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class BaseSandbox(ABC):
    """Abstract sandbox environment providing isolation and rollback."""

    @abstractmethod
    def enter(self) -> Path:
        """Activate sandbox and return working directory path."""
        pass

    @abstractmethod
    def exit(self, clean: bool = True) -> None:
        """Exit sandbox and optionally clean up temporary resources."""
        pass

    @abstractmethod
    def snapshot(self, label: str) -> str:
        """Take a snapshot of current state for rollback capability."""
        pass

    @abstractmethod
    def rollback(self, snapshot_id: str) -> None:
        """Revert sandbox files to a previously saved snapshot."""
        pass

    @abstractmethod
    def get_path(self) -> Path:
        """Return the current active sandbox directory."""
        pass
