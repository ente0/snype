"""Welcome view: initial dashboard."""
from __future__ import annotations

from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .base import ViewWidget


BANNER = r"""
  _____ ____   __ __  ____   ___
 / ___/|    \ |  |  ||    \ /  _]
(   \_ |  _  ||  |  ||  o  )  [_
 \__  ||  |  ||  ~  ||   _/    _]
 /  \ ||  |  ||___, ||  | |   [_
 \    ||  |  ||     ||  | |     |
  \___||__|__||____/ |__| |_____|
"""


class WelcomeView(ViewWidget):
    def _build(self):
        banner = Text(BANNER, style="bold blue")

        info = Table.grid(padding=(0, 2))
        info.add_column(style="dim cyan", justify="right")
        info.add_column(style="white")
        info.add_row("data", str(self.state.paths.root))
        info.add_row("handshakes", str(self.state.paths.hs))
        info.add_row("logs", str(self.state.paths.logs))
        info.add_row("term mode", self.state.term_mode)
        info.add_row("dry run", "yes" if self.state.dry_run else "no")

        hints = Table.grid(padding=(0, 2))
        hints.add_column(style="bold cyan", justify="right")
        hints.add_column(style="white")
        for k, v in [
            ("s", "scan networks"),
            ("m", "monitor selected target"),
            ("d", "deauth attack"),
            ("c", "wordlist cracking"),
            ("f", "browse captures"),
            ("?", "show help"),
        ]:
            hints.add_row(k, v)

        return Panel(
            Group(
                Align.center(banner),
                Align.center(Text("WPA Handshake Capture Utility", style="italic")),
                Text(""),
                Panel(info, title="workspace", border_style="grey50"),
                Panel(hints, title="shortcuts", border_style="grey50"),
            ),
            border_style="blue",
        )
