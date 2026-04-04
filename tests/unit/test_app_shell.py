import sys
import tempfile
import unittest
from pathlib import Path
from subprocess import run


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

    def test_render_standalone_shell_script_matches_generated_output(self) -> None:
        root_dir = Path(__file__).resolve().parents[2]
        script_path = root_dir / "tools" / "render_standalone_shell.py"

        with tempfile.TemporaryDirectory(prefix="cellular-automaton-standalone-shell-") as tempdir:
            output_path = Path(tempdir) / "standalone.html"
            run(
                [sys.executable, str(script_path), str(output_path)],
                check=True,
                cwd=root_dir,
            )

            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                render_standalone_document(),
            )


if __name__ == "__main__":
    unittest.main()
