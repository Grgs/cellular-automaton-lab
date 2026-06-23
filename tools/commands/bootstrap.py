from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.bootstrap_data import build_bootstrap_payload
from backend.dev_server import APP_NAME
from tools._common import write_text_lf
from tools.command_docs import command_doc


def _export_bootstrap(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog=command_doc("bootstrap", "export").label,
        description=command_doc("bootstrap", "export").details,
    )
    parser.add_argument("output_path", type=Path)
    args = parser.parse_args(argv)
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_bootstrap_payload({"app_name": APP_NAME})
    write_text_lf(args.output_path, json.dumps(payload, indent=2))
    return 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "export",
        help=command_doc("bootstrap", "export").summary,
        description=command_doc("bootstrap", "export").details,
    )
    parser.add_argument("output_path")
    parser.set_defaults(_run=lambda args: _export_bootstrap([args.output_path]))
