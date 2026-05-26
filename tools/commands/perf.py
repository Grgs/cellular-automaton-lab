from __future__ import annotations

import argparse

from tools import bench_engine, profile_tiling_latency
from tools.command_docs import command_doc
from tools.cli_support import add_passthrough_command


def _bench_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog=command_doc("perf", "bench").label,
        description=command_doc("perf", "bench").details,
    )


def _latency_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog=command_doc("perf", "latency").label,
        description=command_doc("perf", "latency").details,
    )


def _run_bench(argv: list[str] | None = None) -> int:
    _bench_parser().parse_args(argv)
    return bench_engine.main() or 0


def _run_latency(argv: list[str] | None = None) -> int:
    _latency_parser().parse_args(argv)
    return profile_tiling_latency.main() or 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    add_passthrough_command(
        subparsers,
        name="bench",
        doc=command_doc("perf", "bench"),
        target_main=_run_bench,
        parser_factory=_bench_parser,
    )
    add_passthrough_command(
        subparsers,
        name="latency",
        doc=command_doc("perf", "latency"),
        target_main=_run_latency,
        parser_factory=_latency_parser,
    )
