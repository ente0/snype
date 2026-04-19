"""Standalone deauth view (without concurrent monitoring)."""
from __future__ import annotations

import subprocess
import threading
import time

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.binding import Binding

from .base import ViewWidget
from ..state import AppState
from core import aireplay


class DeauthView(ViewWidget):
    BINDINGS = [
        Binding("enter", "run_deauth", "Run", show=False),
        Binding("plus", "increase_duration", "+dur", show=False),
        Binding("minus", "decrease_duration", "-dur", show=False),
        Binding("c", "clear_client", "Clear client", show=False),
    ]

    def __init__(self, state: AppState, **kwargs) -> None:
        super().__init__(state, **kwargs)
        self._duration = 10
        self._client = ""
        self._running = False
        self._last_rc: int | None = None

    def _build(self):
        cfg = self.state.config
        grid = Table.grid(padding=(0, 2))
        grid.add_column(style="dim cyan", justify="right")
        grid.add_column(style="white")
        grid.add_row("inject iface", cfg.effective_inject() or "[red]not set[/red]")
        grid.add_row("target bssid", cfg.target.bssid or "[red]not set[/red]")
        grid.add_row("client mac", self._client or "all clients")
        grid.add_row("duration", f"{self._duration}s (0 = continuous)")

        body: list = [grid, Text("")]
        if self._running:
            body.append(Text(" deauth running… ", style="bold yellow on grey19"))
        elif self._last_rc is not None:
            style = "green" if self._last_rc == 0 else "red"
            body.append(Text(f" last run exit code: {self._last_rc} ", style=style))
        else:
            body.append(
                Text(
                    " [enter] run  [+/-] duration  [ctrl+c] clear client ",
                    style="bold green on grey19",
                )
            )

        return Panel(Group(*body), title="deauth", border_style="blue")

    def action_run_deauth(self) -> None:
        cfg = self.state.config
        if self._running:
            return
        iface = cfg.effective_inject()
        if not (iface and cfg.target.bssid):
            self.state.log("[deauth] missing interface or target")
            return
        cmd = aireplay.build_deauth_cmd(iface, cfg.target.bssid, self._client or None, count=0)
        threading.Thread(target=self._run_worker, args=(cmd,), daemon=True).start()

    def _run_worker(self, cmd: list) -> None:
        self._running = True
        self.state.log(f"[deauth] $ {' '.join(cmd)}")
        if self.state.dry_run:
            self._last_rc = 0
        else:
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if self._duration > 0:
                    try:
                        proc.wait(timeout=self._duration)
                    except subprocess.TimeoutExpired:
                        proc.terminate()
                        try:
                            proc.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            proc.kill()
                else:
                    proc.wait()
                self._last_rc = proc.returncode
            except Exception as exc:
                self.state.log(f"[deauth] error: {exc}")
                self._last_rc = -1
        self._running = False
        try:
            self.app.call_from_thread(self._do_refresh)
        except Exception:
            pass

    def action_increase_duration(self) -> None:
        self._duration = min(600, self._duration + 5)
        self._do_refresh()

    def action_decrease_duration(self) -> None:
        self._duration = max(0, self._duration - 5)
        self._do_refresh()

    def action_clear_client(self) -> None:
        self._client = ""
        self._do_refresh()
