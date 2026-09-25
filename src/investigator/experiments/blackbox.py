"""Black-box Investigation Engine for AI Software Investigator.

Enables automated investigation of closed-source, compiled, or unknown binaries
using binary search boundary discovery, input mutation, differential testing,
and safe argument construction without shell injection.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import shlex
import sys
from pathlib import Path

from investigator.sandbox.process import ProcessSandbox


class BoundaryDiscoveryResult:
    """Findings from binary search boundary discovery."""

    def __init__(
        self,
        parameter_name: str,
        lower_passing_bound: int,
        upper_failing_bound: int,
        search_history: List[Dict[str, Any]],
        trigger_description: str,
    ):
        self.parameter_name = parameter_name
        self.lower_passing_bound = lower_passing_bound
        self.upper_failing_bound = upper_failing_bound
        self.search_history = search_history
        self.trigger_description = trigger_description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parameter": self.parameter_name,
            "passing_bound": self.lower_passing_bound,
            "failing_bound": self.upper_failing_bound,
            "steps_count": len(self.search_history),
            "description": self.trigger_description,
            "history": self.search_history,
        }


class BlackboxInvestigator:
    """Automates empirical black-box testing and boundary condition search."""

    def __init__(
        self,
        runner_func: Optional[Callable[[Union[str, List[str]], Optional[str]], Tuple[int, str, str]]] = None,
        working_dir: Optional[Path] = None,
    ):
        """runner_func: takes (command_or_argv, stdin_str), returns (exit_code, stdout, stderr)."""
        self.working_dir = working_dir or Path.cwd()
        self.sandbox = ProcessSandbox(working_dir=self.working_dir, sanitize_env=True)
        self.runner_func = runner_func or self._default_run

    def _default_run(self, command: Union[str, List[str]], stdin_str: Optional[str] = None) -> Tuple[int, str, str]:
        """Default sandbox runner."""
        code, out, err, _, _ = self.sandbox.run(command=command, stdin_input=stdin_str, timeout_sec=10.0)
        return code, out, err

    def _build_command(
        self,
        template: Union[str, List[str]],
        payload: str,
        use_stdin: bool
    ) -> Tuple[Union[str, List[str]], Optional[str]]:
        """Construct safe command without shell injection risks."""
        if use_stdin:
            return template, payload

        if isinstance(template, list):
            # Substitute directly into list element without shell interpretation
            cmd_args = [arg.replace("{input}", payload) for arg in template]
            return cmd_args, None
        else:
            # String template: use shlex.quote to prevent command injection
            escaped_payload = shlex.quote(payload)
            # If the template explicitly has {input}, replace with quoted payload
            if "{input}" in template:
                cmd_str = template.replace("{input}", escaped_payload)
            else:
                cmd_str = f"{template} {escaped_payload}"
            return cmd_str, None

    def binary_search_length_boundary(
        self,
        command_template: Union[str, List[str]],
        min_len: int = 1,
        max_len: int = 2048,
        use_stdin: bool = False,
        char: str = "A",
        expected_pass_code: int = 0,
    ) -> Optional[BoundaryDiscoveryResult]:
        """Binary search to pinpoint exact input length where behavior transitions from pass to crash."""
        history: List[Dict[str, Any]] = []

        # Check bounds first
        low_input = char * min_len
        cmd_low, stdin_low = self._build_command(command_template, low_input, use_stdin)
        code_low, _, _ = self.runner_func(cmd_low, stdin_low)

        high_input = char * max_len
        cmd_high, stdin_high = self._build_command(command_template, high_input, use_stdin)
        code_high, _, _ = self.runner_func(cmd_high, stdin_high)

        history.append({"length": min_len, "exit_code": code_low, "status": "pass" if code_low == expected_pass_code else "fail"})
        history.append({"length": max_len, "exit_code": code_high, "status": "pass" if code_high == expected_pass_code else "fail"})

        if code_low != expected_pass_code:
            return None
        if code_high == expected_pass_code:
            return None

        left = min_len
        right = max_len

        while left + 1 < right:
            mid = (left + right) // 2
            mid_input = char * mid
            cmd_mid, stdin_mid = self._build_command(command_template, mid_input, use_stdin)
            code_mid, _, err = self.runner_func(cmd_mid, stdin_mid)

            is_pass = (code_mid == expected_pass_code)
            history.append({
                "length": mid,
                "exit_code": code_mid,
                "status": "pass" if is_pass else "fail",
                "stderr_snippet": err.strip()[:80] if err else ""
            })

            if is_pass:
                left = mid
            else:
                right = mid

        description = (
            f"Exact failure boundary isolated at input length: {left} (OK) -> {right} (CRASH/FAIL). "
            f"Input of length {left} returns exit code {expected_pass_code}, "
            f"whereas length {right} triggers failure with code {code_high}."
        )

        return BoundaryDiscoveryResult(
            parameter_name="input_length",
            lower_passing_bound=left,
            upper_failing_bound=right,
            search_history=history,
            trigger_description=description
        )

    def fuzz_input_permutations(
        self,
        command_template: Union[str, List[str]],
        use_stdin: bool = False,
    ) -> List[Dict[str, Any]]:
        """Test a suite of canonical input mutations safely with proper escaping."""
        test_payloads = [
            ("empty_string", ""),
            ("whitespace_only", "   \t   "),
            ("control_chars", "\r\n\t"),
            ("unicode_emoji", "测试数据 🚀🔥"),
            ("format_string", "%s%s%s%x"),
            ("path_traversal", "../../etc/passwd"),
            ("sql_meta", "' OR '1'='1"),
            ("long_numeric", "99999999999999999999999999999999"),
            ("negative_number", "-1"),
            ("json_malformed", "{bad_json: 123"),
        ]

        results = []
        for name, payload in test_payloads:
            cmd, stdin = self._build_command(command_template, payload, use_stdin)
            code, out, err = self.runner_func(cmd, stdin)
            results.append({
                "mutation": name,
                "payload_repr": repr(payload)[:40],
                "exit_code": code,
                "stdout_snippet": out.strip()[:100],
                "stderr_snippet": err.strip()[:100],
                "crashed": code not in (0, 1),
            })
        return results
