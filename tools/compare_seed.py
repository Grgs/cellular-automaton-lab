"""CLI for cross-topology seed comparison.

Maps one seed onto many tilings through a canonical traversal, runs the same
rule on each, and reports how the end states differ. Backs
``python -m tools tilings compare``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from backend.simulation.seeding import compare_seed
from backend.simulation.seeding.comparison import (
    DEFAULT_GRID_SIZE,
    DEFAULT_RULE,
    DEFAULT_STEPS,
    SeedComparison,
)
from backend.simulation.seeding.traversal import DEFAULT_TRAVERSAL, TRAVERSALS

# A small, recognisable default: an R-pentomino-style smear (5 live cells).
DEFAULT_SEED = "01100 11000 01000"

_COLUMNS = (
    ("geometry", "geometry", 26),
    ("family", "family", 10),
    ("cells", "cell_count", 6),
    ("seed", "seed_cells", 5),
    ("live0", "initial_population", 6),
    ("liveN", "final_population", 6),
    ("norm", "normalized_population", 6),
    ("class", "classification", 16),
    ("note", "note", 0),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools tilings compare",
        description="Compare one seed under one rule across many tilings.",
    )
    parser.add_argument(
        "seed",
        nargs="?",
        default=DEFAULT_SEED,
        help=f"Seed bit string (separators ignored). Default: {DEFAULT_SEED!r}.",
    )
    parser.add_argument(
        "--rule",
        default=DEFAULT_RULE,
        help=f"Rule name applied to every tiling (default: {DEFAULT_RULE}).",
    )
    parser.add_argument(
        "--traversal",
        choices=sorted(TRAVERSALS),
        default=DEFAULT_TRAVERSAL,
        help=f"Seed-to-cell ordering (default: {DEFAULT_TRAVERSAL}).",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=DEFAULT_STEPS,
        help=f"Maximum generations to run per tiling (default: {DEFAULT_STEPS}).",
    )
    parser.add_argument(
        "--grid-size",
        type=int,
        default=DEFAULT_GRID_SIZE,
        help=f"Grid dimension for lattice tilings (default: {DEFAULT_GRID_SIZE}).",
    )
    parser.add_argument(
        "--geometries",
        default=None,
        help="Comma-separated geometry keys to limit the sweep (default: all).",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format (default: table).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional file to write the report to (default: stdout).",
    )
    return parser


def _format_cell(result_dict: dict[str, object], attr: str) -> str:
    value = result_dict.get(attr)
    if value is None:
        return ""
    if attr == "normalized_population" and isinstance(value, (int, float)):
        return f"{value:.2f}"
    return str(value)


def render_table(comparison: SeedComparison) -> str:
    rows = [result.to_dict() for result in comparison.results]
    rows.sort(key=lambda row: (str(row["family"]), str(row["geometry"])))

    widths = {}
    for header, attr, minimum in _COLUMNS:
        longest = max((len(_format_cell(row, attr)) for row in rows), default=0)
        widths[attr] = max(minimum, len(header), longest)

    def render_row(values: dict[str, str]) -> str:
        return "  ".join(values[attr].ljust(widths[attr]) for _, attr, _ in _COLUMNS).rstrip()

    header_line = render_row({attr: header for header, attr, _ in _COLUMNS})
    separator = render_row({attr: "-" * widths[attr] for _, attr, _ in _COLUMNS})

    lines = [
        f"seed={comparison.seed!r}  bits={comparison.seed_bits}  "
        f"rule={comparison.rule_name}  traversal={comparison.traversal}  "
        f"steps={comparison.steps}",
        f"tilings={len(comparison.results)}  degenerate={comparison.degenerate}",
        "",
        header_line,
        separator,
    ]
    for row in rows:
        lines.append(render_row({attr: _format_cell(row, attr) for _, attr, _ in _COLUMNS}))
    if comparison.degenerate:
        lines.append("")
        lines.append("WARNING: seed extincts quickly on most tilings; not a meaningful comparison.")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    geometries = (
        tuple(part.strip() for part in args.geometries.split(",") if part.strip())
        if args.geometries
        else None
    )
    try:
        comparison = compare_seed(
            seed=args.seed,
            rule_name=args.rule,
            geometries=geometries,
            traversal=args.traversal,
            steps=args.steps,
            grid_size=args.grid_size,
        )
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if args.format == "json":
        rendered = json.dumps(comparison.to_dict(), indent=2) + "\n"
    else:
        rendered = render_table(comparison)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
