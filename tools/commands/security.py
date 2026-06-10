from __future__ import annotations

import argparse

from tools import privacy_guard, run_detect_secrets, run_supply_chain_audit
from tools.cli_support import add_passthrough_command
from tools.command_docs import command_doc


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    add_passthrough_command(
        subparsers,
        name="privacy",
        doc=command_doc("security", "privacy"),
        target_main=privacy_guard.main,
        parser_factory=privacy_guard.build_parser,
    )
    add_passthrough_command(
        subparsers,
        name="secrets",
        doc=command_doc("security", "secrets"),
        target_main=run_detect_secrets.main,
        parser_factory=run_detect_secrets.build_parser,
    )
    add_passthrough_command(
        subparsers,
        name="supply-chain",
        doc=command_doc("security", "supply-chain"),
        target_main=run_supply_chain_audit.main,
        parser_factory=run_supply_chain_audit.build_parser,
    )
