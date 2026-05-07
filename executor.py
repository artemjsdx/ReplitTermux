"""
  executor.py — Shell command execution.
  S: One responsibility — run shell commands and return structured results.
  I: Executor protocol can be swapped (e.g., for sandboxed execution).
  """
  import os, subprocess, time
  from history import CommandRecord


  class ShellExecutor:
      def __init__(self, timeout: int = 60) -> None:
          self._timeout = timeout

      def run(self, cmd: str) -> CommandRecord:
          ts_start = time.time()
          try:
              proc = subprocess.run(
                  cmd, shell=True, capture_output=True,
                  timeout=self._timeout,
                  env={**os.environ, "TERM": "xterm-256color"},
              )
              # Явно декодируем с заменой битых байт — нужно для Android/Termux
              # где системная кодировка может быть не UTF-8
              raw = (proc.stdout or b"") + (proc.stderr or b"")
              out  = raw.decode("utf-8", errors="replace").strip()
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
  