"""Convert ``.cap`` / ``.pcap`` to Hashcat ``.hc22000`` via ``hcxpcapngtool``."""
from __future__ import annotations

import subprocess
from pathlib import Path


def convert(cap_file: Path, out_file: Path | None = None) -> Path | None:
    """Convert ``cap_file`` and return the path to the generated hc22000,
    or ``None`` on failure / empty output.
    """
    if not cap_file.exists():
        return None
    out = out_file or cap_file.with_suffix(".hc22000")
    try:
        subprocess.run(
            ["hcxpcapngtool", "-o", str(out), str(cap_file)],
            capture_output=True, check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    if out.exists() and out.stat().st_size > 0:
        return out
    if out.exists():
        out.unlink()
    return None


def extract_essid_via_aircrack(cap_file: Path) -> str | None:
    """Best-effort ESSID extraction by parsing ``aircrack-ng`` output."""
    if not cap_file.exists():
        return None
    try:
        proc = subprocess.run(
            ["aircrack-ng", str(cap_file)],
            capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        return None
    for line in proc.stdout.splitlines():
        if "WPA (" in line:
            tokens = line.strip().split()
            if len(tokens) > 2:
                return "_".join(tokens[2:]).split("_WPA")[0]
    return None
