from __future__ import annotations

import argparse
import sys
from importlib import import_module

from tools.cli_support import run_passthrough_command
from tools.command_docs import GROUPS

GROUP_REGISTRARS = {
    "build": "tools.commands.build",
    "rules": "tools.commands.rules",
    "tilings": "tools.commands.tilings",
    "fixtures": "tools.commands.fixtures",
    "bootstrap": "tools.commands.bootstrap",
    "browser": "tools.commands.browser",
    "test": "tools.commands.test",
    "security": "tools.commands.security",
    "perf": "tools.commands.perf",
    "repo": "tools.commands.repo",
}


def _register_group_commands(
    group_key: str,
    command_subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    module = import_module(GROUP_REGISTRARS[group_key])
    module.register(command_subparsers)


def build_parser(*, active_group: str | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools",
        description="Unified Python-first CLI for repo-owned developer tooling.",
    )
    group_subparsers = parser.add_subparsers(dest="group", required=True)
    for group_doc in GROUPS:
        group_parser = group_subparsers.add_parser(
            group_doc.key,
            help=group_doc.intro,
            description=group_doc.intro,
        )
        if active_group == group_doc.key:
            command_subparsers = group_parser.add_subparsers(dest="command", required=True)
            _register_group_commands(group_doc.key, command_subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    argv_list = list(sys.argv[1:] if argv is None else argv)
    if not argv_list:
        parser = build_parser()
        parser.print_help()
        return 0
    if argv_list[0] in {"-h", "--help"}:
        parser = build_parser()
        parser.parse_args(argv_list)
        return 0

    active_group = argv_list[0]
    parser = build_parser(active_group=active_group if active_group in GROUP_REGISTRARS else None)
    args, unknown = parser.parse_known_args(argv_list)
    passthrough_target = getattr(args, "_passthrough_target", None)
    if passthrough_target is not None:
        return int(
            run_passthrough_command(
                list(unknown),
                target_main=passthrough_target,
                doc=args._passthrough_doc,
                parser_factory=args._passthrough_parser_factory,
                allow_parser_remainder=bool(
                    getattr(args, "_passthrough_allow_parser_remainder", False)
                ),
            )
        )
    runner = getattr(args, "_run", None)
    if runner is None:
        parser.error("missing command runner")
    if unknown:
        parser.error(f"unrecognized arguments: {' '.join(unknown)}")
    return int(runner(args))
