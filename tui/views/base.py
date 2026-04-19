"""Base class shared by every view widget."""
from __future__ import annotations

import threading
from rich.console import RenderableType
from textual.widget import Widget
from textual.widgets import Static

from ..state import AppState


class ViewWidget(Widget):
    """Base for all view panes.

    Subclasses override ``_render()`` to return a Rich renderable.
    State changes automatically re-render the content via a ``Static`` child.
    """

    can_focus = True

    def __init__(self, state: AppState, **kwargs) -> None:
        super().__init__(**kwargs)
        self.state = state

    def compose(self):
        yield Static(self._build(), id="content", expand=True)

    def on_mount(self) -> None:
        self.state.subscribe(self._on_state_change)

    def on_show(self) -> None:
        """Focus this view when ContentSwitcher makes it visible."""
        self.focus()

    def _on_state_change(self) -> None:
        """Called from any thread when AppState changes."""
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

    def _build(self) -> RenderableType:
        raise NotImplementedError
