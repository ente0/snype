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
import os
import shutil
import stat
from pathlib import Path

from . import passwords
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
    paths.ensure()

    return actions


def _migrate_handshakes(paths: Paths) -> list[str]:
    if not _validate_legacy_directory(LEGACY_HANDSHAKES):
        return []
    # Keep the already validated private destination directory in place and
    # relocate only ordinary, non-symlink entries from the legacy tree.
    moved = []
    for entry in LEGACY_HANDSHAKES.iterdir():
        dest = paths.hs / entry.name
        if dest.exists() or dest.is_symlink():
            continue
        shutil.move(str(entry), str(dest))
        _harden_private_tree(dest)
        moved.append(f"[hs]  merged {entry.name}")
    if not any(LEGACY_HANDSHAKES.iterdir()):
        LEGACY_HANDSHAKES.rmdir()
    return moved


def _harden_private_tree(path: Path) -> None:
    """Apply private modes to a validated migrated capture tree."""
    info = path.lstat()
    if stat.S_ISREG(info.st_mode):
        if os.name == "posix":
            path.chmod(0o600)
        return
    if not stat.S_ISDIR(info.st_mode):
        raise RuntimeError(f"Refusing special migrated path: {path}")
    if os.name == "posix":
        path.chmod(0o700)
    for child in path.iterdir():
        if child.is_symlink():
            raise RuntimeError(f"Refusing symlink in migrated capture tree: {child}")
        _harden_private_tree(child)


def _validate_legacy_directory(path: Path) -> bool:
    """Reject symlinks and special files before privileged migration."""
    if path.is_symlink():
        raise RuntimeError(f"Refusing symlinked legacy directory: {path}")
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    if not stat.S_ISDIR(info.st_mode):
        return False
    for current, directories, files in os.walk(path, followlinks=False):
        for name in (*directories, *files):
            entry = Path(current) / name
            entry_info = entry.lstat()
            if stat.S_ISLNK(entry_info.st_mode):
                raise RuntimeError(f"Refusing symlink in legacy handshakes: {entry}")
            if not (
                stat.S_ISDIR(entry_info.st_mode) or stat.S_ISREG(entry_info.st_mode)
            ):
                raise RuntimeError(
                    f"Refusing special file in legacy handshakes: {entry}"
                )
    return True


def _legacy_regular_file(path: Path) -> bool:
    if path.is_symlink():
        raise RuntimeError(f"Refusing symlinked legacy file: {path}")
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    if not stat.S_ISREG(info.st_mode):
        raise RuntimeError(f"Refusing non-regular legacy file: {path}")
    return True


def _migrate_interfaces(cfg: Config) -> list[str]:
    if not _legacy_regular_file(LEGACY_IFACE_FILE) or cfg.monitor_iface:
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
    if not _legacy_regular_file(LEGACY_NETWORK_FILE) or cfg.has_target():
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
    if not _legacy_regular_file(LEGACY_FOUND_PASSWORDS):
        return []
    actions: list[str] = []
    with LEGACY_FOUND_PASSWORDS.open("r", encoding="utf-8") as src:
        for line in src:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                if ":" not in line:
                    continue
                ssid, password = line.split(":", 1)
                data = {"ssid": ssid, "password": password}
            if not isinstance(data, dict):
                continue
            passwords.append(
                paths.found_passwords,
                passwords.PasswordEntry(
                    ssid=str(data.get("ssid", "")),
                    password=str(data.get("password", "")),
                    capture_file=data.get("capture_file"),
                    date_cracked=data.get("date_cracked"),
                ),
            )
    LEGACY_FOUND_PASSWORDS.unlink(missing_ok=True)
    actions.append(
        f"[pwd] imported found_passwords.txt -> {paths.found_passwords.name}"
    )
    return actions
