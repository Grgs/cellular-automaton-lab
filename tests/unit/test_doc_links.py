from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "tools" / "internal" / "check_doc_links.mjs"


class DocumentationLinkCheckerTests(unittest.TestCase):
    def _run_checker(self, files: dict[str, str]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for relative_path, content in files.items():
                destination = root / relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(content, encoding="utf-8")
            return subprocess.run(
                ["node", str(CHECKER), "--root", str(root), "*.md", "docs"],
                cwd=ROOT,
                capture_output=True,
                check=False,
                text=True,
            )

    def test_accepts_files_directories_html_links_and_github_anchors(self) -> None:
        result = self._run_checker(
            {
                "README.md": (
                    "[guide](docs/GUIDE.md#quick-start)\n"
                    '<a href="docs/GUIDE.md">Guide</a>\n'
                    '<img src="docs/image.svg">\n'
                    "[docs directory](docs/)\n"
                    "[external](https://example.com/unavailable)\n"
                ),
                "docs/GUIDE.md": "## Quick start\n",
                "docs/image.svg": "<svg></svg>\n",
            }
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Checked 4 local link(s) in 2 documentation file(s).", result.stdout)

    def test_reports_missing_paths_and_anchors(self) -> None:
        result = self._run_checker(
            {
                "README.md": "[missing](docs/MISSING.md) [anchor](docs/GUIDE.md#absent)\n",
                "docs/GUIDE.md": "# Present\n",
            }
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("docs/MISSING.md points to a missing path", result.stderr)
        self.assertIn("docs/GUIDE.md#absent points to a missing anchor", result.stderr)


if __name__ == "__main__":
    unittest.main()
