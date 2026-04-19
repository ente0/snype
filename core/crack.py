"""Wordlist cracking wrapper around aircrack-ng."""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


KEY_RE = re.compile(r"KEY FOUND!\s*\[\s*(?P<pw>.+?)\s*\]")


@dataclass
class CrackResult:
    success: bool
    password: str | None
    stdout: str
    stderr: str


def crack(cap_file: Path, wordlist: Path, bssid: str | None = None) -> CrackResult:
    cmd = ["aircrack-ng", "-w", str(wordlist)]
    if bssid:
        cmd.extend(["-b", bssid])
    cmd.append(str(cap_file))
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return CrackResult(False, None, "", "aircrack-ng not found in PATH")
    out = proc.stdout or ""
    pw = None
    for line in out.splitlines():
        m = KEY_RE.search(line)
        if m:
            pw = m.group("pw")
            break
    return CrackResult(success=bool(pw), password=pw, stdout=out, stderr=proc.stderr or "")
