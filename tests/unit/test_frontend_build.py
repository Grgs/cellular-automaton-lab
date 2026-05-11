from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from backend.frontend_build import (
    frontend_server_build_status,
    require_current_frontend_server_build,
)


class FrontendBuildStatusTests(unittest.TestCase):
    def _write_repo_fixture(self, root: Path) -> tuple[Path, Path, Path, Path]:
        frontend_dir = root / "frontend"
        frontend_dir.mkdir(parents=True)
        source_path = frontend_dir / "app-runtime.ts"
        source_path.write_text("console.log('preview');\n", encoding="utf-8")
        package_path = root / "package.json"
        package_path.write_text("{}\n", encoding="utf-8")
        static_dist_dir = root / "static" / "dist" / "assets"
        static_dist_dir.mkdir(parents=True)
        asset_path = static_dist_dir / "app-test.js"
        asset_path.write_text("console.log('built');\n", encoding="utf-8")
        manifest_path = root / "static" / "dist" / "manifest.json"
        manifest_path.write_text(
            "{\n"
            '  "frontend/server-entry.ts": {\n'
            '    "file": "assets/app-test.js",\n'
            '    "isEntry": true\n'
            "  }\n"
            "}\n",
            encoding="utf-8",
        )
        return source_path, package_path, manifest_path, asset_path

    def test_frontend_server_build_status_reports_current_build(self) -> None:
        with tempfile.TemporaryDirectory(prefix="frontend-build-status-") as tmpdir:
            root = Path(tmpdir)
            source_path, package_path, manifest_path, asset_path = self._write_repo_fixture(root)
            os.utime(source_path, ns=(1_000_000_000, 1_000_000_000))
            os.utime(package_path, ns=(1_000_000_000, 1_000_000_000))
            os.utime(manifest_path, ns=(2_000_000_000, 2_000_000_000))
            os.utime(asset_path, ns=(3_000_000_000, 3_000_000_000))

            status = frontend_server_build_status(root, root / "static")

            self.assertTrue(status["buildCurrent"])
            self.assertEqual(status["reason"], "frontend build outputs are current")
            self.assertEqual(status["newestSourcePath"], "frontend/app-runtime.ts")
            self.assertEqual(status["newestBuildPath"], "static/dist/assets/app-test.js")

    def test_frontend_server_build_status_reports_stale_build_when_source_is_newer(self) -> None:
        with tempfile.TemporaryDirectory(prefix="frontend-build-stale-") as tmpdir:
            root = Path(tmpdir)
            source_path, package_path, manifest_path, asset_path = self._write_repo_fixture(root)
            os.utime(package_path, ns=(1_000_000_000, 1_000_000_000))
            os.utime(manifest_path, ns=(1_000_000_000, 1_000_000_000))
            os.utime(asset_path, ns=(1_000_000_000, 1_000_000_000))
            os.utime(source_path, ns=(2_000_000_000, 2_000_000_000))

            status = frontend_server_build_status(root, root / "static")

            self.assertFalse(status["buildCurrent"])
            self.assertEqual(status["reason"], "frontend sources are newer than the server bundle")
            self.assertEqual(status["newestSourcePath"], "frontend/app-runtime.ts")

    def test_require_current_frontend_server_build_raises_clear_error_for_stale_build(self) -> None:
        with tempfile.TemporaryDirectory(prefix="frontend-build-guard-") as tmpdir:
            root = Path(tmpdir)
            source_path, package_path, manifest_path, asset_path = self._write_repo_fixture(root)
            os.utime(package_path, ns=(1_000_000_000, 1_000_000_000))
            os.utime(manifest_path, ns=(1_000_000_000, 1_000_000_000))
            os.utime(asset_path, ns=(1_000_000_000, 1_000_000_000))
            os.utime(source_path, ns=(2_000_000_000, 2_000_000_000))

            with self.assertRaisesRegex(
                RuntimeError,
                r"Frontend server build is not current: frontend sources are newer than the server bundle\.",
            ):
                require_current_frontend_server_build(root, root / "static")


if __name__ == "__main__":
    unittest.main()
