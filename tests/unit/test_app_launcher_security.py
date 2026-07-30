from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class AppLauncherSecurityTests(unittest.TestCase):
    def test_flask_launcher_does_not_enable_debug_mode(self) -> None:
        tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
        app_run_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "run"
        ]

        self.assertEqual(len(app_run_calls), 1)
        debug_keywords = [
            keyword for keyword in app_run_calls[0].keywords if keyword.arg == "debug"
        ]
        self.assertTrue(
            not debug_keywords
            or all(
                isinstance(keyword.value, ast.Constant) and keyword.value.value is False
                for keyword in debug_keywords
            )
        )


if __name__ == "__main__":
    unittest.main()
