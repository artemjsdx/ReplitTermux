"""
display.py — Terminal output / UI rendering.
S: One responsibility — all Rich-based terminal presentation.

Mobile-friendly: no alignment padding, no long wrapping lines.
"""
from rich.console import Console
from rich.rule    import Rule
from rich.table   import Table
from rich         import box as rbox
from history      import CommandRecord

console = Console()


# ── startup header ─────────────────────────────────────────────────────────────
def print_startup(port: int) -> None:
    console.print(Rule("[bold #ff8c00]ReplitTermux v3.0[/bold #ff8c00]"))
    console.print(f"[dim]server : localhost:{port}[/dim]")
    console.print(f"[dim]tunnel : serveo.net...[/dim]")
    console.print(f"[dim]stop   : Ctrl+C[/dim]")
    console.print()


# ── connection info ─────────────────────────────────────────────────────────────
def print_connection_info(url: str, token: str) -> None:
    console.print()
    console.print(Rule("[bold #ff8c00]✓ Мост готов[/bold #ff8c00]"))
    console.print(f"[dim]URL[/dim]")
    console.print(f"[bold cyan]{url}[/bold cyan]")
    console.print()
    console.print(f"[dim]Token[/dim]")
    console.print(f"[bold #3fb950]{token}[/bold #3fb950]")
    console.print()
    console.print(f"[dim]Web → {url}/?token={token}[/dim]")
    console.print(Rule(style="dim"))
    console.print()


# ── command result ──────────────────────────────────────────────────────────────
def print_result(r: CommandRecord) -> None:
    color = "#3fb950" if r.code == 0 else "#f85149"
    icon  = "✓"       if r.code == 0 else "✗"
    console.print(f"[bold #ff8c00]▶[/bold #ff8c00] [bold]{r.cmd}[/bold]")
    if r.out:
        for line in r.out[:2000].splitlines():
            console.print(f"  {line}")
        if len(r.out) > 2000:
            console.print("  [dim]...[/dim]")
    console.print(f"[{color}]{icon} EXIT {r.code}[/{color}] [dim]({r.elapsed}s)[/dim]")
    console.print()


# ── periodic status ─────────────────────────────────────────────────────────────
def print_status_table(records: list[CommandRecord]) -> None:
    if not records:
        return
    t = Table(
        box=rbox.SIMPLE, show_header=True,
        header_style="bold #ff8c00", show_edge=False,
        pad_edge=False,
    )
    t.add_column("Time", width=8, style="dim")
    t.add_column("Cmd",  max_width=20, style="bold", no_wrap=True)
    t.add_column("RC",   width=3)
    for h in reversed(records):
        icon = "[#3fb950]✓[/#3fb950]" if h.code == 0 else "[#f85149]✗[/#f85149]"
        t.add_row(h.ts, h.cmd[:20], f"{icon}{h.code}")
    console.print(t)


# ── error helper ───────────────────────────────────────────────────────────────
def print_error(msg: str) -> None:
    console.print(f"[red]✗ {msg}[/red]")
