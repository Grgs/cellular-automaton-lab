from __future__ import annotations

import argparse

from tools import (
    bench_engine,
    profile_refactor_baseline,
    profile_standalone_runtime,
    profile_tiling_latency,
)
from tools.cli_support import add_passthrough_command
from tools.command_docs import command_doc


def _bench_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog=command_doc("perf", "bench").label,
        description=command_doc("perf", "bench").details,
    )


def _latency_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=command_doc("perf", "latency").label,
        description=command_doc("perf", "latency").details,
    )
    parser.add_argument(
        "--allow-oversize",
        action="store_true",
        help="include intentionally oversized stress cases",
    )
    return parser


def _baseline_parser() -> argparse.ArgumentParser:
    return profile_refactor_baseline.build_parser()


def _standalone_runtime_parser() -> argparse.ArgumentParser:
    return profile_standalone_runtime.build_parser()


def _run_bench(argv: list[str] | None = None) -> int:
    _bench_parser().parse_args(argv)
    return bench_engine.main() or 0


def _run_latency(argv: list[str] | None = None) -> int:
    _latency_parser().parse_args(argv)
    return profile_tiling_latency.main(argv) or 0


def _run_baseline(argv: list[str] | None = None) -> int:
    return profile_refactor_baseline.main(argv)


def _run_standalone_runtime(argv: list[str] | None = None) -> int:
    return profile_standalone_runtime.main(argv)


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
    add_passthrough_command(
        subparsers,
        name="baseline",
        doc=command_doc("perf", "baseline"),
        target_main=_run_baseline,
        parser_factory=_baseline_parser,
    )
    add_passthrough_command(
        subparsers,
        name="standalone-runtime",
        doc=command_doc("perf", "standalone-runtime"),
        target_main=_run_standalone_runtime,
        parser_factory=_standalone_runtime_parser,
    )
