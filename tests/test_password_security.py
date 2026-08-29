from __future__ import annotations

import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import migrate
from core import paths as paths_module
from core.passwords import (
    PasswordEntry,
    append,
    credential_filename,
    load_all,
    write_per_network,
)
from core.paths import build_paths


class PasswordStorageSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.base = Path(self.tempdir.name)
        self.paths = build_paths(str(self.base / "snype-data")).ensure()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_absolute_and_traversal_essids_cannot_escape_data_root(self) -> None:
        escape_stem = self.base / "outside"
        old_vulnerable_path = Path(f"{escape_stem}_password.txt")
        for ssid in (str(escape_stem), "../escaped", "..", ".", "a/b", "a\\b"):
            with self.subTest(ssid=ssid):
                out = write_per_network(
                    self.paths,
                    PasswordEntry(ssid=ssid, password="secret"),
                )
                out.resolve().relative_to(self.paths.root.resolve())
        self.assertFalse(old_vulnerable_path.exists())

    def test_filename_is_deterministic_collision_resistant_and_unicode_safe(
        self,
    ) -> None:
        values = ("a/b", "a?b", "é", "e\u0301", "网络", "\x00hidden")
        names = [credential_filename(value) for value in values]
        self.assertEqual(len(names), len(set(names)))
        for value, name in zip(values, names, strict=True):
            self.assertEqual(credential_filename(value), name)
            self.assertRegex(name, r"^network-[0-9a-f]{64}_password\.txt$")

    def test_exact_essid_remains_display_data(self) -> None:
        entry = PasswordEntry(ssid="Café/网络", password="p@ss")
        append(self.paths.found_passwords, entry)
        out = write_per_network(self.paths, entry)
        loaded = load_all(self.paths.found_passwords)
        self.assertEqual(loaded[0].ssid, entry.ssid)
        self.assertIn("Network: Café/网络", out.read_text(encoding="utf-8"))

    def test_non_object_credential_records_are_ignored(self) -> None:
        self.paths.found_passwords.write_text(
            '["not", "a", "credential"]\n{"ssid":"safe","password":"value"}\n',
            encoding="utf-8",
        )
        loaded = load_all(self.paths.found_passwords)
        self.assertEqual(
            [(entry.ssid, entry.password) for entry in loaded],
            [("safe", "value")],
        )

    def test_standard_session_timestamp_layout_is_preserved(self) -> None:
        session = self.paths.session_dir("network", "20260828-120000")
        self.assertEqual(session.name, "20260828-120000")

    @unittest.skipUnless(os.name == "posix", "POSIX mode assertions")
    def test_directories_and_password_files_are_owner_only_under_umask_022(
        self,
    ) -> None:
        previous = os.umask(0o022)
        try:
            entry = PasswordEntry(ssid="network", password="secret")
            append(self.paths.found_passwords, entry)
            per_network = write_per_network(self.paths, entry)
        finally:
            os.umask(previous)

        for directory in (
            self.paths.root,
            self.paths.hs,
            self.paths.logs,
            per_network.parent,
        ):
            self.assertEqual(stat.S_IMODE(directory.stat().st_mode), 0o700)
        for sensitive in (self.paths.found_passwords, per_network):
            self.assertEqual(stat.S_IMODE(sensitive.stat().st_mode), 0o600)

    @unittest.skipUnless(os.name == "posix", "POSIX mode assertions")
    def test_existing_permissions_are_repaired(self) -> None:
        self.paths.root.chmod(0o755)
        self.paths.hs.chmod(0o755)
        self.paths.found_passwords.write_text("", encoding="utf-8")
        self.paths.found_passwords.chmod(0o644)
        self.paths.ensure()
        self.assertEqual(stat.S_IMODE(self.paths.root.stat().st_mode), 0o755)
        self.assertEqual(stat.S_IMODE(self.paths.hs.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(self.paths.found_passwords.stat().st_mode), 0o600)

    @unittest.skipUnless(os.name == "posix", "POSIX mode assertions")
    def test_append_does_not_chmod_existing_custom_data_root(self) -> None:
        self.paths.root.chmod(0o755)
        append(
            self.paths.found_passwords,
            PasswordEntry(ssid="network", password="secret"),
        )
        self.assertEqual(stat.S_IMODE(self.paths.root.stat().st_mode), 0o755)

    @unittest.skipUnless(os.name == "posix", "symlink semantics")
    def test_symlinked_credential_file_is_rejected(self) -> None:
        entry = PasswordEntry(ssid="network", password="secret")
        essid_dir = self.paths.essid_dir(entry.ssid)
        password_dir = essid_dir / "passwords"
        password_dir.mkdir(mode=0o700)
        target = self.base / "external-secret"
        target.write_text("do not overwrite", encoding="utf-8")
        link = password_dir / credential_filename(entry.ssid)
        link.symlink_to(target)
        with self.assertRaises(RuntimeError):
            write_per_network(self.paths, entry)
        self.assertEqual(target.read_text(encoding="utf-8"), "do not overwrite")

    def test_write_validates_existing_file_before_truncating(self) -> None:
        target = self.paths.found_passwords
        target.write_text("keep", encoding="utf-8")
        original_check = paths_module._check_owned

        def reject_target(info, path):
            if Path(path) == target:
                raise PermissionError("controlled ownership rejection")
            return original_check(info, path)

        with mock.patch.object(
            paths_module,
            "_check_owned",
            side_effect=reject_target,
        ), self.assertRaises(PermissionError):
            paths_module.private_text_open(target, "w")
        self.assertEqual(target.read_text(encoding="utf-8"), "keep")

    @unittest.skipUnless(os.name == "posix", "FIFO semantics")
    def test_private_write_rejects_fifo_before_opening_it(self) -> None:
        fifo = self.paths.root / "credential.fifo"
        os.mkfifo(fifo)
        with self.assertRaises(RuntimeError):
            paths_module.private_text_open(fifo, "w")

    @unittest.skipUnless(os.name == "posix", "symlink semantics")
    def test_replaced_hs_directory_symlink_cannot_escape_data_root(self) -> None:
        external = self.base / "external"
        external.mkdir()
        self.paths.hs.rmdir()
        self.paths.hs.symlink_to(external, target_is_directory=True)

        with self.assertRaises(RuntimeError):
            write_per_network(
                self.paths,
                PasswordEntry(ssid="network", password="secret"),
            )

        self.assertEqual(list(external.iterdir()), [])

    @unittest.skipUnless(os.name == "posix", "symlink semantics")
    def test_legacy_handshake_symlink_is_rejected_without_moving_victim(self) -> None:
        external = self.base / "victim"
        external.mkdir()
        victim_file = external / "important.txt"
        victim_file.write_text("keep", encoding="utf-8")
        legacy = self.base / "handshakes"
        legacy.symlink_to(external, target_is_directory=True)

        with (
            mock.patch.object(migrate, "LEGACY_HANDSHAKES", legacy),
            self.assertRaises(RuntimeError),
        ):
            migrate._migrate_handshakes(self.paths)

        self.assertEqual(victim_file.read_text(encoding="utf-8"), "keep")
        self.assertFalse((self.paths.hs / victim_file.name).exists())

    def test_regular_legacy_handshake_is_migrated_into_private_tree(self) -> None:
        legacy = self.base / "handshakes"
        legacy.mkdir()
        capture = legacy / "capture.cap"
        capture.write_bytes(b"capture")

        with mock.patch.object(migrate, "LEGACY_HANDSHAKES", legacy):
            actions = migrate._migrate_handshakes(self.paths)

        self.assertEqual((self.paths.hs / capture.name).read_bytes(), b"capture")
        if os.name == "posix":
            self.assertEqual(
                stat.S_IMODE((self.paths.hs / capture.name).stat().st_mode),
                0o600,
            )
        self.assertFalse(legacy.exists())
        self.assertEqual(actions, [f"[hs]  merged {capture.name}"])


if __name__ == "__main__":
    unittest.main()
