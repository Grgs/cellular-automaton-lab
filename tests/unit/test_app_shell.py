import sys
import unittest
from pathlib import Path


try:
    from backend.app_shell import render_server_app_shell, render_standalone_document
    from backend.defaults import APP_DEFAULTS
    from backend.simulation.topology_catalog import describe_topologies
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.app_shell import render_server_app_shell, render_standalone_document
    from backend.defaults import APP_DEFAULTS
    from backend.simulation.topology_catalog import describe_topologies


class AppShellTests(unittest.TestCase):
    def test_render_server_app_shell_uses_current_default_controls(self) -> None:
        rendered = render_server_app_shell(APP_DEFAULTS, describe_topologies())

        self.assertIn('<div id="app-startup-error" hidden></div>', rendered)
        self.assertIn('<option value="square" selected="selected">Square</option>', rendered)
        self.assertIn('value="12"', rendered)
        self.assertIn(">7 gen/s<", rendered)
        self.assertIn('<select id="adjacency-mode-select"><option value="edge" selected="selected">Edge</option></select>', rendered)

    def test_checked_in_standalone_shell_matches_generated_output(self) -> None:
        standalone_path = Path(__file__).resolve().parents[2] / "standalone.html"

        self.assertEqual(
            standalone_path.read_text(encoding="utf-8"),
            render_standalone_document(),
        )


if __name__ == "__main__":
    unittest.main()
