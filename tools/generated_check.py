from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from tools._common import ROOT_DIR
from tools.tools_docs import TOOLS_DOC_PATH, render_tools_reference


BOOTSTRAP_FIXTURE_PATH = ROOT_DIR / "frontend" / "test-fixtures" / "bootstrap-data.json"
CheckName = Literal["tools-docs", "bootstrap", "frontend-fixtures", "reference-fixtures"]
ALL_CHECKS: tuple[CheckName, ...] = (
    "tools-docs",
    "bootstrap",
    "frontend-fixtures",
    "reference-fixtures",
)


@dataclass(frozen=True)
class GeneratedCheckResult:
    name: CheckName
    ok: bool
    detail: str


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT_DIR))
    except ValueError:
        return str(path)


def _check_tools_docs() -> GeneratedCheckResult:
    current = TOOLS_DOC_PATH.read_text(encoding="utf-8")
    expected = render_tools_reference()
    return GeneratedCheckResult(
        "tools-docs",
        current == expected,
        "docs/TOOLS.md is up to date"
        if current == expected
        else "docs/TOOLS.md is out of date; run `python -m tools repo tools-docs --write`",
    )


def _check_bootstrap_fixture() -> GeneratedCheckResult:
    from backend.bootstrap_data import build_bootstrap_payload
    from backend.dev_server import APP_NAME

    current = json.loads(BOOTSTRAP_FIXTURE_PATH.read_text(encoding="utf-8"))
    expected = build_bootstrap_payload({"app_name": APP_NAME})
    return GeneratedCheckResult(
        "bootstrap",
        current == expected,
        f"{_relative(BOOTSTRAP_FIXTURE_PATH)} is up to date"
        if current == expected
        else (
            f"{_relative(BOOTSTRAP_FIXTURE_PATH)} is out of date; run "
            "`python -m tools bootstrap export frontend/test-fixtures/bootstrap-data.json`"
        ),
    )


def _check_frontend_fixtures() -> GeneratedCheckResult:
    from tools.regenerate_frontend_topology_fixtures import (
        discover_fixture_targets,
        fixture_drift_lines,
    )

    targets = discover_fixture_targets(all_targets=True, names=())
    drift = fixture_drift_lines(targets)
    return GeneratedCheckResult(
        "frontend-fixtures",
        not drift,
        "frontend topology fixtures are up to date"
        if not drift
        else (
            "frontend topology fixture drift: "
            + ", ".join(drift)
            + "; run `python -m tools fixtures frontend --all --check` for details"
        ),
    )


def _check_reference_fixtures() -> GeneratedCheckResult:
    from tools.regenerate_reference_fixtures import check_fixture_drift

    drift = check_fixture_drift(
        mode="both",
        all_targets=True,
        geometry=None,
        depth=None,
    )
    return GeneratedCheckResult(
        "reference-fixtures",
        not drift,
        "reference fixtures are up to date"
        if not drift
        else (
            "reference fixture drift: "
            + ", ".join(drift)
            + "; run `python -m tools fixtures reference --all --mode both --check` for details"
        ),
    )


def run_selected_checks(selected: tuple[CheckName, ...]) -> tuple[GeneratedCheckResult, ...]:
    checks = {
        "tools-docs": _check_tools_docs,
        "bootstrap": _check_bootstrap_fixture,
        "frontend-fixtures": _check_frontend_fixtures,
        "reference-fixtures": _check_reference_fixtures,
    }
    return tuple(checks[name]() for name in selected)


def _parse_only(values: list[str]) -> tuple[CheckName, ...]:
    if not values:
        return ALL_CHECKS
    selected: list[CheckName] = []
    for raw_value in values:
        value = cast(CheckName, raw_value)
        if value not in selected:
            selected.append(value)
    return tuple(selected)


def _render_text(results: tuple[GeneratedCheckResult, ...]) -> str:
    lines = ["generated freshness check"]
    for result in results:
        marker = "PASS" if result.ok else "FAIL"
        lines.append(f"[{marker}] {result.name}: {result.detail}")
    lines.append(
        "Generated surfaces are current."
        if all(result.ok for result in results)
        else "Generated surfaces are stale; refresh the failed items before continuing."
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run freshness checks for generated repo-owned files.",
    )
    parser.add_argument(
        "--only",
        action="append",
        choices=ALL_CHECKS,
        default=[],
        help="Run only one generated-surface check. May be repeated.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    selected = _parse_only([str(value) for value in args.only])
    results = run_selected_checks(selected)
    ok = all(result.ok for result in results)
    if args.format == "json":
        print(
            json.dumps(
                {
                    "ok": ok,
                    "checks": [result.__dict__ for result in results],
                },
                indent=2,
            )
        )
    else:
        print(_render_text(results))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
