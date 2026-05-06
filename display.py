"""
display.py — Terminal output / UI rendering.
S: One responsibility — all Rich-based terminal presentation.

Mobile-friendly rules:
  - Labels via Rich (short, coloured).
  - Raw data (URL, token, output lines) via plain print() — bypasses Rich width-wrap.
  - No alignment padding.
"""
from rich.console import Console
from rich.rule    import Rule
from rich.table   import Table
from rich         import box as rbox
from history      import CommandRecord

console = Console()

_O = "\033[0m"          # reset
_B = "\033[1m"          # bold
_DIM = "\033[2m"        # dim
_CYA = "\033[96m"       # bright cyan
_GRN = "\033[92m"       # bright green
_RED = "\033[91m"       # bright red
_ORG = "\033[38;5;208m" # orange


def _hr(label: str = "") -> None:
    """Print a plain separator line with optional label."""
    if label:
        print(f"{_ORG}── {label} ──{_O}")
    else:
        print(f"{_DIM}{'─' * 32}{_O}")


# ── startup header ─────────────────────────────────────────────────────────────
def print_startup(port: int) -> None:
    _hr("ReplitTermux v3.0")
    print(f"{_DIM}server : localhost:{port}{_O}")
    print(f"{_DIM}tunnel : serveo.net...{_O}")
    print(f"{_DIM}stop   : Ctrl+C{_O}")
    print()


# ── connection info ─────────────────────────────────────────────────────────────
def print_connection_info(url: str, token: str) -> None:
    print()
    _hr("✓ Мост готов")
    print(f"{_DIM}URL:{_O}")
    print(f"{_CYA}{_B}{url}{_O}")
    print()
    print(f"{_DIM}Token:{_O}")
    print(f"{_GRN}{_B}{token}{_O}")
    print()
    print(f"{_DIM}Web:{_O}")
    print(f"{_DIM}{url}/?token={token}{_O}")
    _hr()
    print()


# ── command result ──────────────────────────────────────────────────────────────
def print_result(r: CommandRecord) -> None:
    color = _GRN if r.code == 0 else _RED
    icon  = "✓"  if r.code == 0 else "✗"
    print(f"{_ORG}▶{_O} {_B}{r.cmd}{_O}")
    if r.out:
        for line in r.out[:2000].splitlines():
            print(f"  {line}")
        if len(r.out) > 2000:
            print("  ...")
    print(f"{color}{icon} EXIT {r.code}{_O}  {_DIM}({r.elapsed}s){_O}")
    print()


# ── periodic status ─────────────────────────────────────────────────────────────
def print_status_table(records: list[CommandRecord]) -> None:
    if not records:
        return
    _hr("история")
    for h in reversed(records):
        icon = f"{_GRN}✓{_O}" if h.code == 0 else f"{_RED}✗{_O}"
        print(f"  {_DIM}{h.ts}{_O}  {icon}  {h.cmd[:30]}")
    print()


# ── error helper ───────────────────────────────────────────────────────────────
def print_error(msg: str) -> None:
    print(f"{_RED}✗ {msg}{_O}")
