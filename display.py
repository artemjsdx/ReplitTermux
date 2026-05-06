"""
display.py — Terminal output / UI rendering.
S: One responsibility — all Rich-based terminal presentation.

Design decisions:
  • No large Panel boxes — compact inline output only.
  • Rule separators instead of bordered panels.
  • Colour-coded prefix lines (▶ cmd, ✓/✗ result).
  • Connection info printed as a tight block, not a full-width panel.
"""
from rich.console import Console
from rich.rule   import Rule
from rich.table  import Table
from rich        import box as rbox
from history     import CommandRecord

console = Console()


# ── startup header ─────────────────────────────────────────────────────────────
def print_startup(port: int) -> None:
    console.clear()
    console.print(Rule("[bold #ff8c00]ReplitTermux[/bold #ff8c00]  [dim]v3.0 · bridge mode[/dim]"))
    console.print(f"  [dim]server  →  http://localhost:{port}[/dim]")
    console.print(f"  [dim]tunnel  →  connecting via serveo.net…[/dim]")
    console.print(f"  [dim]press [bold]Ctrl+C[/bold] to stop[/dim]")
    console.print()


# ── connection info ─────────────────────────────────────────────────────────────
def print_connection_info(url: str, token: str) -> None:
    web = f"{url}/?token={token}"
    console.print()
    console.print(Rule("[bold #ff8c00]✓ Мост готов[/bold #ff8c00]"))
    console.print(f"  [dim]URL  [/dim] [bold cyan]{url}[/bold cyan]")
    console.print(f"  [dim]Token[/dim] [bold #3fb950]{token}[/bold #3fb950]")
    console.print(f"  [dim]Web  [/dim] {web}")
    console.print()
    console.print(
        f"  [dim]curl -X POST {url}/run \\\n"
        f"    -H 'X-Token: {token}' \\\n"
        f"    -H 'Content-Type: application/json' \\\n"
        f"    -d '{{\"cmd\":\"uname -a\"}}'[/dim]"
    )
    console.print(Rule(style="dim"))
    console.print()


# ── command result ──────────────────────────────────────────────────────────────
def print_result(r: CommandRecord) -> None:
    color = "#3fb950" if r.code == 0 else "#f85149"
    icon  = "✓"       if r.code == 0 else "✗"
    console.print(f"[bold #ff8c00]▶[/bold #ff8c00] [bold]{r.cmd}[/bold]")
    if r.out:
        for line in r.out[:2000].splitlines():
            console.print(f"  [dim]{line}[/dim]")
        if len(r.out) > 2000:
            console.print("  [dim]…[/dim]")
    console.print(f"  [{color}]{icon} EXIT {r.code}[/{color}] [dim]({r.elapsed}s)[/dim]")
    console.print()


# ── periodic status ─────────────────────────────────────────────────────────────
def print_status_table(records: list[CommandRecord]) -> None:
    if not records:
        return
    t = Table(
        box=rbox.SIMPLE_HEAVY, show_header=True,
        header_style="bold #ff8c00", show_edge=False,
        pad_edge=False,
    )
    t.add_column("Time",    width=8,  style="dim")
    t.add_column("Command", min_width=22, style="bold")
    t.add_column("RC",      width=4)
    t.add_column("Output",  style="dim")
    for h in reversed(records):
        icon = "[#3fb950]✓[/#3fb950]" if h.code == 0 else "[#f85149]✗[/#f85149]"
        t.add_row(h.ts, h.cmd[:40], f"{icon}{h.code}", h.out[:55])
    console.print(t)


# ── error helper ───────────────────────────────────────────────────────────────
def print_error(msg: str) -> None:
    console.print(f"  [red]✗ {msg}[/red]")
