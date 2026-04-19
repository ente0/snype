"""PTY fallback: run both commands in a single terminal via a multiplexed view.

When neither xterm nor tmux are available (or the user forces ``--term-mode pty``),
this backend spawns both children under a pseudo-terminal and streams their
combined output to stdout with prefixed lines.

If the TUI is active, the ``TerminalPane`` widget in ``tui.widgets.term_pane``
can consume the same ``PtyProcess`` instances to render two split panes inside
the app window.
"""
from __future__ import annotations

import os
import pty
import select
import signal
import sys
import threading
from dataclasses import dataclass
from typing import Callable, Sequence

from ..detect import Environment
from ..launcher import Command


@dataclass
class PtyProcess:
    pid: int
    fd: int
    title: str

    def close(self) -> None:
        try:
            os.kill(self.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            os.close(self.fd)
        except OSError:
            pass

    def read_ready(self, timeout: float = 0.1) -> bytes:
        try:
            r, _, _ = select.select([self.fd], [], [], timeout)
            if self.fd in r:
                return os.read(self.fd, 4096)
        except OSError:
            return b""
        return b""


def spawn(argv: Sequence[str], title: str = "") -> PtyProcess:
    """Spawn ``argv`` under a fresh PTY. Returns a ``PtyProcess``."""
    pid, fd = pty.fork()
    if pid == 0:
        os.execvp(argv[0], list(argv))
    return PtyProcess(pid=pid, fd=fd, title=title)


def run(left: Command, right: Command, env: Environment, log: Callable[[str], None]) -> tuple[bool, str]:
    log("[pty] no tmux/xterm available, streaming both commands in-place")

    procs = (
        spawn(list(left.argv), title=left.title or "left"),
        spawn(list(right.argv), title=right.title or "right"),
    )

    stop = threading.Event()

    def relay(proc: PtyProcess, prefix: str) -> None:
        while not stop.is_set():
            data = proc.read_ready(0.2)
            if not data:
                try:
                    done_pid, _ = os.waitpid(proc.pid, os.WNOHANG)
                    if done_pid == proc.pid:
                        return
                except ChildProcessError:
                    return
                continue
            text = data.decode("utf-8", errors="replace")
            for line in text.splitlines(keepends=False):
                sys.stdout.write(f"[{prefix}] {line}\n")
            sys.stdout.flush()

    threads = [
        threading.Thread(target=relay, args=(procs[0], left.title or "L"), daemon=True),
        threading.Thread(target=relay, args=(procs[1], right.title or "R"), daemon=True),
    ]
    for t in threads:
        t.start()
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        stop.set()
    finally:
        for p in procs:
            p.close()
    return True, "pty panes closed"
