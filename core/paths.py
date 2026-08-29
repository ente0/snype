"""Centralised filesystem layout for snype.

All artefacts live under a single portable root. The default is
``./snype-data/`` next to the project. Override with the env var
``SNYPE_DATA_DIR`` or with the CLI flag ``--data-dir``.
"""

from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path

DEFAULT_ROOT_NAME = "snype-data"
HS_DIR_NAME = "hs"
LOGS_DIR_NAME = "logs"
CONFIG_FILE_NAME = "config.json"
FOUND_PASSWORDS_FILE = "found_passwords.jsonl"


@dataclass(frozen=True)
class Paths:
    root: Path
    hs: Path
    logs: Path
    config: Path
    found_passwords: Path

    def ensure(self) -> Paths:
        root = self.root.resolve(strict=False)
        if root in {Path(root.anchor), Path.home().resolve()}:
            raise ValueError("SNYPE_DATA_DIR must be an application-owned subdirectory")
        ensure_application_root(self.root)
        ensure_private_directory(self.hs)
        ensure_private_directory(self.logs)
        for sensitive_file in (self.config, self.found_passwords):
            if sensitive_file.exists() or sensitive_file.is_symlink():
                ensure_private_file(sensitive_file)
        return self

    def session_dir(self, essid: str, timestamp: str) -> Path:
        ensure_private_directory(self.hs)
        safe = _safe_component(essid)
        safe_timestamp = _safe_timestamp_component(timestamp)
        essid_path = _contained_path(self.hs, self.hs / safe)
        ensure_private_directory(essid_path)
        path = _contained_path(self.hs, essid_path / safe_timestamp)
        ensure_private_directory(path)
        return path

    def essid_dir(self, essid: str) -> Path:
        ensure_private_directory(self.hs)
        safe = _safe_component(essid)
        path = _contained_path(self.hs, self.hs / safe)
        ensure_private_directory(path)
        return path


def _safe_component(name: str) -> str:
    raw = str(name)
    slug = "".join(
        char if char.isalnum() or char in ("-", "_") else "_" for char in raw
    ).strip("_-")[:48]
    digest = hashlib.sha256(raw.encode("utf-8", errors="surrogatepass")).hexdigest()[
        :12
    ]
    return f"{slug or 'unknown'}-{digest}"


def _safe_timestamp_component(timestamp: str) -> str:
    """Preserve normal session timestamps while rejecting path components."""
    value = str(timestamp)
    if (
        1 <= len(value) <= 64
        and value not in {".", ".."}
        and value[0].isalnum()
        and all(char.isalnum() or char in ("-", "_", ".") for char in value)
    ):
        return value
    return _safe_component(value)


def _contained_path(base: Path, candidate: Path) -> Path:
    if base.is_symlink():
        raise RuntimeError(f"Refusing symlinked sensitive directory: {base}")
    base = base.resolve(strict=False)
    candidate = candidate.resolve(strict=False)
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise RuntimeError(f"Path escapes the snype data root: {candidate}") from exc
    return candidate


def _check_owned(info: os.stat_result, path: Path) -> None:
    if hasattr(os, "getuid") and info.st_uid != os.getuid():
        raise PermissionError(f"Sensitive path is not owned by this user: {path}")


def _ensure_owned_directory(path: Path, *, private: bool) -> Path:
    """Validate a directory and optionally make the final component private."""
    if path.is_symlink():
        raise RuntimeError(f"Refusing symlinked sensitive directory: {path}")
    existed = path.exists()
    path.mkdir(parents=True, mode=0o700, exist_ok=True)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode):
        raise RuntimeError(f"Sensitive path is not a directory: {path}")
    _check_owned(info, path)
    if os.name == "posix" and (private or not existed):
        path.chmod(0o700)
    return path


def ensure_application_root(path: Path) -> Path:
    """Create a private data root without chmodding an existing custom root."""
    return _ensure_owned_directory(path, private=False)


def ensure_private_directory(path: Path) -> Path:
    """Create or repair an owner-only managed directory without symlinks."""
    return _ensure_owned_directory(path, private=True)


def private_text_open(
    path: Path,
    mode: str,
    *,
    encoding: str = "utf-8",
    errors: str | None = None,
):
    """Open an owner-only regular text file with no symlink traversal."""
    if path.is_symlink():
        raise RuntimeError(f"Refusing symlinked sensitive file: {path}")
    # The data root may be a pre-existing application directory shared with
    # other files. Protect the credential itself without chmodding that root.
    ensure_application_root(path.parent)
    try:
        existing_info = path.lstat()
    except FileNotFoundError:
        existing_info = None
    if existing_info is not None:
        if not stat.S_ISREG(existing_info.st_mode):
            raise RuntimeError(f"Sensitive path is not a regular file: {path}")
        _check_owned(existing_info, path)

    if mode == "r":
        flags = os.O_RDONLY
    elif mode == "a":
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    elif mode == "w":
        flags = os.O_WRONLY | os.O_CREAT
    else:
        raise ValueError(f"Unsupported private file mode: {mode}")
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK
    fd = os.open(path, flags, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise RuntimeError(f"Sensitive path is not a regular file: {path}")
        _check_owned(info, path)
        if os.name == "posix":
            os.fchmod(fd, 0o600)
        if mode == "w":
            os.ftruncate(fd, 0)
        return os.fdopen(fd, mode, encoding=encoding, errors=errors)
    except Exception:
        os.close(fd)
        raise


def ensure_private_file(path: Path) -> Path:
    with private_text_open(path, "a"):
        pass
    return path


def resolve_root(cli_override: str | None = None) -> Path:
    if cli_override:
        return Path(cli_override).expanduser().resolve()
    env = os.environ.get("SNYPE_DATA_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return (Path.cwd() / DEFAULT_ROOT_NAME).resolve()


def build_paths(cli_override: str | None = None) -> Paths:
    root = resolve_root(cli_override)
    return Paths(
        root=root,
        hs=root / HS_DIR_NAME,
        logs=root / LOGS_DIR_NAME,
        config=root / CONFIG_FILE_NAME,
        found_passwords=root / FOUND_PASSWORDS_FILE,
    )
