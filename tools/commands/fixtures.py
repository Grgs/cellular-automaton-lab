from __future__ import annotations

import argparse

from tools import regenerate_frontend_topology_fixtures, regenerate_reference_fixtures
from tools.command_docs import command_doc
from tools.cli_support import add_passthrough_command


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    add_passthrough_command(
        subparsers,
        name="reference",
        doc=command_doc("fixtures", "reference"),
        target_main=regenerate_reference_fixtures.main,
        parser_factory=regenerate_reference_fixtures.build_parser,
    )
    add_passthrough_command(
        subparsers,
        name="frontend",
        doc=command_doc("fixtures", "frontend"),
        target_main=regenerate_frontend_topology_fixtures.main,
        parser_factory=regenerate_frontend_topology_fixtures.build_parser,
    )
