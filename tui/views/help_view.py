"""Help overlay content."""
from __future__ import annotations

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .base import ViewWidget


class HelpView(ViewWidget):
    def _build(self):
        globals_kb = Table(title="global", box=None)
        globals_kb.add_column("key", style="cyan", no_wrap=True)
        globals_kb.add_column("action")
        for k, v in [
            ("s", "Scan networks"),
            ("m", "Monitor + deauth (dual pane)"),
            ("d", "Standalone deauth"),
            ("c", "Wordlist cracking"),
            ("f", "Files browser"),
            ("t", "Settings"),
            ("?", "This help"),
            ("h", "Home / welcome"),
            ("q", "Quit"),
        ]:
            globals_kb.add_row(k, v)

        scan_kb = Table(title="in scan", box=None)
        scan_kb.add_column("key", style="cyan", no_wrap=True)
        scan_kb.add_column("action")
        for k, v in [
            ("r", "Start a scan"),
            ("up / down", "Move selection"),
            ("enter", "Pick target"),
            ("+ / -", "Adjust duration"),
        ]:
            scan_kb.add_row(k, v)

        settings_kb = Table(title="in settings", box=None)
        settings_kb.add_column("key", style="cyan", no_wrap=True)
        settings_kb.add_column("action")
        for k, v in [
            ("1", "Set monitor interface"),
            ("2", "Set inject interface"),
            ("3", "Cycle terminal backend"),
            ("f", "Flush monitor-mode services"),
        ]:
            settings_kb.add_row(k, v)

        data = Table(title="data layout", box=None)
        data.add_column("path", style="yellow")
        data.add_column("purpose")
        data.add_row(str(self.state.paths.root), "workspace root")
        data.add_row(str(self.state.paths.hs), "captures by ESSID / session")
        data.add_row(str(self.state.paths.config), "interfaces + last target")
        data.add_row(str(self.state.paths.found_passwords), "recovered keys")

        return Panel(
            Group(globals_kb, Text(""), scan_kb, Text(""), settings_kb, Text(""), data),
            title="help",
            border_style="blue",
        )
