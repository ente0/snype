"""Textual TUI for snype.

``run_tui`` is intentionally *not* re-exported here — importing it pulls
textual, and several unit tests import sub-modules (``tui.state``)
without needing the full UI. Import it explicitly:

    from tui.application import run_tui
"""
