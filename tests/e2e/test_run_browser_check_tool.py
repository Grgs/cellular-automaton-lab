from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.run_browser_check import main


ROOT_DIR = Path(__file__).resolve().parents[2]
STANDALONE_OUTPUT_DIR = ROOT_DIR / "output" / "standalone"
STANDALONE_REQUIRED_OUTPUTS = (
    "index.html",
    "standalone-bootstrap.json",
    "standalone-python-bundle.json",
)


def _standalone_outputs_ready() -> bool:
    return all((STANDALONE_OUTPUT_DIR / relative_path).exists() for relative_path in STANDALONE_REQUIRED_OUTPUTS)


class RunBrowserCheckToolIntegrationTests(unittest.TestCase):
    @unittest.skipUnless(
        _standalone_outputs_ready(),
        "standalone outputs are required; run `npm run build:frontend:standalone`",
    )
    def test_runner_delegates_standalone_render_review(self) -> None:
        with tempfile.TemporaryDirectory(prefix="run-browser-check-standalone-") as tmpdir:
            output_dir = Path(tmpdir)
            exit_code = main(
                [
                    "--host",
                    "standalone",
                    "--artifact-dir",
                    str(output_dir / "artifacts"),
                    "--render-review",
                    "--family",
                    "chair",
                    "--patch-depth",
                    "3",
                ]
            )
            self.assertEqual(exit_code, 0)
            manifest = json.loads((output_dir / "artifacts" / "run-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["hostKind"], "standalone")
            self.assertEqual(manifest["mode"], "render-review")
            self.assertEqual(manifest["exitStatus"], "success")
            self.assertEqual(manifest["renderPng"], str(output_dir / "artifacts" / "chair-depth-3.png"))
            self.assertEqual(manifest["renderSummary"], str(output_dir / "artifacts" / "chair-depth-3.json"))
            self.assertTrue((output_dir / "artifacts" / "chair-depth-3.png").exists())
            self.assertTrue((output_dir / "artifacts" / "chair-depth-3.json").exists())
            self.assertIn("consistencyWarnings", manifest)

    def test_runner_delegates_server_render_review(self) -> None:
        with tempfile.TemporaryDirectory(prefix="run-browser-check-server-") as tmpdir:
            output_dir = Path(tmpdir)
            exit_code = main(
                [
                    "--host",
                    "server",
                    "--artifact-dir",
                    str(output_dir / "artifacts"),
                    "--render-review",
                    "--family",
                    "chair",
                    "--patch-depth",
                    "3",
                ]
            )
            self.assertEqual(exit_code, 0)
            manifest = json.loads((output_dir / "artifacts" / "run-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["hostKind"], "server")
            self.assertEqual(manifest["mode"], "render-review")
            self.assertEqual(manifest["exitStatus"], "success")
            self.assertEqual(manifest["renderPng"], str(output_dir / "artifacts" / "chair-depth-3.png"))
            self.assertEqual(manifest["renderSummary"], str(output_dir / "artifacts" / "chair-depth-3.json"))
            self.assertTrue((output_dir / "artifacts" / "chair-depth-3.png").exists())
            self.assertTrue((output_dir / "artifacts" / "chair-depth-3.json").exists())

    @unittest.skipUnless(
        _standalone_outputs_ready(),
        "standalone outputs are required; run `npm run build:frontend:standalone`",
    )
    def test_runner_delegates_standalone_unittest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="run-browser-check-standalone-unittest-") as tmpdir:
            output_dir = Path(tmpdir)
            exit_code = main(
                [
                    "--host",
                    "standalone",
                    "--artifact-dir",
                    str(output_dir / "artifacts"),
                    "--unittest",
                    "tests.e2e.playwright_case_suite.StandaloneCellularAutomatonUITests.test_chair_topology_switch_renders_aperiodic_patch",
                ]
            )
            self.assertEqual(exit_code, 0)
            manifest = json.loads((output_dir / "artifacts" / "run-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["hostKind"], "standalone")
            self.assertEqual(manifest["mode"], "unittest")
            self.assertEqual(manifest["exitStatus"], "success")
            self.assertIn("unittestTargets", manifest)

    def test_runner_delegates_server_unittest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="run-browser-check-server-unittest-") as tmpdir:
            output_dir = Path(tmpdir)
            exit_code = main(
                [
                    "--host",
                    "server",
                    "--artifact-dir",
                    str(output_dir / "artifacts"),
                    "--unittest",
                    "tests.e2e.playwright_case_suite.CellularAutomatonUITests.test_chair_topology_switch_renders_aperiodic_patch",
                ]
            )
            self.assertEqual(exit_code, 0)
            manifest = json.loads((output_dir / "artifacts" / "run-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["hostKind"], "server")
            self.assertEqual(manifest["mode"], "unittest")
            self.assertEqual(manifest["exitStatus"], "success")

    def test_runner_delegates_server_unittest_with_success_artifacts(self) -> None:
        with tempfile.TemporaryDirectory(prefix="run-browser-check-server-unittest-success-") as tmpdir:
            output_dir = Path(tmpdir)
            exit_code = main(
                [
                    "--host",
                    "server",
                    "--success-artifacts",
                    "--artifact-dir",
                    str(output_dir / "artifacts"),
                    "--unittest",
                    "tests.e2e.playwright_case_suite.CellularAutomatonUITests.test_chair_topology_switch_renders_aperiodic_patch",
                ]
            )
            self.assertEqual(exit_code, 0)
            manifest = json.loads((output_dir / "artifacts" / "run-manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["successArtifactsRequested"])
            test_artifacts_dir = output_dir / "artifacts" / "test-artifacts"
            self.assertEqual(manifest["testArtifactsDir"], str(test_artifacts_dir))
            self.assertTrue(test_artifacts_dir.exists())
            artifact_dirs = [path for path in test_artifacts_dir.iterdir() if path.is_dir()]
            self.assertEqual(len(artifact_dirs), 1)
            artifact_dir = artifact_dirs[0]
            self.assertTrue((artifact_dir / "page.png").exists())
            self.assertTrue((artifact_dir / "canvas.png").exists())
            self.assertTrue((artifact_dir / "render-summary.json").exists())
            self.assertTrue((artifact_dir / "run-manifest.json").exists())
