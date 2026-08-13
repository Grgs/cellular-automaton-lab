from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools import dependency_maintenance as dependencies


class EnvironmentGuardTests(unittest.TestCase):
    def test_windows_python_from_wsl_is_rejected(self) -> None:
        with self.assertRaisesRegex(dependencies.MaintenanceError, "Windows Python from WSL"):
            dependencies.ensure_native_wsl_python(
                platform="win32", environment={"WSL_DISTRO_NAME": "Ubuntu"}
            )

    def test_native_wsl_python_is_allowed(self) -> None:
        dependencies.ensure_native_wsl_python(
            platform="linux", environment={"WSL_DISTRO_NAME": "Ubuntu"}
        )

    def test_python_version_must_match_repository_pin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            version_path = Path(tmp) / ".python-version"
            version_path.write_text("0.0.0\n", encoding="utf-8")
            with (
                patch.object(dependencies, "PYTHON_VERSION_PATH", version_path),
                self.assertRaisesRegex(dependencies.MaintenanceError, "requires 0.0.0"),
            ):
                dependencies.check_python_version()


class PinParsingTests(unittest.TestCase):
    def test_python_source_pins_are_read_from_both_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = root / "requirements.in"
            development = root / "requirements-dev.in"
            runtime.write_text("Flask==3.1.3\n", encoding="utf-8")
            development.write_text("Pillow==12.3.0\nruff==0.16.2\n", encoding="utf-8")
            with patch.object(dependencies, "PYTHON_SOURCE_PATHS", (runtime, development)):
                pins = dependencies.read_python_source_pins()

        self.assertEqual(pins["flask"].current, "3.1.3")
        self.assertEqual(pins["pillow"].source, "requirements-dev.in")
        self.assertEqual(pins["ruff"].current, "0.16.2")

    def test_npm_source_pins_include_dev_dependencies_and_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_path = Path(tmp) / "package.json"
            package_path.write_text(
                json.dumps(
                    {
                        "devDependencies": {"vite": "^8.2.1"},
                        "overrides": {"rolldown": "1.2.4"},
                    }
                ),
                encoding="utf-8",
            )
            with patch.object(dependencies, "PACKAGE_PATH", package_path):
                pins = dependencies.read_npm_source_pins()

        self.assertEqual(pins["devDependencies:vite"].current, "8.2.1")
        self.assertEqual(pins["overrides:rolldown"].current, "1.2.4")

    def test_exact_pin_replacement_preserves_package_name(self) -> None:
        updated = dependencies._replace_python_pin(
            "Pillow==12.2.0\nruff==0.16.2\n", "Pillow", "12.3.0"
        )
        self.assertEqual(updated, "Pillow==12.3.0\nruff==0.16.2\n")


class RegistryResolutionTests(unittest.TestCase):
    def test_resolvers_annotate_current_and_stale_pins(self) -> None:
        pins = [
            dependencies.DependencyPin("python", "Flask", "3.1.3", "requirements.in"),
            dependencies.DependencyPin("npm", "vite", "8.2.0", "package.json#devDependencies"),
        ]
        resolved = dependencies.resolve_latest_versions(
            pins,
            python_resolver=lambda _name: "3.1.3",
            npm_resolver=lambda _name: "8.2.1",
        )

        self.assertTrue(resolved[1].is_current)
        self.assertFalse(resolved[0].is_current)
        self.assertEqual(resolved[0].latest, "8.2.1")


