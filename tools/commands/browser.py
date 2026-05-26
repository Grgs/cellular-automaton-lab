from __future__ import annotations

import argparse

from tools.command_docs import command_doc
from tools.cli_support import add_passthrough_command
from tools.render_review import (
    browser_check,
    diff_review,
    family_sample_workbench,
    geometry_cleanup_workbench,
    review,
    sweep,
)
from tools import smoke_test_standalone


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    add_passthrough_command(
        subparsers,
        name="review",
        doc=command_doc("browser", "review"),
        target_main=review.main,
        parser_factory=review.build_parser,
    )
    add_passthrough_command(
        subparsers,
        name="check",
        doc=command_doc("browser", "check"),
        target_main=browser_check.main,
        parser_factory=browser_check.build_parser,
    )
    add_passthrough_command(
        subparsers,
        name="sweep",
        doc=command_doc("browser", "sweep"),
        target_main=sweep.main,
        parser_factory=sweep.build_parser,
    )
    add_passthrough_command(
        subparsers,
        name="diff",
        doc=command_doc("browser", "diff"),
        target_main=diff_review.main,
        parser_factory=diff_review.build_parser,
    )
    add_passthrough_command(
        subparsers,
        name="workbench-samples",
        doc=command_doc("browser", "workbench-samples"),
        target_main=family_sample_workbench.main,
        parser_factory=family_sample_workbench.build_parser,
    )
    add_passthrough_command(
        subparsers,
        name="workbench-cleanup",
        doc=command_doc("browser", "workbench-cleanup"),
        target_main=geometry_cleanup_workbench.main,
        parser_factory=geometry_cleanup_workbench.build_parser,
    )
    add_passthrough_command(
        subparsers,
        name="smoke-standalone",
        doc=command_doc("browser", "smoke-standalone"),
        target_main=smoke_test_standalone.main,
        parser_factory=smoke_test_standalone.build_parser,
    )
