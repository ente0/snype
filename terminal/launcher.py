"""Public launcher API: pick a backend and run two panes concurrently."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Sequence

from .detect import Backend, Environment, detect, pick_mode


@dataclass
class Command:
    argv: Sequence[str]
    title: str = ""
    hold_on_exit: bool = True
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class LaunchResult:
    backend: Backend
    success: bool
    message: str = ""


def launch_dual_pane(
    left: Command,
    right: Command,
    mode: str = "auto",
    env: Environment | None = None,
    log: Callable[[str], None] | None = None,
) -> LaunchResult:
    """Open two panes, one per ``Command``. Blocks until both exit.

    ``mode`` accepts ``auto``, ``xterm``, ``tmux``, ``pty``.
    """
    environment = env or detect()
    backend = pick_mode(environment, mode)
    logger = log or (lambda _: None)
    logger(f"[launcher] environment={environment}")
    logger(f"[launcher] selected backend={backend.value}")

    if backend is Backend.XTERM:
        from .backends import xterm as impl
    elif backend is Backend.TMUX:
        from .backends import tmux as impl
    else:
        from .backends import pty_embed as impl

    try:
        ok, msg = impl.run(left, right, environment, logger)
    except Exception as exc:
        return LaunchResult(backend=backend, success=False, message=f"{type(exc).__name__}: {exc}")
    return LaunchResult(backend=backend, success=ok, message=msg)
