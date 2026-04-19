"""xterm-compatible GUI terminal backend.

Spawns two terminal windows (one per Command). Supports xterm, kitty,
gnome-terminal, konsole, alacritty and terminator through a small
adapter. Blocks until both children exit.
"""
from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from typing import Callable

from ..detect import Environment
from ..launcher import Command


def run(left: Command, right: Command, env: Environment, log: Callable[[str], None]) -> tuple[bool, str]:
    term = env.gui_term
    if not term:
        for cand in ("xterm", "kitty", "gnome-terminal", "konsole", "alacritty", "terminator"):
            if shutil.which(cand):
                term = cand
                break
    if not term:
        return False, "no GUI terminal emulator found in PATH"

    log(f"[xterm] using {term}")
    children = [
        _spawn(term, left, "left"),
        _spawn(term, right, "right"),
    ]
    for proc in children:
        try:
            proc.wait()
        except KeyboardInterrupt:
            for p in children:
                if p.poll() is None:
                    p.terminate()
            break
    return True, f"launched via {term}"


def _spawn(term: str, cmd: Command, side: str) -> subprocess.Popen:
    inner = _wrap_hold(list(cmd.argv), hold=cmd.hold_on_exit)
    title = cmd.title or side
    env = {**os.environ, **cmd.env}

    if term == "xterm":
        argv = ["xterm", "-T", title, "-fa", "Monospace", "-fs", "11",
                "-e", "bash", "-lc", inner]
    elif term == "kitty":
        argv = ["kitty", "--title", title, "bash", "-lc", inner]
    elif term == "gnome-terminal":
        argv = ["gnome-terminal", "--title", title, "--", "bash", "-lc", inner]
    elif term == "konsole":
        argv = ["konsole", "-p", f"tabtitle={title}", "-e", "bash", "-lc", inner]
    elif term == "alacritty":
        argv = ["alacritty", "-t", title, "-e", "bash", "-lc", inner]
    elif term == "terminator":
        argv = ["terminator", "-T", title, "-x", "bash", "-lc", inner]
    else:
        argv = [term, "-e", "bash", "-lc", inner]

    return subprocess.Popen(argv, env=env)


def _wrap_hold(argv: list[str], hold: bool) -> str:
    quoted = " ".join(shlex.quote(a) for a in argv)
    if not hold:
        return quoted
    return f"{quoted}; echo; echo '[snype] process exited. Press Enter to close.'; read _"
