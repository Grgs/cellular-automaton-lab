"""Report standalone-bundle size by category and gate on per-category budgets.

The standalone build (output/standalone/) is the primary user-facing artifact.
Without a budget gate, dependency upgrades or new bundled assets can silently
balloon the download size for end users. This tool walks the build directory,
classifies each file into a category by glob, sums the raw and gzipped bytes
per category, and compares the totals against the budget defined in
``tools/standalone_bundle_budget.json``. It also writes a JSON manifest so the
sizes can be tracked over time (e.g. a CI job uploading the manifest as an
artifact).

Examples:

    py -3 tools/check_bundle_size.py
    py -3 tools/check_bundle_size.py --build-dir output/standalone
    py -3 tools/check_bundle_size.py --format json
    py -3 tools/check_bundle_size.py --output output/bundle-size.json
    py -3 tools/check_bundle_size.py --baseline output/bundle-size.baseline.json
"""

from __future__ import annotations

import argparse
import fnmatch
import gzip
import io
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

ROOT_DIR: Final[Path] = Path(__file__).resolve().parents[1]
DEFAULT_BUILD_DIR: Final[Path] = ROOT_DIR / "output" / "standalone"
DEFAULT_BUDGET_PATH: Final[Path] = ROOT_DIR / "tools" / "standalone_bundle_budget.json"
GZIP_COMPRESSION_LEVEL: Final[int] = 9


@dataclass(frozen=True)
class CategoryBudget:
    name: str
    patterns: tuple[str, ...]
    raw: int | None
    gzip: int | None


@dataclass
class CategorySizes:
    name: str
    raw_bytes: int = 0
    gzip_bytes: int = 0
    file_count: int = 0
    files: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TotalBudget:
    raw: int | None
    gzip: int | None


@dataclass(frozen=True)
class Budget:
    categories: tuple[CategoryBudget, ...]
    total: TotalBudget


def load_budget(path: Path) -> Budget:
    # Tolerate UTF-8 BOMs that Windows editors and Set-Content commonly emit.
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    raw_categories = payload.get("categories", [])
    if not isinstance(raw_categories, list):
        raise ValueError(f"{path}: 'categories' must be a list")
    categories: list[CategoryBudget] = []
    for raw in raw_categories:
        if not isinstance(raw, dict):
            continue
        name = str(raw.get("name", ""))
        patterns = tuple(str(p) for p in raw.get("patterns", []))
        if not name or not patterns:
            continue
        raw_budget = raw.get("raw")
        gzip_budget = raw.get("gzip")
        categories.append(
            CategoryBudget(
                name=name,
                patterns=patterns,
                raw=int(raw_budget) if isinstance(raw_budget, int) else None,
                gzip=int(gzip_budget) if isinstance(gzip_budget, int) else None,
            )
        )
    total_raw = payload.get("total", {})
    total = TotalBudget(
        raw=int(total_raw.get("raw")) if isinstance(total_raw.get("raw"), int) else None,
        gzip=int(total_raw.get("gzip")) if isinstance(total_raw.get("gzip"), int) else None,
    )
    return Budget(categories=tuple(categories), total=total)


def _classify(relative_path: str, categories: tuple[CategoryBudget, ...]) -> str:
    for category in categories:
        for pattern in category.patterns:
            if fnmatch.fnmatch(relative_path, pattern):
                return category.name
    return "uncategorised"


def _gzip_size(data: bytes) -> int:
    buffer = io.BytesIO()
    # Disable mtime so byte-for-byte determinism is preserved across runs.
    with gzip.GzipFile(
        fileobj=buffer,
        mode="wb",
        compresslevel=GZIP_COMPRESSION_LEVEL,
        mtime=0,
    ) as handle:
        handle.write(data)
    return buffer.tell()


