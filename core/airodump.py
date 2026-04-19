"""airodump-ng wrappers: network scan and targeted capture."""
from __future__ import annotations

import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Network:
    idx: int
    bssid: str
    channel: str
    power: str
    essid: str
    beacons: str = "0"
    data: str = "0"


@dataclass
class Station:
    mac: str
    power: str
    packets: str


# ── live scan primitives ──────────────────────────────────────────────────────

def start_live_scan(
    iface: str,
    output_dir: Path,
    dry_run: bool = False,
) -> subprocess.Popen | None:
    """Start airodump-ng writing continuously to *output_dir*.

    The CSV is at ``output_dir / "scan-01.csv"`` and updated every second.
    Returns the process handle, or ``None`` in dry-run mode.
    """
    if dry_run:
        return None
    cmd = [
        "sudo", "airodump-ng",
        "--write", str(output_dir / "scan"),
        "--output-format", "csv",
        "--write-interval", "1",
        iface,
    ]
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def read_live_csv(output_dir: Path) -> list[Network]:
    """Parse the current state of the CSV being written by airodump-ng.

    Returns an empty list if the file does not exist yet or is partially written.
    """
    csv_file = output_dir / "scan-01.csv"
    if not csv_file.exists():
        return []
    try:
        return _parse_airodump_csv(csv_file)
    except Exception:
        return []


def stop_live_scan(proc: subprocess.Popen | None) -> None:
    """Terminate an airodump-ng process started by :func:`start_live_scan`."""
    if proc is None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


# ── high-level blocking scan (kept for compatibility) ────────────────────────

def scan_networks(interface: str, duration: int = 20, dry_run: bool = False) -> list[Network]:
    """Block for *duration* seconds then return discovered networks."""
    if dry_run:
        return []
    with tempfile.TemporaryDirectory(prefix="snype-scan-") as tmp:
        output_dir = Path(tmp)
        proc = start_live_scan(interface, output_dir)
        try:
            time.sleep(duration)
        finally:
            stop_live_scan(proc)
        return read_live_csv(output_dir)


# ── capture ───────────────────────────────────────────────────────────────────

def build_targeted_capture_cmd(
    interface: str,
    bssid: str,
    channel: str | int | None,
    output_stem: Path,
) -> list[str]:
    """Compose the airodump-ng command used during a capture session."""
    cmd = [
        "sudo", "airodump-ng",
        "--ignore-negative-one",
        "--write", str(output_stem),
        "--output-format", "pcap",
        "--bssid", bssid,
    ]
    if channel:
        cmd.extend(["--channel", str(channel)])
    cmd.append(interface)
    return cmd


def start_targeted_capture(
    interface: str,
    bssid: str,
    channel: str | int | None,
    output_stem: Path,
) -> subprocess.Popen:
    """Start airodump-ng targeted capture (pcap + csv). Returns process."""
    cmd = [
        "sudo", "airodump-ng",
        "--ignore-negative-one",
        "--write", str(output_stem),
        "--output-format", "pcap,csv",
        "--write-interval", "1",
        "--bssid", bssid,
    ]
    if channel:
        cmd.extend(["--channel", str(channel)])
    cmd.append(interface)
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def read_capture_stats(output_stem: Path) -> tuple[list[Network], list[Station]]:
    """Parse the live CSV written during targeted capture (stem-01.csv).

    Returns (networks, stations). Both lists are empty if the file does not
    exist yet or is partially written.
    """
    csv_file = Path(str(output_stem) + "-01.csv")
    if not csv_file.exists():
        return [], []
    try:
        return _parse_capture_csv(csv_file)
    except Exception:
        return [], []


def _parse_capture_csv(path: Path) -> tuple[list[Network], list[Station]]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    try:
        station_idx = next(i for i, ln in enumerate(lines) if "Station MAC" in ln)
    except StopIteration:
        station_idx = len(lines)

    networks: list[Network] = []
    idx = 0
    for line in lines[1:station_idx]:
        line = line.strip()
        if not line or "BSSID" in line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 14:
            continue
        networks.append(Network(
            idx=idx,
            bssid=parts[0],
            channel=parts[3],
            power=parts[8],
            essid=parts[13],
            beacons=parts[9] if len(parts) > 9 else "0",
            data=parts[10] if len(parts) > 10 else "0",
        ))
        idx += 1

    stations: list[Station] = []
    for line in lines[station_idx + 1:]:
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 5:
            continue
        stations.append(Station(
            mac=parts[0],
            power=parts[3],
            packets=parts[4],
        ))

    return networks, stations


def kill_interfering_processes() -> None:
    subprocess.run(["sudo", "airmon-ng", "check", "kill"], capture_output=True, check=False)


# ── CSV parser ────────────────────────────────────────────────────────────────

def _parse_airodump_csv(path: Path) -> list[Network]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    try:
        station_index = next(i for i, line in enumerate(lines) if "Station MAC" in line)
    except StopIteration:
        station_index = len(lines)
    networks: list[Network] = []
    idx = 0
    for line in lines[1:station_index]:
        line = line.strip()
        if not line or "BSSID" in line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 14:
            continue
        networks.append(Network(
            idx=idx,
            bssid=parts[0],
            channel=parts[3],
            power=parts[8],
            essid=parts[13],
        ))
        idx += 1
    return networks
