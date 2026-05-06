"""
executor.py — Shell command execution.
S: One responsibility — run shell commands and return structured results.
I: Executor protocol can be swapped (e.g., for sandboxed execution).
"""
import os, subprocess, time
from .history import CommandRecord


class ShellExecutor:
    def __init__(self, timeout: int = 60) -> None:
        self._timeout = timeout

    def run(self, cmd: str) -> CommandRecord:
        ts_start = time.time()
        try:
            proc = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=self._timeout,
                env={**os.environ, "TERM": "xterm-256color"},
            )
            out  = (proc.stdout + proc.stderr).strip()
            code = proc.returncode
        except subprocess.TimeoutExpired:
            out, code = f"TIMEOUT ({self._timeout}s)", -1
        except Exception as exc:
            out, code = f"ERROR: {exc}", -2

        return CommandRecord(
            cmd=cmd,
            out=out,
            code=code,
            elapsed=round(time.time() - ts_start, 2),
        )
