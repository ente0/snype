"""Files view: browse captured sessions, hc22000 files, recovered passwords."""
from __future__ import annotations

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .base import ViewWidget
from core import passwords


class FilesView(ViewWidget):
    def _build(self):
        hs_table = Table(title="handshakes", box=None)
        hs_table.add_column("essid", style="yellow")
        hs_table.add_column("sessions", justify="right", style="cyan")
        hs_table.add_column("cap", justify="right")
        hs_table.add_column("hc22000", justify="right")

        if self.state.paths.hs.exists():
            for essid_dir in sorted(
                p for p in self.state.paths.hs.iterdir() if p.is_dir()
            ):
                sessions = [
                    p for p in essid_dir.iterdir()
                    if p.is_dir() and p.name != "passwords"
                ]
                cap_count = sum(1 for _ in essid_dir.rglob("*.cap"))
                hc_count = sum(1 for _ in essid_dir.rglob("*.hc22000"))
                hs_table.add_row(
                    essid_dir.name, str(len(sessions)), str(cap_count), str(hc_count)
                )

        pw_table = Table(title="recovered passwords", box=None)
        pw_table.add_column("ssid", style="yellow")
        pw_table.add_column("password", style="green")
        pw_table.add_column("date", style="dim")
        entries = passwords.load_all(self.state.paths.found_passwords)
        for e in entries[-20:]:
            pw_table.add_row(e.ssid, e.password, e.date_cracked or "")
        if not entries:
            pw_table.add_row("—", "no passwords recovered yet", "")

        return Panel(
            Group(hs_table, Text(""), pw_table),
            title="files",
            border_style="blue",
        )
