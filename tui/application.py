"""TUI entry point: Textual application."""
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import ContentSwitcher

from .state import AppState
from .widgets.footer import FooterBar
from .widgets.sidebar import SidebarWidget
from .widgets.status_bar import StatusBarWidget
from .views.welcome import WelcomeView
from .views.scan import ScanView
from .views.monitor import MonitorView
from .views.deauth import DeauthView
from .views.crack import CrackView
from .views.files import FilesView
from .views.settings import SettingsView
from .views.help_view import HelpView


class SnypeApp(App):
    CSS = """
    StatusBarWidget {
        dock: top;
        height: 1;
        background: #1e1e2e;
        color: #cdd6f4;
    }
    FooterBar {
        dock: bottom;
        height: 1;
        background: #1e1e2e;
        color: #cdd6f4;
    }
    #body {
        height: 1fr;
    }
    SidebarWidget {
        width: 22;
        background: #11111b;
        border-right: solid #313244;
    }
    ContentSwitcher {
        width: 1fr;
    }
    ContentSwitcher > * {
        width: 1fr;
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("s", "switch_view('scan')", "Scan", show=False),
        Binding("m", "switch_view('monitor')", "Monitor", show=False),
        Binding("d", "switch_view('deauth')", "Deauth", show=False),
        Binding("c", "switch_view('crack')", "Crack", show=False),
        Binding("f", "switch_view('files')", "Files", show=False),
        Binding("t", "switch_view('settings')", "Settings", show=False),
        Binding("question_mark", "switch_view('help')", "Help", show=False),
        Binding("h", "switch_view('welcome')", "Home", show=False),
        Binding("q", "quit", "Quit", show=False),
    ]

    active_view: reactive[str] = reactive("welcome")

    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield StatusBarWidget(self.state)
        with Horizontal(id="body"):
            yield SidebarWidget(id="sidebar")
            with ContentSwitcher(initial="welcome"):
                yield WelcomeView(self.state, id="welcome")
                yield ScanView(self.state, id="scan")
                yield MonitorView(self.state, id="monitor")
                yield DeauthView(self.state, id="deauth")
                yield CrackView(self.state, id="crack")
                yield FilesView(self.state, id="files")
                yield SettingsView(self.state, id="settings")
                yield HelpView(self.state, id="help")
        yield FooterBar(self.state)

    def watch_active_view(self, view_id: str) -> None:
        self.query_one(ContentSwitcher).current = view_id
        self.query_one(SidebarWidget).active_view_id = view_id
        try:
            self.query_one(f"#{view_id}").focus()
        except Exception:
            pass

    def action_switch_view(self, view_id: str) -> None:
        self.active_view = view_id


def _restore_managed_mode(state: AppState) -> None:
    iface = state.config.monitor_iface
    if not iface:
        return
    from core.interfaces import get_mode, disable_monitor_mode
    try:
        if get_mode(iface) == "monitor":
            disable_monitor_mode(iface)
    except Exception:
        pass


def run_tui(state: AppState) -> None:
    try:
        SnypeApp(state).run()
    finally:
        _restore_managed_mode(state)
