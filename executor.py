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
              result = subprocess.run(
                  cmd,
                  shell=True,
                  capture_output=True,
                  text=True,
                  encoding="utf-8",
                  errors="replace",
                  timeout=self._timeout,
              )
              out  = result.stdout
              err  = result.stderr
              code = result.returncode
          except subprocess.TimeoutExpired:
              out  = ""
              err  = f"Command timed out after {self._timeout}s"
              code = -1
          except Exception as exc:
              out  = ""
              err  = str(exc)
              code = -1

          elapsed = round(time.time() - ts_start, 3)
          return CommandRecord(
              cmd=cmd,
              stdout=out,
              stderr=err,
              code=code,
              elapsed=elapsed,
          )
  