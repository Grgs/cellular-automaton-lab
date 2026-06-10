from __future__ import annotations

import argparse
import json

from tools import run_coverage
from tools.cli_support import add_passthrough_command
from tools.command_docs import command_doc
from tools.playwright_runner import (
    build_e2e_parser,
    standalone_build_status_payload,
    suite_manifest_payload,
)
from tools.playwright_runner import (
    main as playwright_main,
)


def _playwright_suites(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog=command_doc("test", "playwright-suites").label,
        description=command_doc("test", "playwright-suites").details,
    )
    parser.add_argument("--format", choices=("json", "names"), default="json")
    args = parser.parse_args(argv)
    payload = suite_manifest_payload()
    if args.format == "names":
        for entry in payload:
            print(entry["name"])
        return 0
    print(json.dumps(payload, indent=2))
    return 0


def _standalone_build_status(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog=command_doc("test", "standalone-build-status").label,
        description=command_doc("test", "standalone-build-status").details,
    )
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    args = parser.parse_args(argv)
    payload = standalone_build_status_payload()
    if args.format == "summary":
        status = "current" if payload.get("buildCurrent") else "stale"
        print(f"standalone build: {status} ({payload.get('reason')})")
        return 0
    print(json.dumps(payload, indent=2))
    return 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    add_passthrough_command(
        subparsers,
        name="e2e",
        doc=command_doc("test", "e2e"),
        target_main=playwright_main,
        parser_factory=build_e2e_parser,
    )
    add_passthrough_command(
        subparsers,
        name="coverage",
        doc=command_doc("test", "coverage"),
        target_main=run_coverage.main,
        parser_factory=run_coverage.build_parser,
    )
    suites_parser = subparsers.add_parser(
        "playwright-suites",
        help=command_doc("test", "playwright-suites").summary,
        description=command_doc("test", "playwright-suites").details,
    )
    suites_parser.add_argument("--format", choices=("json", "names"), default="json")
    suites_parser.set_defaults(_run=lambda args: _playwright_suites(["--format", args.format]))
    status_parser = subparsers.add_parser(
        "standalone-build-status",
        help=command_doc("test", "standalone-build-status").summary,
        description=command_doc("test", "standalone-build-status").details,
    )
    status_parser.add_argument("--format", choices=("json", "summary"), default="json")
    status_parser.set_defaults(
        _run=lambda args: _standalone_build_status(["--format", args.format])
    )
