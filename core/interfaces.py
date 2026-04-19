"""Wireless-interface discovery, mode detection and monitor-mode management."""
from __future__ import annotations

import re
import subprocess


def list_wireless() -> list[str]:
    """Return the list of interfaces reported by ``iw dev``."""
    try:
        proc = subprocess.run(["iw", "dev"], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return _fallback_iwconfig()
    interfaces: list[str] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("Interface "):
            interfaces.append(line.split(None, 1)[1])
    return interfaces


def _fallback_iwconfig() -> list[str]:
    try:
        proc = subprocess.run(["iwconfig"], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return []
    interfaces: list[str] = []
    for line in proc.stdout.splitlines():
        if not line or line.startswith(" "):
            continue
        name = line.split()[0]
        if "no wireless" not in line.lower():
            interfaces.append(name)
    return interfaces


def exists(name: str) -> bool:
    try:
        proc = subprocess.run(
            ["iwconfig", name],
            capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        return False
    return proc.returncode == 0 and "no such device" not in proc.stderr.lower()


def get_mode(name: str) -> str | None:
    """Return the current mode of *name* (``'monitor'``, ``'managed'``, …) or ``None``.

    Tries ``iw dev info`` first, falls back to ``iwconfig``.
    """
    try:
        proc = subprocess.run(
            ["iw", "dev", name, "info"],
            capture_output=True, text=True, check=False,
        )
        for line in proc.stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith("type "):
                return stripped.split(None, 1)[1].lower()
    except FileNotFoundError:
        pass

    # fallback: iwconfig
    try:
        proc = subprocess.run(
            ["iwconfig", name],
            capture_output=True, text=True, check=False,
        )
        for line in proc.stdout.splitlines():
            if "Mode:" in line:
                return line.split("Mode:")[1].split()[0].lower()
    except FileNotFoundError:
        pass

    return None


def enable_monitor_mode(name: str) -> str:
    """Enable monitor mode on *name* via ``airmon-ng start``.

    Returns the name of the resulting monitor interface (may differ from
    *name*, e.g. ``wlan0`` → ``wlan0mon``).

    Raises ``RuntimeError`` if monitor mode could not be confirmed.
    """
    proc = subprocess.run(
        ["sudo", "airmon-ng", "start", name],
        capture_output=True, text=True, check=False,
    )
    output = proc.stdout + proc.stderr

    # Newer airmon-ng: "monitor mode enabled on wlan0mon"
    m = re.search(r"monitor mode enabled on (\w+)", output)
    if m:
        return m.group(1)

    # Older/verbose: "(mac80211 monitor mode vif enabled for [phy0]wlan0 on [phy0]wlan0mon)"
    m = re.search(r"on \[?[^\[\]\s]*\]?(\w+)", output)
    if m:
        candidate = m.group(1)
        if get_mode(candidate) == "monitor":
            return candidate

    # Some drivers modify the interface in-place
    if get_mode(name) == "monitor":
        return name

    # Common convention: append "mon"
    mon = name + "mon"
    if get_mode(mon) == "monitor":
        return mon

    raise RuntimeError(
        f"Could not enable monitor mode on {name!r}.\n"
        f"airmon-ng output:\n{output[-300:].strip()}"
    )


def set_mode(name: str, mode: str) -> None:
    """Set interface *name* to *mode* (``'monitor'`` or ``'managed'``)."""
    subprocess.run(["sudo", "ifconfig", name, "down"], capture_output=True, check=False)
    subprocess.run(
        ["sudo", "iw", "dev", name, "set", "type", mode],
        capture_output=True, check=False,
    )
    subprocess.run(["sudo", "ifconfig", name, "up"], capture_output=True, check=False)


def disable_monitor_mode(name: str) -> None:
    """Stop monitor mode on *name* via ``airmon-ng stop``; fall back to iw/ifconfig."""
    subprocess.run(
        ["sudo", "airmon-ng", "stop", name],
        capture_output=True, check=False,
    )
    if get_mode(name) == "monitor":
        set_mode(name, "managed")


def restart_network_services() -> None:
    subprocess.run(
        ["sudo", "systemctl", "restart", "wpa_supplicant"],
        capture_output=True, check=False,
    )
    subprocess.run(
        ["sudo", "systemctl", "restart", "NetworkManager"],
        capture_output=True, check=False,
    )
