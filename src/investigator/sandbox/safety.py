"""Safety Guardrails and Human Approval Manager for AI Software Investigator.

Intercepts destructive operations, protects host environments, and enforces
human authorization for high-risk actions.
"""

from typing import List, Optional, Tuple
import re


class SafetyViolation(Exception):
    """Raised when an unsafe command is blocked by the safety guardrail."""
    pass


class SafetyGuard:
    """Detects dangerous patterns and manages human approval requirements."""

    DANGEROUS_COMMAND_PATTERNS = [
        r"rm\s+-rf\s+[/~]",
        r"del(\s+/[a-zA-Z]+)*\s+[a-zA-Z]:\\",
        r"rd(\s+/[a-zA-Z]+)*\s+[a-zA-Z]:\\",
        r"format\s+[a-zA-Z]:",
        r"mkfs\.",
        r":\(\)\s*\{\s*:\|:&\s*\};:",  # Fork bomb
        r">\s*/dev/sd[a-z]",
        r"dd\s+if=.*of=/dev/",
        r"chmod\s+-R\s+777\s+/",
        r"curl.*\|\s*(bash|sh|powershell)",
        r"wget.*\|\s*(bash|sh|powershell)",
    ]

    SENSITIVE_TARGET_PATTERNS = [
        r"\.env($|\s)",
        r"id_rsa($|\s)",
        r"\.ssh/",
        r"\.aws/",
        r"\.config/gcloud",
        r"/etc/shadow",
        r"/etc/passwd",
        r"C:\\Windows\\System32",
    ]

    DESTRUCTIVE_ACTIONS = [
        "DROP DATABASE",
        "TRUNCATE TABLE",
        "DELETE FROM",
        "rmdir /s /q",
        "Remove-Item -Recurse -Force",
    ]

    def __init__(self, require_approval_callback: Optional[callable] = None):
        """require_approval_callback: function(action_desc, risk_reason) -> bool"""
        self.require_approval_callback = require_approval_callback

    def check_command(self, command: str) -> Tuple[bool, str]:
        """Check if command is dangerous or requires confirmation.

        Returns (is_allowed, reason).
        """
        lower_cmd = command.lower()

        # Check for explicitly prohibited catastrophic commands
        for pat in self.DANGEROUS_COMMAND_PATTERNS:
            if re.search(pat, command, re.IGNORECASE):
                return False, f"Prohibited catastrophic command pattern detected: {pat}"

        # Check for credential or sensitive path exfiltration
        for pat in self.SENSITIVE_TARGET_PATTERNS:
            if re.search(pat, command, re.IGNORECASE):
                return False, f"Access to sensitive host target detected: {pat}"

        # Check for destructive database or bulk deletion
        for action in self.DESTRUCTIVE_ACTIONS:
            if action.lower() in lower_cmd:
                if self.require_approval_callback:
                    approved = self.require_approval_callback(
                        action_desc=command,
                        risk_reason=f"Potentially destructive action detected: {action}"
                    )
                    if not approved:
                        return False, "Operation rejected by user."
                    return True, "Approved by user."
                else:
                    return False, f"Destructive command requires human approval: {action}"

        return True, "Safe"

    def authorize_or_raise(self, command: str) -> None:
        """Validate command safety or raise SafetyViolation."""
        allowed, reason = self.check_command(command)
        if not allowed:
            raise SafetyViolation(f"Safety Violation: {reason} (Command: '{command}')")
