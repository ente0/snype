"""Persistence layer for recovered passwords."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

from .paths import (
    Paths,
    _contained_path,
    ensure_application_root,
    ensure_private_directory,
    private_text_open,
)


@dataclass
class PasswordEntry:
    ssid: str
    password: str
    capture_file: str | None = None
    date_cracked: str | None = None


def load_all(path: Path) -> list[PasswordEntry]:
    if not path.exists():
        return []
    entries: list[PasswordEntry] = []
    with private_text_open(path, "r", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(data, dict):
                continue
            entries.append(
                PasswordEntry(
                    ssid=data.get("ssid", ""),
                    password=data.get("password", ""),
                    capture_file=data.get("capture_file"),
                    date_cracked=data.get("date_cracked"),
                )
            )
    return entries


def append(path: Path, entry: PasswordEntry) -> None:
    ensure_application_root(path.parent)
    if not entry.date_cracked:
        entry.date_cracked = time.strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "ssid": entry.ssid,
        "password": entry.password,
        "capture_file": entry.capture_file,
        "date_cracked": entry.date_cracked,
    }
    with private_text_open(path, "a") as fp:
        fp.write(json.dumps(payload) + "\n")


def credential_filename(ssid: str) -> str:
    """Return a deterministic opaque filename for the exact ESSID string."""
    digest = hashlib.sha256(ssid.encode("utf-8", errors="surrogatepass")).hexdigest()
    return f"network-{digest}_password.txt"


def write_per_network(paths: Paths, entry: PasswordEntry) -> Path:
    essid_dir = paths.essid_dir(entry.ssid)
    passwords_dir = essid_dir / "passwords"
    ensure_private_directory(passwords_dir)
    out = _contained_path(
        passwords_dir, passwords_dir / credential_filename(entry.ssid)
    )
    content = (
        f"Network: {entry.ssid}\n"
        f"Password: {entry.password}\n"
        f"Capture file: {entry.capture_file or ''}\n"
        f"Date cracked: {entry.date_cracked}\n"
    )
    with private_text_open(out, "w") as handle:
        handle.write(content)
    return out
