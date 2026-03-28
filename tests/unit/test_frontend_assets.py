import json
import tempfile
import unittest
from pathlib import Path

from backend.frontend_assets import FrontendAssetManifest


class FrontendAssetManifestTests(unittest.TestCase):
    def test_load_raises_clear_error_when_manifest_is_missing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cellular-automaton-static-") as tempdir:
            with self.assertRaisesRegex(RuntimeError, r"npm run build:frontend"):
                FrontendAssetManifest.load(tempdir)

    def test_load_rejects_invalid_manifest_payload(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cellular-automaton-static-") as tempdir:
            dist_dir = Path(tempdir) / "dist"
            dist_dir.mkdir(parents=True, exist_ok=True)
            (dist_dir / "manifest.json").write_text(json.dumps(["not-an-object"]), encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, r"is invalid"):
                FrontendAssetManifest.load(tempdir)

    def test_entry_assets_resolve_script_and_stylesheets(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cellular-automaton-static-") as tempdir:
            dist_dir = Path(tempdir) / "dist"
            dist_dir.mkdir(parents=True, exist_ok=True)
            (dist_dir / "manifest.json").write_text(
                json.dumps(
                    {
                        "frontend/app.ts": {
                            "file": "assets/app-123.js",
                            "src": "frontend/app.ts",
                            "isEntry": True,
                            "css": ["assets/app-123.css"],
                        }
                    }
                ),
                encoding="utf-8",
            )

            manifest = FrontendAssetManifest.load(tempdir)
            entry_assets = manifest.entry_assets("frontend/app.ts")

            self.assertEqual(entry_assets.script_filename, "dist/assets/app-123.js")
            self.assertEqual(entry_assets.stylesheet_filenames, ("dist/assets/app-123.css",))


if __name__ == "__main__":
    unittest.main()
