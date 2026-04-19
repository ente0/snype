"""Bottom footer: contextual keybindings hint and last log line."""
from __future__ import annotations

from rich.text import Text
from textual.widget import Widget
from textual.widgets import Static

from ..state import AppState


NAV_KEYS = [
    ("s", "Scan"), ("m", "Monitor"), ("d", "Deauth"), ("c", "Crack"),
    ("f", "Files"), ("?", "Help"), ("q", "Quit"),
]


class FooterBar(Widget):
    DEFAULT_CSS = """
    FooterBar {
        dock: bottom;
        height: 1;
    }
    """

    def __init__(self, state: AppState, **kwargs) -> None:
        super().__init__(**kwargs)
        self.state = state

    def compose(self):
        yield Static(self._build(), id="content", expand=True)

    def on_mount(self) -> None:
        self.state.subscribe(self._on_state_change)

    def _on_state_change(self) -> None:
        try:
            self.app.call_from_thread(self._do_refresh)
        except Exception:
            pass

    def _do_refresh(self) -> None:
        try:
            self.query_one("#content", Static).update(self._build())
        except Exception:
            pass

    def _build(self) -> Text:
        text = Text()
        for k, label in NAV_KEYS:
            text.append(f" {k} ", style="reverse bold")
            text.append(f" {label} ", style="white")
        tail = self.state.last_log()
        if tail:
            text.append("  │  ", style="dim")
            text.append(tail[:120], style="dim italic")
        return text
