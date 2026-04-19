from __future__ import annotations

import json
import unittest
from pathlib import Path

from backend.bootstrap_data import build_bootstrap_payload
from backend.dev_server import APP_NAME


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP_FIXTURE_PATH = ROOT / "frontend" / "test-fixtures" / "bootstrap-data.json"


class FrontendBootstrapFixtureTests(unittest.TestCase):
    def test_fixture_matches_backend_bootstrap_payload(self) -> None:
        actual = json.loads(BOOTSTRAP_FIXTURE_PATH.read_text(encoding="utf-8"))
        expected = build_bootstrap_payload({"app_name": APP_NAME})

        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
