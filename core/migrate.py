"""One-shot migration from the legacy flat layout.

Moves:
  - ``handshakes/``          -> ``snype-data/hs/``
  - ``interface_config.txt`` -> entries in ``config.json``
  - ``selected_network.txt`` -> ``target`` in ``config.json``
  - ``found_passwords.txt``  -> ``snype-data/found_passwords.jsonl``

No data is deleted; files are only relocated. Idempotent: once the
target layout exists, subsequent runs are a no-op.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from .config import Config, Target
from .paths import Paths


LEGACY_HANDSHAKES = Path("handshakes")
LEGACY_IFACE_FILE = Path("interface_config.txt")
LEGACY_NETWORK_FILE = Path("selected_network.txt")
LEGACY_FOUND_PASSWORDS = Path("found_passwords.txt")


def run(paths: Paths, verbose: bool = False) -> list[str]:
    """Execute the migration. Returns a human-readable list of actions."""
    actions: list[str] = []
    paths.ensure()

    actions += _migrate_handshakes(paths)
    cfg = Config.load(paths.config)
    actions += _migrate_interfaces(cfg)
    actions += _migrate_target(cfg)
    if any(entry.startswith("[cfg]") for entry in actions):
        cfg.save(paths.config)
    actions += _migrate_found_passwords(paths)

    return actions


def _migrate_handshakes(paths: Paths) -> list[str]:
    if not LEGACY_HANDSHAKES.exists() or not LEGACY_HANDSHAKES.is_dir():
        return []
    if any(paths.hs.iterdir()):
        # Target already populated: merge by moving missing entries.
        moved = []
        for entry in LEGACY_HANDSHAKES.iterdir():
            dest = paths.hs / entry.name
            if dest.exists():
                continue
            shutil.move(str(entry), str(dest))
            moved.append(f"[hs]  merged {entry.name}")
        if not any(LEGACY_HANDSHAKES.iterdir()):
            LEGACY_HANDSHAKES.rmdir()
        return moved
    shutil.rmtree(paths.hs, ignore_errors=True)
    shutil.move(str(LEGACY_HANDSHAKES), str(paths.hs))
    return [f"[hs]  moved handshakes/ -> {paths.hs}"]


def _migrate_interfaces(cfg: Config) -> list[str]:
    if not LEGACY_IFACE_FILE.exists() or cfg.monitor_iface:
        return []
    try:
        raw = LEGACY_IFACE_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return []
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if not parts:
        LEGACY_IFACE_FILE.unlink(missing_ok=True)
        return []
    cfg.monitor_iface = parts[0]
    cfg.inject_iface = parts[1] if len(parts) > 1 else parts[0]
    LEGACY_IFACE_FILE.unlink(missing_ok=True)
    return [f"[cfg] imported interfaces: {cfg.monitor_iface} / {cfg.inject_iface}"]


def _migrate_target(cfg: Config) -> list[str]:
    if not LEGACY_NETWORK_FILE.exists() or cfg.has_target():
        return []
    try:
        raw = LEGACY_NETWORK_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return []
    parts = [p.strip() for p in raw.split(",")]
    if not parts or ":" not in parts[0]:
        LEGACY_NETWORK_FILE.unlink(missing_ok=True)
        return []
    cfg.target = Target(
        bssid=parts[0],
        channel=parts[1] if len(parts) > 1 else None,
        essid=parts[2] if len(parts) > 2 else None,
    )
    LEGACY_NETWORK_FILE.unlink(missing_ok=True)
    return [f"[cfg] imported target: {cfg.target.bssid}"]


def _migrate_found_passwords(paths: Paths) -> list[str]:
    if not LEGACY_FOUND_PASSWORDS.exists():
        return []
    actions: list[str] = []
    with LEGACY_FOUND_PASSWORDS.open("r", encoding="utf-8") as src:
        with paths.found_passwords.open("a", encoding="utf-8") as dst:
            for line in src:
                line = line.strip()
                if not line:
                    continue
                try:
                    json.loads(line)
                    dst.write(line + "\n")
                    continue
                except json.JSONDecodeError:
                    pass
                if ":" in line:
                    ssid, password = line.split(":", 1)
                    dst.write(json.dumps({"ssid": ssid, "password": password}) + "\n")
    LEGACY_FOUND_PASSWORDS.unlink(missing_ok=True)
    actions.append(f"[pwd] imported found_passwords.txt -> {paths.found_passwords.name}")
    return actions
