from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _hook_config(config: str, hook_id: str) -> str:
    _, hook = config.split(f"      - id: {hook_id}", maxsplit=1)
    return hook.split("\n      - id:", maxsplit=1)[0]


def _hook_files_pattern(hook: str) -> str:
    match = re.search(r"^        files: (.+)$", hook, flags=re.MULTILINE)
    if match is None:
        raise AssertionError("hook is missing a files filter")
    return match.group(1)


class RepoGuardConfigTests(unittest.TestCase):
    def test_ci_uses_repository_runtime_version_files(self) -> None:
        node_version = (ROOT / ".node-version").read_text(encoding="utf-8").strip()
        python_version = (ROOT / ".python-version").read_text(encoding="utf-8").strip()
        self.assertRegex(node_version, r"^\d+\.\d+\.\d+$")
        self.assertRegex(python_version, r"^\d+\.\d+\.\d+$")

        for relative in (
            ".github/workflows/ci.yml",
            ".github/workflows/release.yml",
            ".github/workflows/supply-chain-audit.yml",
        ):
            workflow = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn('node-version: "22"', workflow)
            self.assertNotIn('python-version: "3.13"', workflow)
            self.assertIn('node-version-file: ".node-version"', workflow)
            self.assertIn('python-version-file: ".python-version"', workflow)

    def test_dependency_scripts_use_repository_tooling(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        scripts = package["scripts"]

        self.assertEqual(
            scripts["dependencies:update"],
            "node ./tools/internal/python_tools_entry.mjs dependencies update",
        )
        self.assertIn("dependencies check --audit", scripts["check:dependencies"])

    def test_fresh_bundle_guard_builds_before_measuring(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        scripts = package["scripts"]

        self.assertEqual(
            scripts["check:bundle-size:fresh"],
            "npm run build:frontend:standalone && npm run check:bundle-size",
        )
        self.assertIn("npm run check:bundle-size:fresh", scripts["check:ci-local"])

    def test_local_ci_gate_starts_with_full_repository_privacy_scan(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        scripts = package["scripts"]

        self.assertEqual(
            scripts["check:privacy"],
            "node ./tools/internal/python_tools_entry.mjs security privacy --all-files",
        )
        self.assertTrue(scripts["check:ci-local"].startswith("npm run check:privacy && "))

    def test_security_guide_uses_the_repository_managed_hooks(self) -> None:
        security_guide = (ROOT / "SECURITY.md").read_text(encoding="utf-8")

        self.assertIn("git config core.hooksPath .githooks", security_guide)
        self.assertNotIn("pre_commit install", security_guide)

    def test_pre_push_runs_the_fresh_bundle_guard(self) -> None:
        config = (ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
        hook = _hook_config(config, "standalone-bundle-budget")

        self.assertIn("entry: npm run check:bundle-size:fresh", hook)
        self.assertIn("pass_filenames: false", hook)
        self.assertIn("stages: [pre-push, manual]", hook)

    def test_doc_links_use_the_filesystem_checker(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(
            package["scripts"]["check:doc-links"],
            "node ./tools/internal/check_doc_links.mjs",
        )

        config = (ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
        pattern = _hook_files_pattern(_hook_config(config, "doc-links"))
        self.assertEqual(pattern, r"^(?:[^/]+\.md|\.github/.*\.md|docs/.*\.md)$")

        for path in ("README.md", ".github/PULL_REQUEST_TEMPLATE.md", "docs/TESTING.md"):
            with self.subTest(path=path):
                self.assertIsNotNone(re.fullmatch(pattern, path))
        for path in ("examples/README.md", "docs/diagram.svg", "frontend/standalone.ts"):
            with self.subTest(path=path):
                self.assertIsNone(re.fullmatch(pattern, path))

    def test_fresh_bundle_guard_only_runs_for_standalone_build_inputs(self) -> None:
        config = (ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
        pattern = _hook_files_pattern(_hook_config(config, "standalone-bundle-budget"))
        self.assertEqual(
            pattern,
            r"^(?:(?:backend|config)/.*\.(?:py|json)|frontend/.*|static/(?:css/styles\.css|favicon\.svg)|(?:package(?:-lock)?\.json|vite\.config\.ts|tools/(?:_common|provenance|standalone_build)\.py))$",
        )

        # Derived from standalone_build.py: its Python bundle, Vite source tree,
        # staged shell assets, and the builder/configuration helpers it invokes.
        for path in (
            "backend/app_shell.py",
            "config/defaults.json",
            "frontend/standalone.ts",
            "frontend/shell/app-shell-body.html",
            "static/css/styles.css",
            "static/favicon.svg",
            "package.json",
            "package-lock.json",
            "vite.config.ts",
            "tools/standalone_build.py",
            "tools/provenance.py",
            "tools/_common.py",
        ):
            with self.subTest(path=path):
                self.assertIsNotNone(re.fullmatch(pattern, path))
        for path in (
            "README.md",
            "docs/TESTING.md",
            "examples/README.md",
            "static/images/diagram.svg",
            "tools/check_bundle_size.py",
            "tools/standalone_bundle_budget.json",
            "tests/unit/test_repo_guard_config.py",
        ):
            with self.subTest(path=path):
                self.assertIsNone(re.fullmatch(pattern, path))

    def test_full_repository_security_scans_remain_unconditional_at_pre_push(self) -> None:
        config = (ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
        for hook_id in ("privacy-guard-push", "detect-secrets-push"):
            with self.subTest(hook_id=hook_id):
                hook = _hook_config(config, hook_id)
                self.assertNotIn("files:", hook)
                self.assertIn("pass_filenames: false", hook)
                self.assertIn("stages: [pre-push, manual]", hook)

    def test_python_typecheck_runs_for_python_changes_before_commit_and_push(self) -> None:
        config = (ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
        hook = _hook_config(config, "python-typecheck")

        self.assertIn("entry: npm run typecheck:python", hook)
        self.assertIn(
            r"files: ^(?:app\.py|pyproject\.toml|(?:backend|tests|tools)/.*\.py)$",
            hook,
        )
        self.assertIn("pass_filenames: false", hook)
        self.assertIn("stages: [pre-commit, pre-push, manual]", hook)

    def test_repository_managed_pre_push_dispatcher_is_tracked(self) -> None:
        dispatcher = (ROOT / ".githooks" / "pre-push").read_text(encoding="utf-8")

        self.assertIn("PRE_COMMIT_HOOK_TYPE=pre-push", dispatcher)
        self.assertIn('exec "$HOOK_DIR/pre-commit" "$@"', dispatcher)

    def test_hook_launcher_prefers_native_pre_commit_before_windows_fallback(self) -> None:
        launcher = (ROOT / ".githooks" / "pre-commit").read_text(encoding="utf-8")

        self.assertIn('case "$(uname -s)" in', launcher)
        self.assertIn("MINGW*|MSYS*|CYGWIN*)", launcher)
        self.assertLess(
            launcher.index("if command -v pre-commit"),
            launcher.index('if [ -n "$windows_pre_commit" ]'),
        )


if __name__ == "__main__":
    unittest.main()
