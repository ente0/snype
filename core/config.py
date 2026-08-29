"""Persistent app config: interfaces and last target.

Replaces the legacy flat files ``interface_config.txt`` and
``selected_network.txt`` with a single JSON document. Writes are atomic
(write to a temp file, then ``os.replace``) to avoid corruption on crash.
"""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .paths import ensure_application_root, ensure_private_file


@dataclass
class Target:
    bssid: str | None = None
    channel: str | None = None
    essid: str | None = None


@dataclass
class Config:
    monitor_iface: str | None = None
    inject_iface: str | None = None
    target: Target = field(default_factory=Target)
    term_mode: str = "auto"

    @classmethod
    def load(cls, path: Path) -> Config:
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return cls()
        tgt = data.get("target") or {}
        return cls(
            monitor_iface=data.get("monitor_iface"),
            inject_iface=data.get("inject_iface"),
            target=Target(
                bssid=tgt.get("bssid"),
                channel=tgt.get("channel"),
                essid=tgt.get("essid"),
            ),
            term_mode=data.get("term_mode", "auto"),
        )

    def save(self, path: Path) -> None:
        ensure_application_root(path.parent)
        if path.exists() or path.is_symlink():
            ensure_private_file(path)
        payload = asdict(self)
        fd, tmp = tempfile.mkstemp(prefix=".cfg-", dir=str(path.parent))
        try:
            if os.name == "posix":
                os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as fp:
                json.dump(payload, fp, indent=2)
            os.replace(tmp, path)
            ensure_private_file(path)
        except Exception:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise

    def has_interfaces(self) -> bool:
        return bool(self.monitor_iface)

    def has_target(self) -> bool:
        return bool(self.target.bssid)

    def effective_inject(self) -> str | None:
        return self.inject_iface or self.monitor_iface
