"""Monitor view: inline real-time display of airodump-ng + aireplay-ng."""
from __future__ import annotations

import subprocess
import threading
import time
from collections import deque
from pathlib import Path

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.binding import Binding

from .base import ViewWidget
from ..state import AppState
from core import airodump, aireplay, session as session_mod
from core.hashcat_convert import (
    ConversionStatus,
    convert_capture,
    extract_essid_via_aircrack,
    find_hcxpcapngtool,
)

_POLL_INTERVAL = 1.0
_MAX_DEAUTH_LINES = 18

_IDLE = "idle"
_RUNNING = "running"


class MonitorView(ViewWidget):
    BINDINGS = [
        Binding("enter", "launch", "Launch", show=False),
        Binding("escape", "stop_all", "Stop all", show=False),
        Binding("1", "stop_airodump", "Stop monitor", show=False),
        Binding("2", "stop_deauth", "Stop deauth", show=False),
    ]

    def __init__(self, state: AppState, **kwargs) -> None:
        super().__init__(state, **kwargs)
        self._phase = _IDLE
        self._session = None
        self._airodump_proc: subprocess.Popen | None = None
        self._aireplay_proc: subprocess.Popen | None = None
        self._airodump_networks: list = []
        self._airodump_stations: list = []
        self._aireplay_lines: deque[str] = deque(maxlen=_MAX_DEAUTH_LINES)
        self._airodump_stopped = False
        self._aireplay_stopped = False
        self._timer = None
        self._started_at: float | None = None
        self._last_result: str | None = None
        self._error: str | None = None

    # ── render ────────────────────────────────────────────────────────────────

    def _build(self):
        if self._phase == _RUNNING:
            return self._build_running()
        return self._build_idle()

    def _build_idle(self):
        cfg = self.state.config
        grid = Table.grid(padding=(0, 2))
        grid.add_column(style="dim cyan", justify="right")
        grid.add_column(style="white")
        grid.add_row("monitor iface", cfg.monitor_iface or "[red]not set[/red]")
        grid.add_row("inject iface", cfg.effective_inject() or "[red]not set[/red]")
        grid.add_row("target bssid", cfg.target.bssid or "[red]not set[/red]")
        grid.add_row("channel", str(cfg.target.channel or "—"))
        grid.add_row("essid", cfg.target.essid or "—")

        body: list = [grid, Text("")]
        if self._error:
            body.append(Text(f" {self._error} ", style="bold red on grey19"))
        elif self._last_result:
            body.append(Text(f" {self._last_result} ", style="bold green on grey19"))
        else:
            body.append(Text(
                " [enter] launch monitor + deauth ",
                style="bold green on grey19",
            ))
        return Panel(Group(*body), title="monitor + deauth", border_style="blue")

    def _build_running(self):
        cfg = self.state.config
        elapsed = int(time.time() - (self._started_at or time.time()))

        # ── airodump panel ────────────────────────────────────────────────────
        if self._airodump_stopped:
            a_status = Text(" stopped ", style="dim on grey19")
            a_border = "dim"
        else:
            a_status = Text()
            a_status.append(f" running {elapsed}s ", style="bold yellow on grey19")
            a_status.append("  [1] stop", style="dim")
            a_border = "yellow"

        ap_table = Table(show_lines=False, box=None, pad_edge=False)
        ap_table.add_column("BSSID", style="yellow")
        ap_table.add_column("CH", width=3, justify="right")
        ap_table.add_column("PWR", width=4, justify="right")
        ap_table.add_column("Beacons", width=8, justify="right", style="dim")
        ap_table.add_column("Data", width=6, justify="right", style="bold cyan")
        ap_table.add_column("ESSID", style="cyan", overflow="fold")
        for net in self._airodump_networks:
            ap_table.add_row(
                net.bssid, net.channel, net.power,
                net.beacons, net.data, net.essid or "(hidden)",
            )

        a_body: list = [a_status, Text("")]
        if self._airodump_networks:
            a_body.append(ap_table)
        else:
            a_body.append(Text("waiting for data…", style="dim"))

        if self._airodump_stations:
            sta_table = Table(show_lines=False, box=None, pad_edge=False)
            sta_table.add_column("Station", style="dim yellow")
            sta_table.add_column("PWR", width=4, justify="right")
            sta_table.add_column("Pkts", width=5, justify="right", style="cyan")
            for sta in self._airodump_stations:
                sta_table.add_row(sta.mac, sta.power, sta.packets)
            a_body += [Text(""), Text(" stations ", style="dim"), sta_table]

        airodump_panel = Panel(
            Group(*a_body),
            title=f"airodump-ng  [{cfg.monitor_iface or '?'}]",
            border_style=a_border,
        )

        # ── aireplay panel ────────────────────────────────────────────────────
        if self._aireplay_stopped:
            d_status = Text(" stopped ", style="dim on grey19")
            d_border = "dim"
        else:
            d_status = Text()
            d_status.append(" running ", style="bold red on grey19")
            d_status.append("  [2] stop", style="dim")
            d_border = "red"

        d_body: list = [d_status, Text("")]
        lines = list(self._aireplay_lines)
        if lines:
            for line in lines:
                d_body.append(Text(line, style="white"))
        else:
            d_body.append(Text("waiting for output…", style="dim"))

        deauth_panel = Panel(
            Group(*d_body),
            title=f"aireplay-ng  [{cfg.effective_inject() or '?'}]",
            border_style=d_border,
        )

        footer = Text("[esc] stop all", style="dim")
        return Group(airodump_panel, deauth_panel, footer)

    # ── poll ──────────────────────────────────────────────────────────────────

    def _poll(self) -> None:
        if self._phase != _RUNNING:
            return

        # Update airodump stats from CSV
        if self._session and not self._airodump_stopped:
            cap_stem = self._session.directory / session_mod.CAPTURE_STEM
            nets, stas = airodump.read_capture_stats(cap_stem)
            if nets:
                self._airodump_networks = nets
                self._airodump_stations = stas

        # Detect process exits
        if self._airodump_proc and self._airodump_proc.poll() is not None:
            if not self._airodump_stopped:
                self._airodump_stopped = True
                self.state.log("[monitor] airodump-ng exited")

        if self._aireplay_proc and self._aireplay_proc.poll() is not None:
            if not self._aireplay_stopped:
                self._aireplay_stopped = True
                self.state.log("[monitor] aireplay-ng exited")

        # End session when both stop
        if self._airodump_stopped and self._aireplay_stopped:
            self._end_session()
            return

        self._do_refresh()

    # ── launch ────────────────────────────────────────────────────────────────

    def action_launch(self) -> None:
        if self._phase != _IDLE:
            return
        cfg = self.state.config
        if not find_hcxpcapngtool():
            self._error = "hcxpcapngtool not found — install hcxtools"
            self.state.log("[monitor] hcxpcapngtool not found in PATH")
            self._do_refresh()
            return
        if not cfg.monitor_iface:
            self._error = "monitor interface not set — open Settings [t]"
            self._do_refresh()
            return
        if not cfg.target.bssid:
            self._error = "no target — run Scan [s] first"
            self._do_refresh()
            return
        self._error = None
        self._last_result = None
        self._airodump_networks = []
        self._airodump_stations = []
        self._aireplay_lines.clear()
        threading.Thread(target=self._start_worker, daemon=True).start()

    def _start_worker(self) -> None:
        cfg = self.state.config
        try:
            airodump.kill_interfering_processes()
        except Exception as exc:
            self.state.log(f"[monitor] warning: {exc}")

        essid = cfg.target.essid or cfg.target.bssid.replace(":", "")
        sess = session_mod.new_session(
            self.state.paths, essid, cfg.target.bssid, cfg.target.channel
        )
        cap_stem = sess.directory / session_mod.CAPTURE_STEM

        try:
            a_proc = airodump.start_targeted_capture(
                cfg.monitor_iface, cfg.target.bssid, cfg.target.channel, cap_stem,
            )
            d_proc = aireplay.start_deauth(cfg.effective_inject(), cfg.target.bssid)
        except Exception as exc:
            self.app.call_from_thread(self._on_error, str(exc))
            return

        self.app.call_from_thread(self._on_launched, sess, a_proc, d_proc)

    def _on_launched(self, sess, a_proc, d_proc) -> None:
        self._session = sess
        self._airodump_proc = a_proc
        self._aireplay_proc = d_proc
        self._airodump_stopped = False
        self._aireplay_stopped = False
        self._started_at = time.time()
        self._phase = _RUNNING
        self.state.log(f"[monitor] session {sess.directory.name} started")
        threading.Thread(
            target=self._read_deauth_output, args=(d_proc,), daemon=True,
        ).start()
        self._timer = self.set_interval(_POLL_INTERVAL, self._poll)
        self._do_refresh()

    def _on_error(self, msg: str) -> None:
        self._error = msg
        self._phase = _IDLE
        self._do_refresh()

    def _read_deauth_output(self, proc: subprocess.Popen) -> None:
        """Background thread: stream aireplay-ng lines into the deque."""
        try:
            for raw in proc.stdout:
                line = raw.rstrip()
                if line:
                    self._aireplay_lines.append(line)
        except Exception:
            pass

    # ── stop ──────────────────────────────────────────────────────────────────

    def action_stop_all(self) -> None:
        if self._phase != _RUNNING:
            return
        self._kill_airodump()
        self._kill_aireplay()
        self._end_session()

    def action_stop_airodump(self) -> None:
        if self._phase == _RUNNING and not self._airodump_stopped:
            self._kill_airodump()
            self._do_refresh()

    def action_stop_deauth(self) -> None:
        if self._phase == _RUNNING and not self._aireplay_stopped:
            self._kill_aireplay()
            self._do_refresh()

    def _kill_airodump(self) -> None:
        if self._airodump_proc and self._airodump_proc.poll() is None:
            self._airodump_proc.terminate()
            try:
                self._airodump_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._airodump_proc.kill()
        self._airodump_stopped = True

    def _kill_aireplay(self) -> None:
        if self._aireplay_proc and self._aireplay_proc.poll() is None:
            self._aireplay_proc.terminate()
            try:
                self._aireplay_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._aireplay_proc.kill()
        self._aireplay_stopped = True

    def _end_session(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None
        self._phase = _IDLE
        self.state.log("[monitor] session ended")
        if self._session:
            threading.Thread(
                target=self._finalise_session,
                args=(self._session,),
                daemon=True,
            ).start()
        self._do_refresh()

    # ── finalise ──────────────────────────────────────────────────────────────

    def _finalise_session(self, sess) -> None:
        time.sleep(1)  # let airodump flush last write
        cap_candidate = sess.directory / f"{session_mod.CAPTURE_STEM}-01.cap"
        if cap_candidate.exists():
            cap_candidate.rename(sess.capture_path)

        msg = "session ended"
        result_is_error = False
        if sess.capture_path.exists():
            essid = extract_essid_via_aircrack(sess.capture_path)
            if essid and (not sess.essid or sess.essid == sess.bssid.replace(":", "")):
                sess.essid = essid
            result = convert_capture(sess.capture_path, sess.hashcat_path)
            sess.handshake_complete = result.status == ConversionStatus.SUCCESS
            if result.status == ConversionStatus.SUCCESS:
                msg = f"capture saved → {result.output.name}"
            elif result.status == ConversionStatus.NO_HANDSHAKE:
                msg = "capture saved (no handshake)"
            else:
                result_is_error = True
                msg = f"capture saved (conversion failed: {result.detail})"
                self.state.log(f"[monitor] conversion failed: {result.detail}")
        else:
            msg = "no capture file"
            result_is_error = True

        sess.mark_stopped()
        sess.save_meta()

        try:
            self.app.call_from_thread(self._set_result, msg, result_is_error)
        except Exception:
            pass

    def _set_result(self, msg: str, is_error: bool = False) -> None:
        self._error = msg if is_error else None
        self._last_result = None if is_error else msg
        self._do_refresh()
