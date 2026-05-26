from __future__ import annotations

import argparse
from pathlib import Path

from backend.app_shell import render_standalone_document
from tools.command_docs import command_doc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=command_doc("build", "standalone-shell").label,
        description=command_doc("build", "standalone-shell").details,
    )
    parser.add_argument("output_path", nargs="?", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    rendered = render_standalone_document()
    if args.output_path is not None:
        args.output_path.parent.mkdir(parents=True, exist_ok=True)
        args.output_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return 0
