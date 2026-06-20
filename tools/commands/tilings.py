from __future__ import annotations

import argparse

from tools import (
    add_periodic_tiling,
    compare_seed,
    generate_tiling_preview,
    inspect_tiling_svg,
    report_tiling_verification_strength,
    scaffold_aperiodic_family,
    sketch_tiling,
    validate_tilings,
    verify_reference_tilings,
)
from tools.cli_support import add_passthrough_command
from tools.command_docs import command_doc


def _validate_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog=command_doc("tilings", "validate").label,
        description=command_doc("tilings", "validate").details,
    )


def _verify_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog=command_doc("tilings", "verify").label,
        description=command_doc("tilings", "verify").details,
    )


def _run_validate(argv: list[str] | None = None) -> int:
    _validate_parser().parse_args(argv)
    return validate_tilings.main()


def _run_verify(argv: list[str] | None = None) -> int:
    _verify_parser().parse_args(argv)
    return verify_reference_tilings.main()


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    add_passthrough_command(
        subparsers,
        name="validate",
        doc=command_doc("tilings", "validate"),
        target_main=_run_validate,
        parser_factory=_validate_parser,
    )
    add_passthrough_command(
        subparsers,
        name="verify",
        doc=command_doc("tilings", "verify"),
        target_main=_run_verify,
        parser_factory=_verify_parser,
    )
    add_passthrough_command(
        subparsers,
        name="report",
        doc=command_doc("tilings", "report"),
        target_main=report_tiling_verification_strength.main,
        parser_factory=report_tiling_verification_strength.build_parser,
    )
    add_passthrough_command(
        subparsers,
        name="preview",
        doc=command_doc("tilings", "preview"),
        target_main=generate_tiling_preview.main,
        parser_factory=generate_tiling_preview.build_parser,
    )
    add_passthrough_command(
        subparsers,
        name="sketch",
        doc=command_doc("tilings", "sketch"),
        target_main=sketch_tiling.main,
        parser_factory=sketch_tiling.build_parser,
    )
    add_passthrough_command(
        subparsers,
        name="inspect-svg",
        doc=command_doc("tilings", "inspect-svg"),
        target_main=inspect_tiling_svg.main,
        parser_factory=inspect_tiling_svg.build_parser,
    )
    add_passthrough_command(
        subparsers,
        name="add-periodic",
        doc=command_doc("tilings", "add-periodic"),
        target_main=add_periodic_tiling.main,
        parser_factory=add_periodic_tiling.build_parser,
    )
    add_passthrough_command(
        subparsers,
        name="scaffold-aperiodic",
        doc=command_doc("tilings", "scaffold-aperiodic"),
        target_main=scaffold_aperiodic_family.main,
        parser_factory=scaffold_aperiodic_family.build_parser,
    )
    add_passthrough_command(
        subparsers,
        name="compare",
        doc=command_doc("tilings", "compare"),
        target_main=compare_seed.main,
        parser_factory=compare_seed.build_parser,
    )
