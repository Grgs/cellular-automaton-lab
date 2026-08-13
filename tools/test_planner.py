from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass

from tools._common import ROOT_DIR
from tools.playwright_runner import suite_manifest_payload


@dataclass(frozen=True)
class PlannedCheck:
    command: str
    reason: str


@dataclass(frozen=True)
class ValidationPlan:
    changed_paths: tuple[str, ...]
    focused: tuple[PlannedCheck, ...]
    local_pr_gate: PlannedCheck
    ci: tuple[PlannedCheck, ...]

    def payload(self) -> dict[str, object]:
        return {
            "changed_paths": list(self.changed_paths),
            "focused": [_check_payload(check) for check in self.focused],
            "local_pr_gate": _check_payload(self.local_pr_gate),
            "ci": [_check_payload(check) for check in self.ci],
        }


def _check_payload(check: PlannedCheck) -> dict[str, str]:
    return {"command": check.command, "reason": check.reason}


def _package_scripts() -> dict[str, str]:
    package = json.loads((ROOT_DIR / "package.json").read_text(encoding="utf-8"))
    scripts = package.get("scripts")
    if not isinstance(scripts, dict) or not all(
        isinstance(name, str) and isinstance(value, str) for name, value in scripts.items()
    ):
        raise RuntimeError("package.json must contain a string-valued scripts object")
    return scripts


def _npm_script(name: str) -> str:
    if name not in _package_scripts():
        raise RuntimeError(f"package.json does not define the required script {name!r}")
    return f"npm run {name}"


def _e2e_suite(name: str) -> str:
    suite_names = {str(entry["name"]) for entry in suite_manifest_payload()}
    if name not in suite_names:
        raise RuntimeError(f"Playwright suite manifest does not define {name!r}")
    return f"python -m tools test e2e --suite {name}"


def _normalise_paths(paths: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted({path.replace("\\", "/").lstrip("./") for path in paths if path}))


def changed_paths_from_base(base: str) -> tuple[str, ...]:
    commands = (
        ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base}...HEAD"],
        ["git", "diff", "--name-only", "--diff-filter=ACMR"],
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    )
    paths: list[str] = []
    for command in commands:
        result = subprocess.run(
            command,
            cwd=ROOT_DIR,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "git command failed").strip()
            raise RuntimeError(f"Could not inspect changed paths for {base!r}: {detail}")
        paths.extend(result.stdout.splitlines())
    return _normalise_paths(paths)


def _has_prefix(paths: tuple[str, ...], *prefixes: str) -> bool:
    return any(path.startswith(prefixes) for path in paths)


def _is_docs_path(path: str) -> bool:
    return path.endswith(".md") or path.startswith("docs/")


def _is_frontend_path(path: str) -> bool:
    return path.startswith(("frontend/", "static/", "templates/")) or path == "vite.config.ts"


def _is_standalone_path(path: str) -> bool:
    return path.startswith(("frontend/standalone/", "tools/standalone_")) or path in {
        "tools/standalone_build.py",
        "tools/profile_standalone_runtime.py",
        "tools/smoke_test_standalone.py",
        "tools/commands/build.py",
    }


def _is_tiling_path(path: str) -> bool:
    return path.startswith(
        (
            "backend/simulation/",
            "frontend/geometry/",
            "frontend/test-fixtures/topologies/",
            "tools/sketch_examples/",
        )
    ) or path in {
        "tools/add_periodic_tiling.py",
        "tools/regenerate_periodic_catalog.py",
        "tools/validate_tilings.py",
        "tools/verify_reference_tilings.py",
    }


def _is_generated_fixture_path(path: str) -> bool:
    return path.startswith("frontend/test-fixtures/") or path in {
        "backend/application_commands/contracts.py",
        "docs/TOOLS.md",
        "frontend/application-command-contract.ts",
        "frontend/canvas/family-dead-palette-manifest.json",
        "backend/simulation/topology_family_manifest.py",
        "tools/application_command_contract.py",
    }


def _is_dependency_path(path: str) -> bool:
    return path in {
        ".node-version",
        ".python-version",
        ".pre-commit-config.yaml",
        "package.json",
        "package-lock.json",
        "requirements.in",
        "requirements.txt",
        "requirements-dev.in",
        "requirements-dev.txt",
        "requirements-lock.in",
        "requirements-lock.txt",
        ".github/workflows/ci.yml",
        ".github/workflows/release.yml",
        ".github/workflows/supply-chain-audit.yml",
    }


def _append_unique(checks: list[PlannedCheck], command: str, reason: str) -> None:
    if all(check.command != command for check in checks):
        checks.append(PlannedCheck(command, reason))


