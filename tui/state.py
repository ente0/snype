"""Shared mutable state for the TUI.

Single instance passed to every view. Emits a change event so widgets
can refresh their rendering without hunting for the data themselves.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List

from core.config import Config
from core.paths import Paths


@dataclass
class AppState:
    paths: Paths
    config: Config
    term_mode: str = "auto"
    dry_run: bool = False
    verbose: bool = False
    log_tail: List[str] = field(default_factory=list)
    _listeners: List[Callable[[], None]] = field(default_factory=list, repr=False)

    def log(self, line: str) -> None:
        self.log_tail.append(line)
        if len(self.log_tail) > 200:
            del self.log_tail[: len(self.log_tail) - 200]
        self._fire()

    def notify(self) -> None:
        self._fire()

    def subscribe(self, cb: Callable[[], None]) -> None:
        self._listeners.append(cb)

    def _fire(self) -> None:
        for cb in list(self._listeners):
            try:
                cb()
            except Exception:
                pass

    def save_config(self) -> None:
        self.config.save(self.paths.config)
        self._fire()

    def last_log(self, n: int = 1) -> str:
        return " · ".join(self.log_tail[-n:]) if self.log_tail else ""

    def found_passwords_path(self) -> Path:
        return self.paths.found_passwords
