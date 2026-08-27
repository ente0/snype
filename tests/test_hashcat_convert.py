import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.hashcat_convert import (
    ConversionStatus,
    convert,
    convert_capture,
)


class ConvertCaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.cap = Path(self.temp_dir.name) / "capture.cap"
        self.out = Path(self.temp_dir.name) / "capture.hc22000"
        self.cap.write_bytes(b"capture")

    @patch("core.hashcat_convert.find_hcxpcapngtool", return_value=None)
    def test_reports_missing_tool(self, _find):
        result = convert_capture(self.cap, self.out)

        self.assertEqual(result.status, ConversionStatus.MISSING_TOOL)
        self.assertIsNone(result.output)
        self.assertIn("install hcxtools", result.detail)

    @patch("core.hashcat_convert.find_hcxpcapngtool", return_value="/usr/bin/hcxpcapngtool")
    @patch("core.hashcat_convert.subprocess.run")
    def test_reports_converter_error(self, run, _find):
        self.out.write_text("existing hash")
        run.return_value = subprocess.CompletedProcess([], 1, "", "invalid capture")

        result = convert_capture(self.cap, self.out)

        self.assertEqual(result.status, ConversionStatus.ERROR)
        self.assertEqual(result.detail, "invalid capture")
        self.assertEqual(self.out.read_text(), "existing hash")

    @patch("core.hashcat_convert.find_hcxpcapngtool", return_value="/usr/bin/hcxpcapngtool")
    @patch("core.hashcat_convert.subprocess.run")
    def test_distinguishes_no_handshake_from_failure(self, run, _find):
        run.return_value = subprocess.CompletedProcess([], 0, "no hashes written", "")

        result = convert_capture(self.cap, self.out)

        self.assertEqual(result.status, ConversionStatus.NO_HANDSHAKE)
        self.assertIsNone(result.output)

    @patch("core.hashcat_convert.find_hcxpcapngtool", return_value="/usr/bin/hcxpcapngtool")
    @patch("core.hashcat_convert.subprocess.run")
    def test_returns_non_empty_conversion(self, run, _find):
        def write_output(command, **_kwargs):
            Path(command[2]).write_text("WPA*02*hash")
            return subprocess.CompletedProcess([], 0, "", "")

        run.side_effect = write_output

        result = convert_capture(self.cap, self.out)

        self.assertEqual(result.status, ConversionStatus.SUCCESS)
        self.assertEqual(result.output, self.out)
        self.assertEqual(convert(self.cap, self.out), self.out)


if __name__ == "__main__":
    unittest.main()
