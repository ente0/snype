"""Centralised filesystem layout for snype.

All artefacts live under a single portable root. The default is
``./snype-data/`` next to the project. Override with the env var
``SNYPE_DATA_DIR`` or with the CLI flag ``--data-dir``.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_ROOT_NAME = "snype-data"
HS_DIR_NAME = "hs"
LOGS_DIR_NAME = "logs"
CONFIG_FILE_NAME = "config.json"
FOUND_PASSWORDS_FILE = "found_passwords.jsonl"


@dataclass(frozen=True)
class Paths:
    root: Path
    hs: Path
    logs: Path
    config: Path
    found_passwords: Path

    def ensure(self) -> "Paths":
        self.root.mkdir(parents=True, exist_ok=True)
        self.hs.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)
        return self

    def session_dir(self, essid: str, timestamp: str) -> Path:
        safe = _safe_component(essid) or "unknown"
        path = self.hs / safe / timestamp
        path.mkdir(parents=True, exist_ok=True)
        return path

    def essid_dir(self, essid: str) -> Path:
        safe = _safe_component(essid) or "unknown"
        path = self.hs / safe
        path.mkdir(parents=True, exist_ok=True)
        return path


def _safe_component(name: str) -> str:
    return "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in name).strip("_")


def resolve_root(cli_override: str | None = None) -> Path:
    if cli_override:
        return Path(cli_override).expanduser().resolve()
    env = os.environ.get("SNYPE_DATA_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return (Path.cwd() / DEFAULT_ROOT_NAME).resolve()


def build_paths(cli_override: str | None = None) -> Paths:
    root = resolve_root(cli_override)
    return Paths(
        root=root,
        hs=root / HS_DIR_NAME,
        logs=root / LOGS_DIR_NAME,
        config=root / CONFIG_FILE_NAME,
        found_passwords=root / FOUND_PASSWORDS_FILE,
    )
