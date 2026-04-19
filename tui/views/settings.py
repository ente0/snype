"""Settings view: interfaces and terminal backend."""
from __future__ import annotations

import subprocess

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

from .base import ViewWidget
from ..state import AppState
from core import interfaces


class InputModal(ModalScreen[str | None]):
    """Simple text-input modal that returns the entered value (or None on cancel)."""

    CSS = """
    InputModal {
        align: center middle;
    }
    #dialog {
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }
    #dialog Label {
        margin-bottom: 1;
    }
    #dialog Horizontal {
        margin-top: 1;
        height: auto;
    }
    #dialog Button {
        margin-right: 1;
    }
    """

    def __init__(self, title: str, placeholder: str = "") -> None:
        super().__init__()
        self._title = title
        self._placeholder = placeholder

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label(self._title)
            yield Input(placeholder=self._placeholder, id="input")
            with Horizontal():
                yield Button("OK", variant="primary", id="ok")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.dismiss(self.query_one("#input", Input).value or None)
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value or None)


class SettingsView(ViewWidget):
    BINDINGS = [
        Binding("1", "set_monitor_iface", "Monitor iface", show=False),
        Binding("2", "set_inject_iface", "Inject iface", show=False),
        Binding("3", "cycle_term", "Term mode", show=False),
        Binding("f", "flush_services", "Flush", show=False),
    ]

    def _build(self):
        cfg = self.state.config
        grid = Table.grid(padding=(0, 2))
        grid.add_column(style="dim cyan", justify="right")
        grid.add_column(style="white")
        grid.add_row("[1] monitor iface", cfg.monitor_iface or "—")
        grid.add_row("[2] inject iface", cfg.inject_iface or "—")
        grid.add_row("[3] term mode", self.state.term_mode)
        grid.add_row("[f] flush services", "kill monitor-mode interferers, reset to managed")

        avail = Table(title="detected wireless interfaces", box=None)
        avail.add_column("name", style="yellow")
        for name in interfaces.list_wireless():
            avail.add_row(name)
        if not avail.row_count:
            avail.add_row(Text("no wireless interfaces detected", style="red"))

        return Panel(Group(grid, Text(""), avail), title="settings", border_style="blue")

    def action_set_monitor_iface(self) -> None:
        def _handle(result: str | None) -> None:
            if not result:
                return
            self.state.config.monitor_iface = result.strip()
            if not self.state.config.inject_iface:
                self.state.config.inject_iface = self.state.config.monitor_iface
            self.state.save_config()
            self.state.log(f"[settings] monitor iface -> {result.strip()}")

        self.app.push_screen(
            InputModal("Monitor interface", "e.g. wlan0mon"), _handle
        )

    def action_set_inject_iface(self) -> None:
        def _handle(result: str | None) -> None:
            if not result:
                return
            self.state.config.inject_iface = result.strip()
            self.state.save_config()
            self.state.log(f"[settings] inject iface -> {result.strip()}")

        self.app.push_screen(
            InputModal("Inject interface", "e.g. wlan1"), _handle
        )

    def action_cycle_term(self) -> None:
        order = ["auto", "xterm", "tmux", "pty"]
        try:
            idx = order.index(self.state.term_mode)
        except ValueError:
            idx = -1
        self.state.term_mode = order[(idx + 1) % len(order)]
        self.state.config.term_mode = self.state.term_mode
        self.state.save_config()
        self.state.log(f"[settings] term mode -> {self.state.term_mode}")

    def action_flush_services(self) -> None:
        subprocess.run(
            ["sudo", "airmon-ng", "check", "kill"], capture_output=True, check=False
        )
        cfg = self.state.config
        if cfg.monitor_iface:
            interfaces.set_mode(cfg.monitor_iface, "managed")
        if cfg.inject_iface and cfg.inject_iface != cfg.monitor_iface:
            interfaces.set_mode(cfg.inject_iface, "managed")
        interfaces.restart_network_services()
        self.state.log("[settings] services flushed")
