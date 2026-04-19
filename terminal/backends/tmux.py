"""tmux backend: a detached session with a horizontal split.

Works equally well in a desktop terminal, on an SSH pipe and on
NetHunter / Termux where graphical terminals are not available.
"""
from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import time
from typing import Callable

from ..detect import Environment
from ..launcher import Command


SESSION_NAME = "snype-dual"


def run(left: Command, right: Command, env: Environment, log: Callable[[str], None]) -> tuple[bool, str]:
    if not shutil.which("tmux"):
        return False, "tmux not found in PATH"

    subprocess.run(["tmux", "kill-session", "-t", SESSION_NAME],
                   capture_output=True, check=False)

    left_cmd = _wrap_hold(list(left.argv), hold=left.hold_on_exit)
    right_cmd = _wrap_hold(list(right.argv), hold=right.hold_on_exit)

    log(f"[tmux] new-session -d -s {SESSION_NAME}")
    subprocess.run(
        ["tmux", "new-session", "-d", "-s", SESSION_NAME, "-n", left.title or "monitor",
         "bash", "-lc", left_cmd],
        check=True,
    )
    subprocess.run(
        ["tmux", "split-window", "-h", "-t", f"{SESSION_NAME}:0",
         "bash", "-lc", right_cmd],
        check=True,
    )
    subprocess.run(
        ["tmux", "select-pane", "-t", f"{SESSION_NAME}:0.0"],
        capture_output=True, check=False,
    )

    if env.inside_tmux:
        msg = (
            f"[snype] dual panes running in tmux session '{SESSION_NAME}'. "
            f"Run 'tmux switch-client -t {SESSION_NAME}' to jump in."
        )
        log(msg)
        _wait_for_session_end(SESSION_NAME, log)
        return True, msg

    log(f"[tmux] attach -t {SESSION_NAME}")
    try:
        subprocess.run(["tmux", "attach-session", "-t", SESSION_NAME], check=False)
    except KeyboardInterrupt:
        pass

    subprocess.run(["tmux", "kill-session", "-t", SESSION_NAME],
                   capture_output=True, check=False)
    return True, f"tmux session '{SESSION_NAME}' closed"


def _wait_for_session_end(name: str, log: Callable[[str], None]) -> None:
    while True:
        r = subprocess.run(["tmux", "has-session", "-t", name],
                           capture_output=True, check=False)
        if r.returncode != 0:
            break
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            subprocess.run(["tmux", "kill-session", "-t", name],
                           capture_output=True, check=False)
            break


def _wrap_hold(argv: list[str], hold: bool) -> str:
    quoted = " ".join(shlex.quote(a) for a in argv)
    if not hold:
        return quoted
    return f"{quoted}; echo; echo '[snype] process exited. Press Enter to close pane.'; read _"
