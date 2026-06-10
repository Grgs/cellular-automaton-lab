from __future__ import annotations

import argparse
from collections.abc import Callable

from tools.command_docs import CommandDoc

MainFunc = Callable[[list[str] | None], int]
ParserFactory = Callable[[], argparse.ArgumentParser]


def run_passthrough_command(
    argv: list[str],
    *,
    target_main: MainFunc,
    doc: CommandDoc,
    parser_factory: ParserFactory | None = None,
    allow_parser_remainder: bool = False,
) -> int:
    if parser_factory is not None:
        parser = parser_factory()
        parser.prog = doc.label
        if allow_parser_remainder:
            parser.parse_known_args(argv)
        else:
            parser.parse_args(argv)
    return target_main(argv)


def add_passthrough_command(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    *,
    name: str,
    doc: CommandDoc,
    target_main: MainFunc,
    parser_factory: ParserFactory | None = None,
    allow_parser_remainder: bool = False,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        name,
        help=doc.summary,
        description=doc.details,
        add_help=False,
    )
    parser.set_defaults(
        _passthrough_target=target_main,
        _passthrough_doc=doc,
        _passthrough_parser_factory=parser_factory,
        _passthrough_allow_parser_remainder=allow_parser_remainder,
    )
    return parser