class LockValidationTests(unittest.TestCase):
    def test_direct_pins_must_match_lock_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime_lock = root / "requirements.txt"
            development_lock = root / "requirements-dev.txt"
            package = root / "package.json"
            package_lock = root / "package-lock.json"
            runtime_lock.write_text("Flask==3.1.3\n", encoding="utf-8")
            development_lock.write_text("ruff==0.16.2\n", encoding="utf-8")
            package.write_text(
                json.dumps({"devDependencies": {"vite": "^8.2.1"}, "overrides": {}}),
                encoding="utf-8",
            )
            package_lock.write_text(
                json.dumps(
                    {
                        "packages": {
                            "": {"devDependencies": {"vite": "^8.2.1"}},
                            "node_modules/vite": {"version": "8.2.1"},
                        }
                    }
                ),
                encoding="utf-8",
            )
            with (
                patch.object(
                    dependencies,
                    "PYTHON_SOURCE_PATHS",
                    (root / "requirements.in", root / "requirements-dev.in"),
                ),
                patch.object(dependencies, "PYTHON_LOCK_PATHS", (runtime_lock, development_lock)),
                patch.object(dependencies, "PACKAGE_PATH", package),
                patch.object(dependencies, "PACKAGE_LOCK_PATH", package_lock),
            ):
                dependencies.validate_lock_surfaces(
                    {
                        "flask": dependencies.DependencyPin(
                            "python", "Flask", "3.1.3", "requirements.in"
                        ),
                        "ruff": dependencies.DependencyPin(
                            "python", "ruff", "0.16.2", "requirements-dev.in"
                        ),
                    },
                    {
                        "devDependencies:vite": dependencies.DependencyPin(
                            "npm", "vite", "8.2.1", "package.json#devDependencies"
                        )
                    },
                )

    def test_stale_npm_lock_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime_lock = root / "requirements.txt"
            development_lock = root / "requirements-dev.txt"
            package = root / "package.json"
            package_lock = root / "package-lock.json"
            runtime_lock.write_text("", encoding="utf-8")
            development_lock.write_text("", encoding="utf-8")
            package.write_text(
                json.dumps({"devDependencies": {"vite": "^8.2.1"}}), encoding="utf-8"
            )
            package_lock.write_text(
                json.dumps({"packages": {"": {"devDependencies": {"vite": "^8.1.0"}}}}),
                encoding="utf-8",
            )
            with (
                patch.object(
                    dependencies,
                    "PYTHON_SOURCE_PATHS",
                    (root / "requirements.in", root / "requirements-dev.in"),
                ),
                patch.object(dependencies, "PYTHON_LOCK_PATHS", (runtime_lock, development_lock)),
                patch.object(dependencies, "PACKAGE_PATH", package),
                patch.object(dependencies, "PACKAGE_LOCK_PATH", package_lock),
                self.assertRaisesRegex(dependencies.MaintenanceError, "stale for vite"),
            ):
                dependencies.validate_lock_surfaces(
                    {},
                    {
                        "devDependencies:vite": dependencies.DependencyPin(
                            "npm", "vite", "8.2.1", "package.json#devDependencies"
                        )
                    },
                )


class EntrypointTests(unittest.TestCase):
    def test_offline_check_can_skip_local_node_selection(self) -> None:
        pin = dependencies.DependencyPin("python", "Flask", "3.1.3", "requirements.in")
        stdout = io.StringIO()
        with (
            patch.object(dependencies, "ensure_native_wsl_python"),
            patch.object(dependencies, "read_python_source_pins", return_value={"flask": pin}),
            patch.object(dependencies, "read_npm_source_pins", return_value={}),
            patch.object(dependencies, "validate_lock_surfaces"),
            patch.object(dependencies, "validate_mirrored_pins"),
            redirect_stdout(stdout),
        ):
            result = dependencies.check_main(
                ["--offline", "--skip-node-check", "--skip-python-check"]
            )

        self.assertEqual(result, 0)
        self.assertIn("1 direct dependency surfaces checked", stdout.getvalue())

    def test_environment_error_is_actionable(self) -> None:
        stderr = io.StringIO()
        with (
            patch.object(
                dependencies,
                "ensure_native_wsl_python",
                side_effect=dependencies.MaintenanceError("use native Python"),
            ),
            redirect_stderr(stderr),
        ):
            result = dependencies.check_main([])

        self.assertEqual(result, 2)
        self.assertIn("use native Python", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
