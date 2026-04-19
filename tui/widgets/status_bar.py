"""Top status bar: interfaces, target, counts."""
from __future__ import annotations

import threading
from rich.text import Text
from textual.widget import Widget
from textual.widgets import Static

from ..state import AppState


def _count_files(root, suffix: str) -> int:
    if not root.exists():
        return 0
    return sum(1 for _ in root.rglob(f"*{suffix}"))


class StatusBarWidget(Widget):
    DEFAULT_CSS = """
    StatusBarWidget {
        dock: top;
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
        if threading.current_thread() is threading.main_thread():
            self._do_refresh()
        else:
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
        cfg = self.state.config
        paths = self.state.paths
        caps = _count_files(paths.hs, ".cap")
        hc = _count_files(paths.hs, ".hc22000")
        try:
            pw_count = (
                sum(1 for _ in paths.found_passwords.open())
                if paths.found_passwords.exists()
                else 0
            )
        except OSError:
            pw_count = 0

        text = Text()
        text.append(" snype ", style="bold white on blue")
        text.append("  ")
        text.append("iface ", style="dim")
        text.append(
            cfg.monitor_iface or "—",
            style="bold green" if cfg.monitor_iface else "red",
        )
        if cfg.inject_iface and cfg.inject_iface != cfg.monitor_iface:
            text.append("/", style="dim")
            text.append(cfg.inject_iface, style="bold green")
        text.append("  target ", style="dim")
        text.append(
            cfg.target.bssid or "—",
            style="bold yellow" if cfg.target.bssid else "red",
        )
        if cfg.target.channel:
            text.append(f" ch{cfg.target.channel}", style="yellow")
        if cfg.target.essid:
            text.append(f" {cfg.target.essid}", style="yellow")
        text.append("  ")
        text.append(f"cap:{caps} hc:{hc} pwd:{pw_count}", style="cyan")
        text.append("  term:", style="dim")
        text.append(self.state.term_mode, style="magenta")
        return text
