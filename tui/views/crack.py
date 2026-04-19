"""Cracking view: pick capture + wordlist, choose tool (hashcat / aircrack-ng)."""
from __future__ import annotations

import json
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
from core import crack as crack_mod, passwords
from core.hashcat_convert import convert as hc_convert


_WORDLIST_DIRS = [
    Path("/usr/share/wordlists"),
    Path.home() / "wordlists",
    Path("/usr/share/seclists/Passwords"),
    Path.cwd(),
]
_WORDLIST_EXTS = {".txt", ".lst", ".dict"}
_MAX_LINES = 28
_REFRESH_RATE = 0.5  # seconds between live display refreshes

_IDLE = "idle"
_RUNNING = "running"


class CrackView(ViewWidget):
    BINDINGS = [
        Binding("p", "pick_capture", "Capture [p]", show=False),
        Binding("w", "pick_wordlist", "Wordlist [w]", show=False),
        Binding("t", "toggle_tool", "Tool [t]", show=False),
        Binding("r", "refresh_caps", "Refresh [r]", show=False),
        Binding("up", "nav_up", "Up", show=False),
        Binding("down", "nav_down", "Down", show=False),
        Binding("enter", "confirm", "Confirm/Run", show=False),
        Binding("escape", "back_or_stop", "Back/Stop", show=False),
    ]

    def __init__(self, state: AppState, **kwargs) -> None:
        super().__init__(state, **kwargs)
        self._mode = "main"  # "main" | "pick_cap" | "pick_wordlist"
        self._phase = _IDLE
        self._cap_entries: list[dict] = []
        self._wl_entries: list[Path] = []
        self._list_idx = 0
        self._selected_cap: dict | None = None
        self._wordlist: Path | None = None
        self._tool = "hashcat"
        self._result: crack_mod.CrackResult | None = None
        self._crack_lines: deque[str] = deque(maxlen=_MAX_LINES)
        self._crack_proc: subprocess.Popen | None = None
        self._started_at: float | None = None

    def on_mount(self) -> None:
        super().on_mount()
        self._reload()

    def on_show(self) -> None:
        super().on_show()
        self._reload()
        self._do_refresh()

    # ── data loading ──────────────────────────────────────────────────────────

    def _reload(self) -> None:
        self._cap_entries = self._scan_caps()
        self._wl_entries = self._scan_wordlists()

    def _scan_caps(self) -> list[dict]:
        hs = self.state.paths.hs
        if not hs.exists():
            return []
        entries = []
        for cap in sorted(hs.rglob("*.cap"), key=lambda p: p.stat().st_mtime, reverse=True):
            meta: dict = {}
            meta_path = cap.parent / "meta.json"
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                except Exception:
                    pass
            hc_path = cap.with_suffix(".hc22000")
            has_hs = bool(meta.get("handshake_complete")) or hc_path.exists()
            ts_raw = meta.get("started_at", cap.parent.name)
            ts = ts_raw[:16].replace("T", " ") if len(ts_raw) >= 16 else ts_raw
            entries.append({
                "path": cap,
                "essid": meta.get("essid") or cap.parent.parent.name,
                "ts": ts,
                "handshake": has_hs,
                "hc_path": hc_path if hc_path.exists() else None,
            })
        return entries

    def _scan_wordlists(self) -> list[Path]:
        found: list[Path] = []
        seen: set[Path] = set()
        for d in _WORDLIST_DIRS:
            if not d.is_dir():
                continue
            for p in sorted(d.iterdir()):
                if p.is_file() and p.suffix.lower() in _WORDLIST_EXTS and p not in seen:
                    found.append(p)
                    seen.add(p)
        return found

    # ── render ────────────────────────────────────────────────────────────────

    def _build(self):
        if self._mode == "pick_cap":
            return self._build_cap_picker()
        if self._mode == "pick_wordlist":
            return self._build_wl_picker()
        if self._phase == _RUNNING:
            return self._build_running()
        return self._build_idle()

    def _build_idle(self):
        header = Text()
        if self._result is not None:
            if self._result.success:
                header.append(
                    f" KEY FOUND: {self._result.password} ", style="bold white on green"
                )
            else:
                header.append(" key not in wordlist ", style="bold white on red")
        else:
            header.append(
                " [p] capture   [w] wordlist   [t] tool   [enter] run   [r] refresh ",
                style="bold green on grey19",
            )

        grid = Table.grid(padding=(0, 2))
        grid.add_column(style="dim cyan", justify="right")
        grid.add_column(style="white")

        if self._selected_cap:
            e = self._selected_cap
            hs_tag = "[green]HS ✓[/green]" if e["handshake"] else "[red]no HS[/red]"
            grid.add_row("capture [p]", f"{e['essid']}  {e['ts']}  {hs_tag}")
        else:
            grid.add_row("capture [p]", "[red]none — press p[/red]")

        grid.add_row(
            "wordlist [w]",
            str(self._wordlist) if self._wordlist else "[red]none — press w[/red]",
        )

        tool_text = Text()
        tool_text.append(
            f" {'▸' if self._tool == 'hashcat' else ' '} hashcat ",
            style="bold green on grey19" if self._tool == "hashcat" else "dim",
        )
        tool_text.append("  ")
        tool_text.append(
            f" {'▸' if self._tool == 'aircrack' else ' '} aircrack-ng ",
            style="bold green on grey19" if self._tool == "aircrack" else "dim",
        )
        grid.add_row("tool [t]", tool_text)

        return Panel(Group(header, Text(""), grid), title="crack", border_style="blue")

    def _build_running(self):
        elapsed = int(time.time() - (self._started_at or time.time()))
        tool_name = "hashcat" if self._tool == "hashcat" else "aircrack-ng"
        header = Text()
        header.append(f" {tool_name}  running {elapsed}s ", style="bold yellow on grey19")
        header.append("  [esc] stop", style="dim")

        lines = list(self._crack_lines)
        body: list = [header, Text("")]
        if lines:
            for ln in lines:
                body.append(Text(ln, style="white", overflow="fold"))
        else:
            body.append(Text("waiting for output…", style="dim"))

        return Panel(Group(*body), title=f"crack › {tool_name}", border_style="yellow")

    def _build_cap_picker(self):
        table = Table(box=None)
        table.add_column("#", width=3, style="dim")
        table.add_column("essid", style="yellow", overflow="fold")
        table.add_column("date", style="dim", width=18)
        table.add_column("HS", width=4, justify="center")

        if not self._cap_entries:
            table.add_row(
                "", "[red]no .cap files — run a capture session first[/red]", "", ""
            )
        for i, e in enumerate(self._cap_entries):
            sel = i == self._list_idx
            hs_mark = Text("✓", style="green") if e["handshake"] else Text("✗", style="red")
            label = Text(e["essid"], style="reverse yellow" if sel else "yellow")
            table.add_row(str(i + 1), label, e["ts"], hs_mark)

        return Panel(
            Group(
                Text(
                    " [↑↓] navigate   [enter] select   [esc] back ",
                    style="bold green on grey19",
                ),
                Text(""),
                table,
            ),
            title="crack › select capture",
            border_style="blue",
        )

    def _build_wl_picker(self):
        table = Table(box=None)
        table.add_column("#", width=3, style="dim")
        table.add_column("wordlist", overflow="fold")

        if not self._wl_entries:
            table.add_row("", "[red]no wordlists found in standard paths[/red]")
        for i, p in enumerate(self._wl_entries):
            sel = i == self._list_idx
            label = Text(str(p), style="reverse" if sel else "")
            table.add_row(str(i + 1), label)

        return Panel(
            Group(
                Text(
                    " [↑↓] navigate   [enter] select   [esc] back ",
                    style="bold green on grey19",
                ),
                Text(""),
                table,
            ),
            title="crack › select wordlist",
            border_style="blue",
        )

    # ── actions ───────────────────────────────────────────────────────────────

    def action_pick_capture(self) -> None:
        if self._phase == _RUNNING or self._mode != "main":
            return
        self._mode = "pick_cap"
        self._list_idx = 0
        self._do_refresh()

    def action_pick_wordlist(self) -> None:
        if self._phase == _RUNNING or self._mode != "main":
            return
        self._mode = "pick_wordlist"
        self._list_idx = 0
        self._do_refresh()

    def action_toggle_tool(self) -> None:
        if self._phase == _RUNNING:
            return
        self._tool = "aircrack" if self._tool == "hashcat" else "hashcat"
        self._result = None
        self._do_refresh()

    def action_refresh_caps(self) -> None:
        if self._phase == _RUNNING:
            return
        self._reload()
        self._do_refresh()

    def action_nav_up(self) -> None:
        self._list_idx = max(0, self._list_idx - 1)
        self._do_refresh()

    def action_nav_down(self) -> None:
        entries = self._cap_entries if self._mode == "pick_cap" else self._wl_entries
        if entries:
            self._list_idx = min(len(entries) - 1, self._list_idx + 1)
        self._do_refresh()

    def action_confirm(self) -> None:
        if self._mode == "pick_cap":
            if self._cap_entries:
                self._selected_cap = self._cap_entries[self._list_idx]
            self._mode = "main"
            self._do_refresh()
        elif self._mode == "pick_wordlist":
            if self._wl_entries:
                self._wordlist = self._wl_entries[self._list_idx]
            self._mode = "main"
            self._do_refresh()
        else:
            self._start_crack()

    def action_back_or_stop(self) -> None:
        if self._mode != "main":
            self._mode = "main"
            self._do_refresh()
        elif self._phase == _RUNNING:
            self._stop_crack()

    # ── crack ─────────────────────────────────────────────────────────────────

    def _start_crack(self) -> None:
        if self._phase == _RUNNING:
            return
        if not self._selected_cap:
            self.state.log("[crack] select a capture file with [f]")
            return
        if not self._wordlist:
            self.state.log("[crack] select a wordlist with [w]")
            return
        self._result = None
        self._crack_lines.clear()
        self._started_at = time.time()
        self._phase = _RUNNING
        self._do_refresh()
        threading.Thread(target=self._crack_worker, daemon=True).start()

    def _stop_crack(self) -> None:
        proc = self._crack_proc
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        self._phase = _IDLE
        self.state.log("[crack] stopped")
        self._do_refresh()

    def _crack_worker(self) -> None:
        cap: Path = self._selected_cap["path"]
        wl: Path = self._wordlist
        hc: Path | None = self._selected_cap.get("hc_path")
        bssid = self.state.config.target.bssid
        active_tool = self._tool

        try:
            if self._tool == "hashcat":
                if not hc:
                    self.state.log("[crack] converting cap → hc22000…")
                    hc = hc_convert(cap, cap.with_suffix(".hc22000"))
                if not hc:
                    self.state.log("[crack] no EAPOL — falling back to aircrack-ng")
                    proc = self._popen_aircrack(cap, wl, bssid)
                    active_tool = "aircrack"
                else:
                    self.state.log(f"[crack] hashcat -m 22000 {hc.name}  wl={wl.name}")
                    proc = self._popen_hashcat(hc, wl)
            else:
                self.state.log(f"[crack] aircrack-ng -w {wl.name} {cap.name}")
                proc = self._popen_aircrack(cap, wl, bssid)

            if proc is None:
                tool_name = "hashcat" if active_tool == "hashcat" else "aircrack-ng"
                res = crack_mod.CrackResult(False, None, "", f"{tool_name} not found in PATH")
            else:
                self._crack_proc = proc
                res = self._stream_and_collect(proc, active_tool, hc)
        except Exception as exc:
            self.state.log(f"[crack] error: {exc}")
            res = crack_mod.CrackResult(False, None, "", str(exc))
        finally:
            self._crack_proc = None
            self._phase = _IDLE

        self._result = res
        if res.success and res.password:
            essid = self._selected_cap["essid"]
            entry = passwords.PasswordEntry(
                ssid=essid, password=res.password, capture_file=str(cap)
            )
            passwords.append(self.state.paths.found_passwords, entry)
            passwords.write_per_network(self.state.paths.essid_dir(essid), entry)
            self.state.log(f"[crack] KEY FOUND: {res.password}")
        else:
            self.state.log("[crack] key not in wordlist")

        try:
            self.app.call_from_thread(self._do_refresh)
        except Exception:
            pass

    def _popen_hashcat(self, hc: Path, wl: Path) -> subprocess.Popen | None:
        cmd = [
            "hashcat", "-m", "22000", "-a", "0",
            "--status", "--status-timer=2",
            str(hc), str(wl),
        ]
        try:
            return subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
        except FileNotFoundError:
            return None

    def _popen_aircrack(self, cap: Path, wl: Path, bssid: str | None) -> subprocess.Popen | None:
        cmd = ["aircrack-ng", "-w", str(wl)]
        if bssid:
            cmd += ["-b", bssid]
        cmd.append(str(cap))
        try:
            return subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
        except FileNotFoundError:
            return None

    def _stream_and_collect(
        self, proc: subprocess.Popen, tool: str, hc: Path | None
    ) -> crack_mod.CrackResult:
        all_lines: list[str] = []
        last_refresh = time.time()
        try:
            for raw in proc.stdout:
                if self._phase != _RUNNING:
                    break
                line = raw.rstrip()
                all_lines.append(line)
                self._crack_lines.append(line)
                now = time.time()
                if now - last_refresh >= _REFRESH_RATE:
                    last_refresh = now
                    try:
                        self.app.call_from_thread(self._do_refresh)
                    except Exception:
                        pass
        except Exception:
            pass

        proc.wait()
        full_out = "\n".join(all_lines)

        if tool == "hashcat":
            try:
                show = subprocess.run(
                    ["hashcat", "-m", "22000", "--show", str(hc)],
                    capture_output=True, text=True, check=False,
                )
                for line in show.stdout.splitlines():
                    line = line.strip()
                    if ":" in line:
                        pw = line.rsplit(":", 1)[-1]
                        if pw:
                            return crack_mod.CrackResult(True, pw, full_out, "")
            except Exception:
                pass
            return crack_mod.CrackResult(False, None, full_out, "")
        else:
            pw = None
            for line in all_lines:
                m = crack_mod.KEY_RE.search(line)
                if m:
                    pw = m.group("pw")
                    break
            return crack_mod.CrackResult(
                success=bool(pw), password=pw, stdout=full_out, stderr=""
            )
