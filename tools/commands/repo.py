from __future__ import annotations

import argparse

from tools import dev_processes, generated_check, release_check, run_python_style
from tools.command_docs import command_doc
from tools.cli_support import add_passthrough_command
from tools.tools_docs import build_parser as tools_docs_parser, main as tools_docs_main


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    add_passthrough_command(
        subparsers,
        name="processes",
        doc=command_doc("repo", "processes"),
        target_main=dev_processes.main,
        parser_factory=dev_processes.build_parser,
    )
    add_passthrough_command(
        subparsers,
        name="cleanup",
        doc=command_doc("repo", "cleanup"),
        target_main=dev_processes.cleanup_main,
        parser_factory=dev_processes.build_cleanup_parser,
    )
    add_passthrough_command(
        subparsers,
        name="python-style",
        doc=command_doc("repo", "python-style"),
        target_main=run_python_style.main,
        parser_factory=run_python_style.build_parser,
    )
    add_passthrough_command(
        subparsers,
        name="tools-docs",
        doc=command_doc("repo", "tools-docs"),
        target_main=tools_docs_main,
        parser_factory=tools_docs_parser,
    )
    add_passthrough_command(
        subparsers,
        name="generated-check",
        doc=command_doc("repo", "generated-check"),
        target_main=generated_check.main,
        parser_factory=generated_check.build_parser,
    )
    add_passthrough_command(
        subparsers,
        name="release-check",
        doc=command_doc("repo", "release-check"),
        target_main=release_check.main,
        parser_factory=release_check.build_parser,
    )
