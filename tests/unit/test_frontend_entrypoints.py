from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
LEGACY_SERVER_ENTRY = "/".join(("frontend", "app.ts"))
LEGACY_RUNTIME_ENTRY = "/".join(("frontend", "main.ts"))
SCANNED_SUFFIXES = {
    ".d.ts",
    ".html",
    ".md",
    ".mjs",
    ".py",
    ".ts",
    ".yml",
}


def _iter_text_files() -> list[Path]:
    scanned_paths = [
        ROOT_DIR / "backend",
        ROOT_DIR / "docs",
        ROOT_DIR / "frontend",
        ROOT_DIR / "templates",
        ROOT_DIR / "tests",
        ROOT_DIR / "tools",
        ROOT_DIR / "vite.config.ts",
    ]
    discovered: list[Path] = []
    for scanned_path in scanned_paths:
        if scanned_path.is_file():
            discovered.append(scanned_path)
            continue
        for candidate in scanned_path.rglob("*"):
            if candidate.is_file() and candidate.suffix in SCANNED_SUFFIXES:
                discovered.append(candidate)
    return discovered


class FrontendEntrypointContractTests(unittest.TestCase):
    def test_legacy_startup_wrapper_files_are_removed(self) -> None:
        self.assertFalse((ROOT_DIR / "frontend" / "app.ts").exists())
        self.assertFalse((ROOT_DIR / "frontend" / "main.ts").exists())

    def test_repo_no_longer_references_legacy_startup_paths(self) -> None:
        legacy_mentions: list[str] = []
        for candidate in _iter_text_files():
            text = candidate.read_text(encoding="utf-8")
            if LEGACY_SERVER_ENTRY in text or LEGACY_RUNTIME_ENTRY in text:
                legacy_mentions.append(str(candidate.relative_to(ROOT_DIR)))

        self.assertEqual(legacy_mentions, [])


if __name__ == "__main__":
    unittest.main()
