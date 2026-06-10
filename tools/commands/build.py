from __future__ import annotations

import argparse

from tools import check_bundle_size, standalone_shell
from tools._common import ROOT_DIR
from tools.cli_support import add_passthrough_command
from tools.command_docs import command_doc
from tools.standalone_build import build_parser as build_standalone_parser
from tools.standalone_build import main as build_standalone


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    add_passthrough_command(
        subparsers,
        name="standalone",
        doc=command_doc("build", "standalone"),
        target_main=build_standalone,
        parser_factory=lambda: build_standalone_parser(ROOT_DIR),
    )
    add_passthrough_command(
        subparsers,
        name="standalone-shell",
        doc=command_doc("build", "standalone-shell"),
        target_main=standalone_shell.main,
        parser_factory=standalone_shell.build_parser,
    )
    add_passthrough_command(
        subparsers,
        name="bundle-size",
        doc=command_doc("build", "bundle-size"),
        target_main=check_bundle_size.main,
        parser_factory=check_bundle_size.build_parser,
    )
