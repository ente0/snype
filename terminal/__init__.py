"""Dual-terminal dispatch: detect environment, pick a backend, launch panes."""

from .detect import Environment, detect, pick_mode
from .launcher import Command, LaunchResult, launch_dual_pane

__all__ = [
    "Environment",
    "detect",
    "pick_mode",
    "Command",
    "LaunchResult",
    "launch_dual_pane",
]
