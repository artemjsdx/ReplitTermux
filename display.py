"""
display.py — Terminal output / UI rendering.
S: One responsibility — all Rich-based terminal presentation.

Mobile-friendly: plain print() + ANSI, no Rich width calculations.
"""
from history import CommandRecord

_O   = "\033[0m"
_B   = "\033[1m"
_DIM = "\033[2m"
_CYA = "\033[96m"
_GRN = "\033[92m"
_RED = "\033[91m"
_ORG = "\033[38;5;208m"


def _hr(label: str = "") -> None:
    if label:
        print(f"{_ORG}── {label} ──{_O}")
    else:
        print(f"{_DIM}{'─' * 32}{_O}")


# ── startup ────────────────────────────────────────────────────────────────────
def print_startup(port: int) -> None:
    _hr("ReplitTermux v3.0")
    print(f"{_DIM}server : localhost:{port}{_O}")
    print(f"{_DIM}tunnel : serveo.net...{_O}")
    print(f"{_DIM}stop   : Ctrl+C{_O}")
    print()


# ── полные данные (когда TG не настроен) ───────────────────────────────────────
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


# ── краткий статус (когда TG настроен) ────────────────────────────────────────
def print_bridge_ready() -> None:
    print()
    _hr("✓ Мост готов")
    print(f"{_GRN}Данные отправлены в Telegram.{_O}")
    _hr()
    print()


# ── результат команды ──────────────────────────────────────────────────────────
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


# ── периодический статус ───────────────────────────────────────────────────────
def print_status_table(records: list[CommandRecord]) -> None:
    if not records:
        return
    _hr("история")
    for h in reversed(records):
        icon = f"{_GRN}✓{_O}" if h.code == 0 else f"{_RED}✗{_O}"
        print(f"  {_DIM}{h.ts}{_O}  {icon}  {h.cmd[:30]}")
    print()


# ── ошибка ─────────────────────────────────────────────────────────────────────
def print_error(msg: str) -> None:
    print(f"{_RED}✗ {msg}{_O}")
