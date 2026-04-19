"""Persistence layer for recovered passwords."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path


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
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        entries.append(PasswordEntry(
            ssid=data.get("ssid", ""),
            password=data.get("password", ""),
            capture_file=data.get("capture_file"),
            date_cracked=data.get("date_cracked"),
        ))
    return entries


def append(path: Path, entry: PasswordEntry) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not entry.date_cracked:
        entry.date_cracked = time.strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "ssid": entry.ssid,
        "password": entry.password,
        "capture_file": entry.capture_file,
        "date_cracked": entry.date_cracked,
    }
    with path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload) + "\n")


def write_per_network(essid_dir: Path, entry: PasswordEntry) -> Path:
    passwords_dir = essid_dir / "passwords"
    passwords_dir.mkdir(parents=True, exist_ok=True)
    out = passwords_dir / f"{entry.ssid}_password.txt"
    out.write_text(
        f"Network: {entry.ssid}\n"
        f"Password: {entry.password}\n"
        f"Capture file: {entry.capture_file or ''}\n"
        f"Date cracked: {entry.date_cracked}\n",
        encoding="utf-8",
    )
    return out
