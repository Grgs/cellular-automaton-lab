from __future__ import annotations

import unittest

from tools.test_planner import build_validation_plan, render_validation_plan


def _commands(paths: list[str]) -> set[str]:
    return {check.command for check in build_validation_plan(paths).focused}


class TestPlannerTests(unittest.TestCase):
    def test_documentation_paths_plan_link_check(self) -> None:
        self.assertEqual(_commands(["docs/TESTING_CHANGES.md"]), {"npm run check:doc-links"})

    def test_shared_frontend_paths_cover_server_and_standalone_browsers(self) -> None:
        commands = _commands(["frontend/controls/shell-clicks.ts"])

        self.assertTrue(
            {
                "npm run typecheck:frontend",
                "npm run test:frontend",
                "npm run build:frontend",
                "python -m tools test e2e --suite server",
                "python -m tools test e2e --suite standalone",
            }.issubset(commands)
        )

    def test_backend_api_paths_plan_type_unit_api_and_server_checks(self) -> None:
        commands = _commands(["backend/web/routes.py"])

        self.assertTrue(
            {
                "python -m mypy --config-file pyproject.toml",
                "python -m pytest -q -rs tests/unit",
                "python -m pytest -q -rs tests/api",
                "python -m tools test e2e --suite server",
            }.issubset(commands)
        )

    def test_standalone_paths_plan_build_smoke_and_browser_coverage(self) -> None:
        commands = _commands(["frontend/standalone/worker-client.ts"])

        self.assertTrue(
            {
                "npm run check:bundle-size:fresh",
                "npm run smoke:standalone",
                "python -m tools test e2e --suite standalone",
            }.issubset(commands)
        )

    def test_standalone_runtime_profiler_plans_standalone_validation(self) -> None:
        commands = _commands(["tools/profile_standalone_runtime.py"])

        self.assertIn("npm run smoke:standalone", commands)
        self.assertIn("python -m tools test e2e --suite standalone", commands)

    def test_tiling_catalog_paths_plan_catalog_fixture_and_runtime_checks(self) -> None:
        commands = _commands(["backend/simulation/topology_catalog.py"])

        self.assertTrue(
            {
                "python -m tools tilings validate",
                "python -m tools tilings verify",
                "npm run fixtures:reference:check",
                "python -m tools fixtures frontend --all --check",
                "python -m tools test e2e --suite topology_and_persistence",
                "python -m tools test e2e --suite standalone",
            }.issubset(commands)
        )

    def test_generated_fixture_paths_plan_generated_check(self) -> None:
        commands = _commands(["frontend/test-fixtures/topologies/fixture-manifest.json"])

        self.assertIn("python -m tools repo generated-check", commands)

    def test_test_only_paths_run_changed_python_tests(self) -> None:
        commands = _commands(["tests/unit/test_tools_cli.py"])

        self.assertIn("python -m pytest -q -rs tests/unit/test_tools_cli.py", commands)

    def test_plan_uses_the_package_pr_gate_and_has_three_text_tiers(self) -> None:
        plan = build_validation_plan(["docs/TESTING_CHANGES.md"])
        text = render_validation_plan(plan)

        self.assertEqual(plan.local_pr_gate.command, "npm run check:ci-local")
        self.assertIn("Focused checks:", text)
        self.assertIn("Before pushing:", text)
        self.assertIn("CI-owned checks:", text)


if __name__ == "__main__":
    unittest.main()
