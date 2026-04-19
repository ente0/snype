#!/usr/bin/env python3
"""snype entry point.

This file stays as the user-facing launcher (``python3 snype.py``) per
the legacy invocation style. All the logic lives under ``cli``, ``core``,
``terminal`` and ``tui``.
"""
from __future__ import annotations

import sys

from cli import bootstrap


if __name__ == "__main__":
    sys.exit(bootstrap())
