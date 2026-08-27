"""Convert ``.cap`` / ``.pcap`` to Hashcat ``.hc22000`` via ``hcxpcapngtool``."""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ConversionStatus(str, Enum):
    SUCCESS = "success"
    NO_HANDSHAKE = "no_handshake"
    MISSING_CAPTURE = "missing_capture"
    MISSING_TOOL = "missing_tool"
    ERROR = "error"


@dataclass(frozen=True)
class ConversionResult:
    status: ConversionStatus
    output: Path | None = None
    detail: str = ""


def find_hcxpcapngtool() -> str | None:
    """Return the converter executable path, if it is available."""
    return shutil.which("hcxpcapngtool")


def convert_capture(cap_file: Path, out_file: Path | None = None) -> ConversionResult:
    """Convert a capture while preserving the reason conversion did not succeed."""
    if not cap_file.exists():
        return ConversionResult(
            ConversionStatus.MISSING_CAPTURE,
            detail=f"capture file not found: {cap_file}",
        )

    executable = find_hcxpcapngtool()
    if not executable:
        return ConversionResult(
            ConversionStatus.MISSING_TOOL,
            detail="hcxpcapngtool not found in PATH (install hcxtools)",
        )

    out = out_file or cap_file.with_suffix(".hc22000")
    temporary_out = out.with_name(f".{out.name}.tmp")
    if temporary_out.exists():
        temporary_out.unlink()

    try:
        proc = subprocess.run(
            [executable, "-o", str(temporary_out), str(cap_file)],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        temporary_out.unlink(missing_ok=True)
        return ConversionResult(ConversionStatus.ERROR, detail=str(exc))

    if proc.returncode != 0:
        temporary_out.unlink(missing_ok=True)
        detail = (proc.stderr or proc.stdout).strip()
        return ConversionResult(
            ConversionStatus.ERROR,
            detail=detail or f"hcxpcapngtool exited with status {proc.returncode}",
        )

    if temporary_out.exists() and temporary_out.stat().st_size > 0:
        temporary_out.replace(out)
        return ConversionResult(ConversionStatus.SUCCESS, output=out)

    if temporary_out.exists():
        temporary_out.unlink()
    return ConversionResult(
        ConversionStatus.NO_HANDSHAKE,
        detail=(proc.stderr or proc.stdout).strip(),
    )


def convert(cap_file: Path, out_file: Path | None = None) -> Path | None:
    """Backward-compatible wrapper returning only a successful output path."""
    return convert_capture(cap_file, out_file).output


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
