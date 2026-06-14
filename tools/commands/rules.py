from __future__ import annotations

import argparse

from tools import rule_review
from tools.cli_support import add_passthrough_command
from tools.command_docs import command_doc


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    add_passthrough_command(
        subparsers,
        name="review",
        doc=command_doc("rules", "review"),
        target_main=rule_review.main,
        parser_factory=rule_review.build_parser,
    )
