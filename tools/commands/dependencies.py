from __future__ import annotations

import argparse

from tools import dependency_maintenance
from tools.cli_support import add_passthrough_command
from tools.command_docs import command_doc


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    add_passthrough_command(
        subparsers,
        name="check",
        doc=command_doc("dependencies", "check"),
        target_main=dependency_maintenance.check_main,
        parser_factory=dependency_maintenance.build_check_parser,
    )
    add_passthrough_command(
        subparsers,
        name="update",
        doc=command_doc("dependencies", "update"),
        target_main=dependency_maintenance.update_main,
        parser_factory=dependency_maintenance.build_update_parser,
    )
