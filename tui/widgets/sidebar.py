"""Left sidebar: navigation between views."""
from __future__ import annotations

from rich.align import Align
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


SIDEBAR_ENTRIES = [
    ("s", "scan", "Scan"),
    ("m", "monitor", "Monitor"),
    ("d", "deauth", "Deauth"),
    ("c", "crack", "Crack"),
    ("f", "files", "Files"),
    ("t", "settings", "Settings"),
    ("?", "help", "Help"),
]


class SidebarWidget(Widget):
    active_view_id: reactive[str] = reactive("welcome")

    def compose(self):
        yield Static(self._build(), id="content", expand=True)

    def watch_active_view_id(self, _: str) -> None:
        try:
            self.query_one("#content", Static).update(self._build())
        except Exception:
            pass

    def _build(self):
        table = Table.grid(padding=(0, 1))
        table.add_column()
        table.add_column()
        active = self.active_view_id
        for key, view_id, label in SIDEBAR_ENTRIES:
            is_active = view_id == active
            key_cell = Text(f"[{key}]", style="bold cyan" if is_active else "dim cyan")
            label_cell = Text(
                label,
                style="bold white on grey35" if is_active else "white",
            )
            table.add_row(key_cell, label_cell)
        table.add_row("", "")
        table.add_row(Text("[q]", style="dim"), Text("Quit", style="dim"))
        return Panel(Align.left(table), title="snype", title_align="left", border_style="blue")
