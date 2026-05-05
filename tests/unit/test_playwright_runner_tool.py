from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class PlaywrightRunnerToolTests(unittest.TestCase):
    def test_list_suites_reports_public_playwright_suites(self) -> None:
        node_command = shutil.which("node") or shutil.which("node.exe")
        if node_command is None:
            self.skipTest("node is required to inspect the Playwright runner suites")

        result = subprocess.run(
            [node_command, "./tools/run-playwright.mjs", "--list-suites"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        suite_names = [entry["name"] for entry in payload]

        self.assertEqual(
            suite_names,
            [
                "all",
                "server",
                "standalone",
                "subset",
                "rules_and_picker",
                "overlays_and_editor",
                "topology_and_persistence",
                "pattern_and_showcase",
                "standalone_runtime",
            ],
        )

    def test_list_suites_marks_standalone_build_requirements(self) -> None:
        node_command = shutil.which("node") or shutil.which("node.exe")
        if node_command is None:
            self.skipTest("node is required to inspect the Playwright runner suites")

        result = subprocess.run(
            [node_command, "./tools/run-playwright.mjs", "--list-suites"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = {entry["name"]: entry for entry in json.loads(result.stdout)}

        self.assertTrue(payload["all"]["requires_standalone_build"])
        self.assertTrue(payload["standalone"]["requires_standalone_build"])
        self.assertTrue(payload["standalone_runtime"]["requires_standalone_build"])
        self.assertFalse(payload["server"]["requires_standalone_build"])
        self.assertFalse(payload["subset"]["requires_standalone_build"])


if __name__ == "__main__":
    unittest.main()
