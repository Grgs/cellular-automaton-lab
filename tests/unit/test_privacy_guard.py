import sys
import tempfile
import unittest
from collections.abc import Iterator
from contextlib import contextmanager
from os import chdir
from pathlib import Path

try:
    from tools.privacy_guard import ALLOW_MARKER, scan_paths
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.privacy_guard import ALLOW_MARKER, scan_paths


class PrivacyGuardTests(unittest.TestCase):
    @contextmanager
    def _in_temp_dir(self) -> Iterator[Path]:
        with tempfile.TemporaryDirectory(prefix="privacy-guard-") as temp_dir:
            original_cwd = Path.cwd()
            temp_path = Path(temp_dir)
            chdir(temp_path)
            try:
                yield temp_path
            finally:
                chdir(original_cwd)

    def test_detects_local_paths_and_consumer_email_addresses(self) -> None:
        with self._in_temp_dir() as temp_dir:
            file_path = temp_dir / "README.md"
            windows_path = "C:" + "/" + "Us" + "ers" + "/" + "example/Documents/project"
            consumer_email = "person@" + "gma" + "il.com"
            file_path.write_text(
                f"Path: {windows_path}\n"
                f"Email: {consumer_email}\n",
                encoding="utf-8",
            )

            violations = scan_paths([file_path.name], all_files=False)

        self.assertTrue(any("Windows user-profile path" in violation for violation in violations))
        self.assertTrue(any("consumer webmail address" in violation for violation in violations))

    def test_allow_marker_suppresses_line_level_findings(self) -> None:
        with self._in_temp_dir() as temp_dir:
            file_path = temp_dir / "README.md"
            consumer_email = "person@" + "out" + "look.com"
            file_path.write_text(
                f"{consumer_email}  # {ALLOW_MARKER}\n",
                encoding="utf-8",
            )

            violations = scan_paths([file_path.name], all_files=False)

        self.assertEqual(violations, [])

    def test_detects_consumer_cloud_links(self) -> None:
        with self._in_temp_dir() as temp_dir:
            file_path = temp_dir / "README.md"
            cloud_link = "https://" + "drive." + "google.com/file/d/123/view"
            file_path.write_text(
                f"{cloud_link}\n",
                encoding="utf-8",
            )

            violations = scan_paths([file_path.name], all_files=False)

        self.assertTrue(any("consumer cloud-share link" in violation for violation in violations))


if __name__ == "__main__":
    unittest.main()
