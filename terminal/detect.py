"""Environment detection for the dual-terminal launcher.

Priority (auto mode, as agreed): xterm > tmux > PTY. NetHunter / Termux
is detected first and forces tmux because graphical terminal emulators
are rarely available there.
"""
from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from enum import Enum


class Backend(str, Enum):
    XTERM = "xterm"
    TMUX = "tmux"
    PTY = "pty"


@dataclass(frozen=True)
class Environment:
    is_nethunter: bool
    is_termux: bool
    has_display: bool
    has_tmux_binary: bool
    inside_tmux: bool
    gui_term: str | None   # xterm | kitty | gnome-terminal | konsole | None
    is_tty: bool


GUI_TERM_CANDIDATES = ("xterm", "kitty", "gnome-terminal", "konsole", "alacritty", "terminator")


def detect() -> Environment:
    env = os.environ
    termux = bool(env.get("TERMUX_VERSION")) or os.path.isdir("/data/data/com.termux")
    nethunter = (
        os.path.isdir("/data/data/com.offsec.nethunter")
        or os.path.isdir("/data/data/com.offsec.nhterm")
        or "kali" in (env.get("CHROOT") or "").lower()
    )
    has_display = bool(env.get("DISPLAY") or env.get("WAYLAND_DISPLAY"))
    has_tmux = shutil.which("tmux") is not None
    inside_tmux = bool(env.get("TMUX"))
    gui_term = None
    if has_display:
        for cand in GUI_TERM_CANDIDATES:
            if shutil.which(cand):
                gui_term = cand
                break
    return Environment(
        is_nethunter=nethunter,
        is_termux=termux,
        has_display=has_display,
        has_tmux_binary=has_tmux,
        inside_tmux=inside_tmux,
        gui_term=gui_term,
        is_tty=sys.stdout.isatty(),
    )


def pick_mode(env: Environment, requested: str = "auto") -> Backend:
    """Resolve a concrete backend from a user request and the detected env."""
    req = (requested or "auto").lower()
    if req in {"xterm", "tmux", "pty"}:
        return Backend(req)

    # NetHunter / Termux -> tmux preferred.
    if env.is_nethunter or env.is_termux:
        if env.has_tmux_binary:
            return Backend.TMUX
        return Backend.PTY

    # xterm > tmux > PTY on a desktop session.
    if env.has_display and env.gui_term:
        return Backend.XTERM
    if env.has_tmux_binary:
        return Backend.TMUX
    return Backend.PTY
