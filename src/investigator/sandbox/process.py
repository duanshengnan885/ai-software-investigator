"""Process Sandbox implementation for AI Software Investigator.

Provides isolated process execution with environment sanitization, recursive
process tree termination, and safe argv argument handling without shell injection.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import os
import shlex
import signal
import subprocess
import sys
import time

try:
    import psutil
except ImportError:
    psutil = None


class ProcessSandbox:
    """Runs commands with sanitized environment variables, safe arguments, and process tree termination."""

    SENSITIVE_ENV_KEYS = {
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "GITHUB_TOKEN",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "SLACK_BOT_TOKEN",
        "DATABASE_URL",
        "PRIVATE_KEY",
    }

    def __init__(self, working_dir: Path, sanitize_env: bool = True):
        self.working_dir = Path(working_dir).resolve()
        self.sanitize_env = sanitize_env

    def get_clean_env(self, custom_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Construct a sanitized environment dict."""
        env = os.environ.copy()
        if self.sanitize_env:
            for key in self.SENSITIVE_ENV_KEYS:
                env.pop(key, None)

        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        if custom_env:
            env.update(custom_env)
        return env

    def kill_process_tree(self, proc: subprocess.Popen) -> None:
        """Kill the entire process tree recursively to prevent orphan processes."""
        if not proc or proc.poll() is not None:
            return

        pid = proc.pid
        # Method 1: psutil (cross-platform, cleanest)
        if psutil:
            try:
                parent = psutil.Process(pid)
                children = parent.children(recursive=True)
                for child in children:
                    try:
                        child.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                parent.kill()
                return
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Method 2: Platform-specific fallbacks
        if sys.platform == "win32":
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    capture_output=True,
                    timeout=5
                )
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        else:
            try:
                os.killpg(os.getpgid(pid), signal.SIGKILL)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

    def run(
        self,
        command: Union[str, List[str]],
        timeout_sec: float = 30.0,
        stdin_input: Optional[str] = None,
        custom_env: Optional[Dict[str, str]] = None,
        use_shell: Optional[bool] = None,
    ) -> Tuple[int, str, str, bool, float]:
        """Execute command inside sandbox directory with clean environment and process tree control.

        Returns (exit_code, stdout, stderr, timed_out, duration_ms).
        """
        env = self.get_clean_env(custom_env)
        timed_out = False
        start_time = time.perf_counter()

        # Decide whether to use shell
        if isinstance(command, list):
            cmd_args = command
            shell_flag = False
        else:
            # If command contains shell pipes or redirection or is on Windows, use shell
            has_shell_operators = any(op in command for op in ["|", "&&", "||", ">", "<", ";"])
            if use_shell is not None:
                shell_flag = use_shell
                cmd_args = command
            elif sys.platform == "win32":
                shell_flag = True
                cmd_args = command
            elif has_shell_operators:
                shell_flag = True
                cmd_args = command
            else:
                shell_flag = False
                try:
                    cmd_args = shlex.split(command, posix=True)
                except ValueError:
                    shell_flag = True
                    cmd_args = command

        # Process group flags for POSIX
        kwargs = {}
        if not sys.platform == "win32" and not shell_flag:
            kwargs["preexec_fn"] = os.setsid

        try:
            proc = subprocess.Popen(
                cmd_args,
                cwd=str(self.working_dir),
                env=env,
                shell=shell_flag,
                stdin=subprocess.PIPE if stdin_input is not None else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                **kwargs
            )

            stdout, stderr = proc.communicate(input=stdin_input, timeout=timeout_sec)
            exit_code = proc.returncode

        except subprocess.TimeoutExpired:
            timed_out = True
            exit_code = -1
            self.kill_process_tree(proc)
            try:
                stdout, stderr = proc.communicate()
            except Exception:
                stdout, stderr = "", "Process tree terminated due to timeout expiration."

        except Exception as e:
            exit_code = -1
            stdout = ""
            stderr = f"Process execution failed: {str(e)}"

        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        return exit_code, stdout, stderr, timed_out, duration_ms
