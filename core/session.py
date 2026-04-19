"""A capture session: directory layout and meta.json."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path


META_FILE = "meta.json"
CAPTURE_STEM = "capture"


@dataclass
class Session:
    essid: str
    bssid: str
    channel: str | int | None
    directory: Path
    started_at: str
    stopped_at: str | None = None
    duration_s: float | None = None
    eapol_frames: int | None = None
    handshake_complete: bool | None = None
    capture: str = f"{CAPTURE_STEM}.cap"
    hashcat: str = f"{CAPTURE_STEM}.hc22000"
    extras: dict = field(default_factory=dict)

    @property
    def capture_path(self) -> Path:
        return self.directory / self.capture

    @property
    def hashcat_path(self) -> Path:
        return self.directory / self.hashcat

    @property
    def meta_path(self) -> Path:
        return self.directory / META_FILE

    def save_meta(self) -> None:
        payload = asdict(self)
        payload["directory"] = str(self.directory)
        self.meta_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def mark_stopped(self) -> None:
        stop = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.stopped_at = stop
        if self.started_at:
            try:
                t0 = datetime.fromisoformat(self.started_at)
                t1 = datetime.fromisoformat(stop)
                self.duration_s = (t1 - t0).total_seconds()
            except ValueError:
                self.duration_s = None


def new_session(paths, essid: str, bssid: str, channel: str | int | None) -> Session:
    ts = time.strftime("%Y%m%d-%H%M%S")
    directory = paths.session_dir(essid, ts)
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    sess = Session(
        essid=essid,
        bssid=bssid,
        channel=channel,
        directory=directory,
        started_at=started,
    )
    sess.save_meta()
    return sess
