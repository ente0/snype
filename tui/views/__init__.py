"""View widgets consumed by tui.application.

Each view is a ``ViewWidget`` subclass (``textual.widget.Widget``) that
overrides ``_render()`` to return a Rich renderable.  The application
mounts all views inside a ``ContentSwitcher`` and exposes them by ``id``.
"""

from .welcome import WelcomeView
from .scan import ScanView
from .monitor import MonitorView
from .deauth import DeauthView
from .crack import CrackView
from .files import FilesView
from .settings import SettingsView
from .help_view import HelpView

__all__ = [
    "WelcomeView",
    "ScanView",
    "MonitorView",
    "DeauthView",
    "CrackView",
    "FilesView",
    "SettingsView",
    "HelpView",
]