def build_validation_plan(paths: list[str] | tuple[str, ...]) -> ValidationPlan:
    changed_paths = _normalise_paths(paths)
    focused: list[PlannedCheck] = []

    dependency_changed = any(_is_dependency_path(path) for path in changed_paths)
    if dependency_changed:
        _append_unique(
            focused,
            "python -m tools dependencies check",
            "registry freshness and lock consistency",
        )
        _append_unique(focused, _npm_script("check:python"), "Python tooling compatibility")
        _append_unique(focused, _npm_script("check:frontend"), "Node tooling compatibility")
        _append_unique(
            focused,
            _npm_script("check:bundle-size:fresh"),
            "bundler output and standalone budgets",
        )

    if any(_is_docs_path(path) for path in changed_paths):
        _append_unique(focused, _npm_script("check:doc-links"), "documentation links")

    frontend_changed = any(_is_frontend_path(path) for path in changed_paths)
    standalone_changed = any(_is_standalone_path(path) for path in changed_paths)
    if frontend_changed:
        _append_unique(focused, _npm_script("typecheck:frontend"), "frontend contracts")
        _append_unique(focused, _npm_script("test:frontend"), "frontend behavior")
        _append_unique(focused, _npm_script("build:frontend"), "server frontend build")
        _append_unique(focused, _e2e_suite("server"), "server browser coverage")
        if not standalone_changed:
            _append_unique(
                focused,
                _e2e_suite("standalone"),
                "standalone browser coverage for shared UI",
            )

    if standalone_changed:
        _append_unique(
            focused, _npm_script("check:bundle-size:fresh"), "standalone build and budget"
        )
        _append_unique(focused, _npm_script("smoke:standalone"), "standalone startup")
        _append_unique(focused, _e2e_suite("standalone"), "standalone browser coverage")

    backend_changed = _has_prefix(changed_paths, "backend/", "app.py")
    api_changed = _has_prefix(
        changed_paths,
        "backend/application_commands/",
        "backend/web/",
        "app.py",
    )
    if backend_changed:
        _append_unique(
            focused,
            "python -m mypy --config-file pyproject.toml",
            "typed backend contracts",
        )
        _append_unique(focused, "python -m pytest -q -rs tests/unit", "backend unit behavior")
    if api_changed:
        _append_unique(focused, "python -m pytest -q -rs tests/api", "HTTP payload contracts")
        _append_unique(focused, _e2e_suite("server"), "server browser coverage for API behavior")

    if any(_is_tiling_path(path) for path in changed_paths):
        _append_unique(focused, "python -m tools tilings validate", "catalog geometry sanity")
        _append_unique(focused, "python -m tools tilings verify", "source-backed tiling invariants")
        _append_unique(focused, _npm_script("fixtures:reference:check"), "reference fixture drift")
        _append_unique(
            focused,
            "python -m tools fixtures frontend --all --check",
            "frontend topology fixture drift",
        )
        _append_unique(
            focused,
            _e2e_suite("topology_and_persistence"),
            "server topology and persistence flow",
        )
        _append_unique(
            focused,
            _e2e_suite("standalone"),
            "standalone browser coverage for catalog output",
        )

    if any(_is_generated_fixture_path(path) for path in changed_paths):
        _append_unique(
            focused,
            "python -m tools repo generated-check",
            "generated surfaces remain current",
        )

    test_paths = tuple(path for path in changed_paths if path.startswith("tests/"))
    source_paths = tuple(path for path in changed_paths if not path.startswith("tests/"))
    if test_paths and not source_paths:
        python_tests = [path for path in test_paths if path.endswith(".py")]
        if python_tests:
            _append_unique(
                focused,
                "python -m pytest -q -rs " + " ".join(python_tests),
                "changed test coverage",
            )
        frontend_tests = [path for path in test_paths if path.endswith((".test.ts", ".spec.ts"))]
        if frontend_tests:
            _append_unique(
                focused,
                _npm_script("test:frontend") + " -- " + " ".join(frontend_tests),
                "changed frontend test coverage",
            )

    if _has_prefix(changed_paths, "tools/"):
        _append_unique(
            focused,
            "python -m pytest -q -rs tests/unit/test_tools_cli.py",
            "public tooling CLI contracts",
        )

    ci = (
        PlannedCheck(
            "CI: backend unit coverage and 75% combined threshold", "coverage aggregation"
        ),
        PlannedCheck("CI: Windows backend unit suite", "platform-specific behavior"),
        PlannedCheck(
            "CI: frontend and standalone artifact packaging", "clean-environment build artifacts"
        ),
    )
    dependency_only = bool(changed_paths) and all(
        _is_dependency_path(path) for path in changed_paths
    )
    local_gate = (
        PlannedCheck(_npm_script("check:dependencies"), "the dependency-update PR gate")
        if dependency_only
        else PlannedCheck(_npm_script("check:ci-local"), "the repository local PR gate")
    )
    return ValidationPlan(
        changed_paths=changed_paths,
        focused=tuple(focused),
        local_pr_gate=local_gate,
        ci=ci,
    )


def render_validation_plan(plan: ValidationPlan) -> str:
    lines = ["Focused checks:"]
    lines.extend(f"- {check.command}  # {check.reason}" for check in plan.focused)
    if not plan.focused:
        lines.append("- No focused checks selected; inspect the changed paths.")
    lines.extend(("", "Before pushing:", f"- {plan.local_pr_gate.command}", "", "CI-owned checks:"))
    lines.extend(f"- {check.command}" for check in plan.ci)
    return "\n".join(lines)
