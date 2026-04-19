"""Scan view: enables monitor mode, then runs airodump-ng live."""
from __future__ import annotations

import subprocess
import tempfile
import threading
import time
from pathlib import Path

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.binding import Binding

from .base import ViewWidget
from ..state import AppState
from core import airodump
from core.interfaces import enable_monitor_mode, get_mode

_POLL_INTERVAL = 2.0  # seconds between CSV reads

# internal phase constants
_IDLE      = "idle"
_PREPARING = "preparing"
_SCANNING  = "scanning"


class ScanView(ViewWidget):
    BINDINGS = [
        Binding("r", "start_scan", "Scan", show=False),
        Binding("escape", "stop_scan", "Stop", show=False),
        Binding("up", "move_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("enter", "select_network", "Select", show=False),
        Binding("plus", "increase_duration", "+dur", show=False),
        Binding("minus", "decrease_duration", "-dur", show=False),
    ]

    def __init__(self, state: AppState, **kwargs) -> None:
        super().__init__(state, **kwargs)
        self._networks: list = []
        self._phase: str = _IDLE
        self._selected = 0
        self._error: str | None = None
        self._duration = 20
        self._started_at: float | None = None
        self._proc: subprocess.Popen | None = None
        self._tmpdir: tempfile.TemporaryDirectory | None = None
        self._timer = None

    def on_show(self) -> None:
        super().on_show()
        self._do_refresh()

    # ── render ────────────────────────────────────────────────────────────────

    def _build(self):
        if self._phase == _PREPARING:
            iface = self.state.config.monitor_iface or "?"
            header = Text()
            header.append(f" enabling monitor mode on {iface}… ", style="bold cyan on grey19")
            return Panel(
                Group(header, Text(""), Text("please wait", style="dim")),
                title="scan",
                border_style="cyan",
            )

        if self._phase == _SCANNING:
            elapsed = int(time.time() - (self._started_at or time.time()))
            remaining = max(0, self._duration - elapsed)
            header = Text()
            header.append(
                f" scanning… {elapsed}s / {self._duration}s ",
                style="bold yellow on grey19",
            )
            header.append(f"  {remaining}s left  ", style="dim yellow")
            header.append("  [esc] stop  [↑↓] select  [enter] pick")
        else:  # idle
            header = Text()
            header.append(
                f" [r] start {self._duration}s scan   [+/-] duration ",
                style="bold green on grey19",
            )
            tgt = self.state.config.target.bssid
            if tgt:
                essid = self.state.config.target.essid or ""
                label = f"{essid} ({tgt})" if essid else tgt
                header.append(f"   target: ", style="dim")
                header.append(label, style="bold green")
            else:
                header.append("   [enter] pick target")

        if self._error:
            return Panel(
                Group(header, Text(""), Text(self._error, style="red")),
                title="scan",
                border_style="red",
            )

        if not self._networks:
            hint = (
                "waiting for networks…"
                if self._phase == _SCANNING
                else "no networks — press r to scan"
            )
            return Panel(
                Group(header, Text(""), Text(hint, style="dim")),
                title="scan",
                border_style="yellow" if self._phase == _SCANNING else "blue",
            )

        target_bssid = (self.state.config.target.bssid or "").upper()
        table = Table(show_lines=False, box=None, pad_edge=False)
        table.add_column("", width=2)  # target indicator
        table.add_column("#", style="dim", width=3)
        table.add_column("BSSID", style="yellow")
        table.add_column("CH", width=3, justify="right")
        table.add_column("PWR", width=4, justify="right")
        table.add_column("ESSID", style="cyan", overflow="fold")
        for i, net in enumerate(self._networks):
            s = "reverse" if i == self._selected else ""
            is_target = target_bssid and net.bssid.upper() == target_bssid
            indicator = Text("*", style="bold green" if not s else "bold green reverse")
            table.add_row(
                indicator if is_target else Text(" "),
                Text(str(i), style=s),
                Text(net.bssid, style=s),
                Text(net.channel, style=s),
                Text(net.power, style=s),
                Text(net.essid or "(hidden)", style=s),
            )

        border = "yellow" if self._phase == _SCANNING else "blue"
        return Panel(
            Group(header, Text(""), table),
            title="scan",
            subtitle=f"{len(self._networks)} networks",
            border_style=border,
        )

    # ── poll (Textual timer — main thread) ────────────────────────────────────

    def _poll(self) -> None:
        if self._phase != _SCANNING or self._tmpdir is None:
            return
        networks = airodump.read_live_csv(Path(self._tmpdir.name))
        if networks:
            self._networks = networks
            if self._selected >= len(self._networks):
                self._selected = len(self._networks) - 1
        elapsed = time.time() - (self._started_at or time.time())
        if elapsed >= self._duration:
            self._stop_scan()
        else:
            self._do_refresh()

    # ── setup thread ──────────────────────────────────────────────────────────

    def _setup_worker(self, iface: str) -> None:
        """Background thread: check/enable monitor mode, then start scan."""
        try:
            mode = get_mode(iface)
            if mode == "monitor":
                self.state.log(f"[scan] {iface} already in monitor mode")
                airodump.kill_interfering_processes()
                monitor_iface = iface
            else:
                self.state.log(f"[scan] enabling monitor mode on {iface}…")
                airodump.kill_interfering_processes()
                monitor_iface = enable_monitor_mode(iface)
                if monitor_iface != iface:
                    self.state.log(f"[scan] monitor interface: {monitor_iface}")
        except Exception as exc:
            self.app.call_from_thread(self._on_setup_error, str(exc))
            return
        self.app.call_from_thread(self._on_setup_done, monitor_iface)

    def _on_setup_done(self, monitor_iface: str) -> None:
        """Called on main thread after monitor mode is confirmed."""
        # Update config if airmon-ng created a new interface name (e.g. wlan1 → wlan1mon)
        old_iface = self.state.config.monitor_iface
        if monitor_iface != old_iface:
            self.state.config.monitor_iface = monitor_iface
            # Keep inject_iface in sync when it pointed at the same interface
            if self.state.config.inject_iface == old_iface:
                self.state.config.inject_iface = monitor_iface
                self.state.log(f"[scan] inject interface updated: {monitor_iface}")
            self.state.save_config()

        if self.state.dry_run:
            self.state.log(
                f"[scan] dry-run: would run airodump-ng on {monitor_iface} "
                f"for {self._duration}s"
            )
            self._phase = _SCANNING
            self._started_at = time.time()
            self._timer = self.set_interval(_POLL_INTERVAL, self._poll)
            self._do_refresh()
            return

        self._tmpdir = tempfile.TemporaryDirectory(prefix="snype-scan-")
        self._proc = airodump.start_live_scan(monitor_iface, Path(self._tmpdir.name))
        self._phase = _SCANNING
        self._started_at = time.time()
        self._timer = self.set_interval(_POLL_INTERVAL, self._poll)
        self.state.log(f"[scan] started — {monitor_iface}  duration {self._duration}s")
        self._do_refresh()

    def _on_setup_error(self, msg: str) -> None:
        """Called on main thread if monitor mode setup fails."""
        self._error = msg
        self._phase = _IDLE
        self._do_refresh()

    # ── stop ──────────────────────────────────────────────────────────────────

    def _stop_scan(self) -> None:
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        airodump.stop_live_scan(self._proc)
        self._proc = None
        if self._tmpdir is not None:
            networks = airodump.read_live_csv(Path(self._tmpdir.name))
            if networks:
                self._networks = networks
            self._tmpdir.cleanup()
            self._tmpdir = None
        was_active = self._phase != _IDLE
        self._phase = _IDLE
        if was_active:
            self.state.log(f"[scan] done — {len(self._networks)} networks")
        self._do_refresh()

    # ── actions ───────────────────────────────────────────────────────────────

    def action_start_scan(self) -> None:
        if self._phase != _IDLE:
            return
        iface = self.state.config.monitor_iface
        if not iface:
            self._error = "No monitor interface configured — open Settings (t)."
            self._do_refresh()
            return
        self._error = None
        self._networks = []
        self._selected = 0
        self._phase = _PREPARING
        self._do_refresh()
        threading.Thread(target=self._setup_worker, args=(iface,), daemon=True).start()

    def action_stop_scan(self) -> None:
        if self._phase in (_SCANNING, _PREPARING):
            self._stop_scan()

    def action_move_up(self) -> None:
        self._selected = max(0, self._selected - 1)
        self._do_refresh()

    def action_move_down(self) -> None:
        if self._networks:
            self._selected = min(len(self._networks) - 1, self._selected + 1)
        self._do_refresh()

    def action_select_network(self) -> None:
        if not self._networks:
            return
        net = self._networks[self._selected]
        self.state.config.target.bssid = net.bssid
        self.state.config.target.channel = net.channel
        self.state.config.target.essid = net.essid
        self.state.save_config()
        self.state.log(
            f"[scan] target set → {net.bssid} ch{net.channel} essid='{net.essid}'"
        )
        self._do_refresh()

    def action_increase_duration(self) -> None:
        if self._phase == _IDLE:
            self._duration = min(120, self._duration + 5)
            self._do_refresh()

    def action_decrease_duration(self) -> None:
        if self._phase == _IDLE:
            self._duration = max(5, self._duration - 5)
            self._do_refresh()