def measure(build_dir: Path, budget: Budget) -> tuple[dict[str, CategorySizes], list[str]]:
    if not build_dir.exists():
        raise FileNotFoundError(f"build directory does not exist: {build_dir}")

    sizes: dict[str, CategorySizes] = {
        c.name: CategorySizes(name=c.name) for c in budget.categories
    }
    sizes.setdefault("uncategorised", CategorySizes(name="uncategorised"))

    uncategorised: list[str] = []
    for path in sorted(build_dir.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(build_dir).as_posix()
        category = _classify(relative, budget.categories)
        if category == "uncategorised":
            uncategorised.append(relative)
        data = path.read_bytes()
        bucket = sizes[category]
        bucket.raw_bytes += len(data)
        bucket.gzip_bytes += _gzip_size(data)
        bucket.file_count += 1
        bucket.files.append(relative)

    return sizes, uncategorised


@dataclass(frozen=True)
class Violation:
    category: str
    metric: str  # "raw" or "gzip"
    actual: int
    budget: int


def evaluate(
    sizes: dict[str, CategorySizes], budget: Budget
) -> tuple[list[Violation], CategorySizes]:
    violations: list[Violation] = []
    by_name = {c.name: c for c in budget.categories}
    for name, info in sizes.items():
        cat = by_name.get(name)
        if cat is None:
            continue
        if cat.raw is not None and info.raw_bytes > cat.raw:
            violations.append(Violation(name, "raw", info.raw_bytes, cat.raw))
        if cat.gzip is not None and info.gzip_bytes > cat.gzip:
            violations.append(Violation(name, "gzip", info.gzip_bytes, cat.gzip))

    grand_total = CategorySizes(name="TOTAL")
    for info in sizes.values():
        grand_total.raw_bytes += info.raw_bytes
        grand_total.gzip_bytes += info.gzip_bytes
        grand_total.file_count += info.file_count

    if budget.total.raw is not None and grand_total.raw_bytes > budget.total.raw:
        violations.append(Violation("TOTAL", "raw", grand_total.raw_bytes, budget.total.raw))
    if budget.total.gzip is not None and grand_total.gzip_bytes > budget.total.gzip:
        violations.append(Violation("TOTAL", "gzip", grand_total.gzip_bytes, budget.total.gzip))

    return violations, grand_total


def _format_bytes(value: int) -> str:
    if value < 1024:
        return f"{value} B"
    if value < 1024 * 1024:
        return f"{value / 1024:.1f} KiB"
    return f"{value / (1024 * 1024):.2f} MiB"


def _format_summary(
    sizes: dict[str, CategorySizes],
    grand_total: CategorySizes,
    budget: Budget,
    uncategorised: list[str],
    violations: list[Violation],
    baseline: dict[str, dict[str, int]] | None,
) -> str:
    lines: list[str] = []
    lines.append(
        f"{'category':<22}{'raw':>14}{'gzip':>14}{'budget raw':>14}{'budget gz':>14}{'delta raw':>12}"
    )
    lines.append("-" * 90)
    by_name = {c.name: c for c in budget.categories}
    for category in budget.categories:
        info = sizes.get(category.name)
        if info is None:
            continue
        cat_budget = by_name[category.name]
        delta = ""
        if baseline is not None:
            prior = baseline.get(category.name, {}).get("raw_bytes")
            if isinstance(prior, int):
                diff = info.raw_bytes - prior
                delta = f"{diff:+d}"
        lines.append(
            f"{category.name:<22}"
            f"{_format_bytes(info.raw_bytes):>14}"
            f"{_format_bytes(info.gzip_bytes):>14}"
            f"{(_format_bytes(cat_budget.raw) if cat_budget.raw else '-'):>14}"
            f"{(_format_bytes(cat_budget.gzip) if cat_budget.gzip else '-'):>14}"
            f"{delta:>12}"
        )
    lines.append("-" * 90)
    delta_total = ""
    if baseline is not None:
        prior_total = baseline.get("TOTAL", {}).get("raw_bytes")
        if isinstance(prior_total, int):
            delta_total = f"{grand_total.raw_bytes - prior_total:+d}"
    lines.append(
        f"{'TOTAL':<22}"
        f"{_format_bytes(grand_total.raw_bytes):>14}"
        f"{_format_bytes(grand_total.gzip_bytes):>14}"
        f"{(_format_bytes(budget.total.raw) if budget.total.raw else '-'):>14}"
        f"{(_format_bytes(budget.total.gzip) if budget.total.gzip else '-'):>14}"
        f"{delta_total:>12}"
    )

    if uncategorised:
        lines.append("")
        lines.append("Uncategorised files (consider adding a budget category):")
        for name in uncategorised:
            lines.append(f"  - {name}")

    if violations:
        lines.append("")
        lines.append("BUDGET VIOLATIONS:")
        for v in violations:
            overage = v.actual - v.budget
            lines.append(
                f"  {v.category} {v.metric}: {_format_bytes(v.actual)} > {_format_bytes(v.budget)} "
                f"(over by {_format_bytes(overage)})"
            )
    else:
        lines.append("")
        lines.append("All categories within budget.")

    return "\n".join(lines)


def _to_serializable(
    sizes: dict[str, CategorySizes], grand_total: CategorySizes, violations: list[Violation]
) -> dict[str, object]:
    return {
        "categories": {
            name: {
                "raw_bytes": info.raw_bytes,
                "gzip_bytes": info.gzip_bytes,
                "file_count": info.file_count,
                "files": info.files,
            }
            for name, info in sizes.items()
        },
        "TOTAL": {
            "raw_bytes": grand_total.raw_bytes,
            "gzip_bytes": grand_total.gzip_bytes,
            "file_count": grand_total.file_count,
        },
        "violations": [
            {"category": v.category, "metric": v.metric, "actual": v.actual, "budget": v.budget}
            for v in violations
        ],
    }


def _load_baseline(path: Path) -> dict[str, dict[str, int]] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, dict[str, int]] = {}
    categories = payload.get("categories", {})
    if isinstance(categories, dict):
        for name, info in categories.items():
            if isinstance(info, dict):
                out[name] = {k: int(v) for k, v in info.items() if isinstance(v, int)}
    total = payload.get("TOTAL")
    if isinstance(total, dict):
        out["TOTAL"] = {k: int(v) for k, v in total.items() if isinstance(v, int)}
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--build-dir",
        type=Path,
        default=DEFAULT_BUILD_DIR,
        help="standalone build directory (default: output/standalone)",
    )
    parser.add_argument(
        "--budget",
        type=Path,
        default=DEFAULT_BUDGET_PATH,
        help="budget JSON path (default: tools/standalone_bundle_budget.json)",
    )
    parser.add_argument(
        "--format",
        choices=("summary", "json"),
        default="summary",
        help="output format (default: summary)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="write the formatted output to this file as well as stdout",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="optional prior bundle-size manifest for delta reporting",
    )
    parser.add_argument(
        "--no-fail",
        action="store_true",
        help="exit 0 even when budget violations are present",
    )
    args = parser.parse_args(argv)

    try:
        budget = load_budget(args.budget)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"failed to load budget {args.budget}: {exc}", file=sys.stderr)
        return 2

    try:
        sizes, uncategorised = measure(args.build_dir, budget)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    violations, grand_total = evaluate(sizes, budget)

    baseline = _load_baseline(args.baseline) if args.baseline is not None else None

    if args.format == "json":
        rendered = json.dumps(
            _to_serializable(sizes, grand_total, violations), indent=2, sort_keys=True
        )
    else:
        rendered = _format_summary(sizes, grand_total, budget, uncategorised, violations, baseline)

    print(rendered)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Persist machine-readable manifest alongside the formatted output so
        # CI artifacts always carry the structured data.
        manifest_path = (
            args.output
            if args.output.suffix == ".json"
            else args.output.with_suffix(args.output.suffix + ".json")
        )
        manifest_path.write_text(
            json.dumps(_to_serializable(sizes, grand_total, violations), indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        if args.format != "json":
            args.output.write_text(rendered + "\n", encoding="utf-8")

    if args.no_fail:
        return 0
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
