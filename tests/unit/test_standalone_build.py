from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import standalone_build


class StandaloneBuildTests(unittest.TestCase):
    def test_copy_pyodide_runtime_copies_only_required_runtime_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix="standalone-build-pyodide-") as tmpdir:
            root = Path(tmpdir)
            package_dir = root / "package"
            output_dir = root / "output"
            package_dir.mkdir()
            for filename in standalone_build.PYODIDE_RUNTIME_FILES:
                (package_dir / filename).write_bytes(f"runtime:{filename}".encode())
            (package_dir / "pyodide.js.map").write_text("not deployed", encoding="utf-8")

            with (
                patch.object(standalone_build, "PYODIDE_PACKAGE_DIR", package_dir),
                patch.object(standalone_build, "OUTPUT_DIR", output_dir),
            ):
                standalone_build.copy_pyodide_runtime()

            copied_files = sorted(
                path.name for path in (output_dir / "pyodide").iterdir() if path.is_file()
            )
            self.assertEqual(copied_files, sorted(standalone_build.PYODIDE_RUNTIME_FILES))
            self.assertEqual(
                (output_dir / "pyodide" / "pyodide.js").read_bytes(),
                b"runtime:pyodide.js",
            )


if __name__ == "__main__":
    unittest.main()
