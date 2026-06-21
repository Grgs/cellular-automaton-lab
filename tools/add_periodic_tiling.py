from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from tools._common import ROOT_DIR
from tools.generate_tiling_preview import (
    PreviewDescriptor,
    _generate_polygon_data,
    _suggest_fill_count,
)
from tools.sketch_tiling import emit_descriptor_json, emit_reference_spec, load_sketch, sketch

_DESCRIPTOR_DIR = Path("backend/simulation/data/periodic_face_patterns")
_METADATA_DIR = Path("backend/simulation/data/periodic_face_catalog")
_REFERENCE_DIR = Path("backend/simulation/reference_specs/periodic")
_SKETCH_DIR = Path("tools/sketch_examples")
_REGENERATED_PATHS = (
    Path("backend/simulation/data/periodic_face_catalog.json"),
    Path("frontend/canvas/family-dead-palette-manifest.json"),
    Path("frontend/controls/tiling-preview-data.ts"),
    Path("frontend/test-fixtures/bootstrap-data.json"),
    Path("tools/standalone_bundle_budget.json"),
)
_DEFAULT_TOKENS = {
    "triangle": "toneClay",
    "square": "toneStone",
    "pentagon": "toneLinen",
    "hexagon": "toneCream",
    "octagon": "toneTan",
    "dodecagon": "toneCream",
}


@dataclass(frozen=True)
class InstallMetadata:
    source_url: str
    picker_order: int
    default_cell_size: int
    min_cell_size: int
    max_cell_size: int
    default_rule: str
    palette_tokens: dict[str, str]


@dataclass(frozen=True)
class PlannedWrite:
    path: Path
    content: str


def _module_name(geometry: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", geometry.lower()).strip("_")


def _existing_reference_path(root: Path, geometry: str) -> Path | None:
    matches = [
        path
        for path in sorted((root / _REFERENCE_DIR).glob("*.py"))
        if f'"{geometry}"' in path.read_text(encoding="utf-8")
    ]
    if len(matches) > 1:
        raise ValueError(f"Multiple reference modules already define '{geometry}'.")
    return matches[0] if matches else None


def _parse_palette(values: list[str], kinds: tuple[str, ...]) -> dict[str, str]:
    tokens = {kind: _DEFAULT_TOKENS[kind] for kind in kinds if kind in _DEFAULT_TOKENS}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Invalid palette mapping '{value}'; expected kind=token.")
        kind, token = value.split("=", 1)
        if not kind or not token:
            raise ValueError(f"Invalid palette mapping '{value}'; expected kind=token.")
        tokens[kind] = token
    missing = sorted(set(kinds) - set(tokens))
    if missing:
        raise ValueError(
            "Missing palette tokens for: " + ", ".join(missing) + ". Pass --palette kind=token."
        )
    return tokens


def _palette_entry(
    geometry: str,
    kinds: tuple[str, ...],
    tokens: dict[str, str],
    existing: dict[str, Any] | None,
) -> dict[str, Any]:
    if existing is not None:
        variants = existing.get("variants")
        if isinstance(variants, list):
            for variant in variants:
                if not isinstance(variant, dict):
                    continue
                selector = variant.get("selector", {})
                kind = selector.get("kind") if isinstance(selector, dict) else None
                if kind in tokens:
                    variant["color"] = {"token": tokens[str(kind)]}
            return existing
    return {
        "geometry": geometry,
        "variants": [
            {
                "label": f"{geometry}-{kind}",
                "selector": {"kind": kind},
                "color": {"token": tokens[kind]},
            }
            for kind in kinds
        ],
    }


def _metadata_payload(
    *,
    geometry: str,
    label: str,
    kinds: tuple[str, ...],
    metadata: InstallMetadata,
    descriptor: PreviewDescriptor,
    existing: dict[str, Any] | None,
) -> dict[str, Any]:
    source_urls = [
        str(url) for url in (existing or {}).get("source_urls", []) if isinstance(url, str) and url
    ]
    if metadata.source_url not in source_urls:
        source_urls.append(metadata.source_url)
    existing_palette = (existing or {}).get("palette")
    palette = _palette_entry(
        geometry,
        kinds,
        metadata.palette_tokens,
        existing_palette if isinstance(existing_palette, dict) else None,
    )
    return {
        "geometry": geometry,
        "label": label,
        "picker_group": "Periodic Mixed",
        "picker_order": metadata.picker_order,
        "family": "mixed",
        "viewport_sync_mode": "backend-sync",
        "sizing_policy": {
            "control": "cell_size",
            "default": metadata.default_cell_size,
            "min": metadata.min_cell_size,
            "max": metadata.max_cell_size,
        },
        "default_rule": metadata.default_rule,
        "minimum_grid_dimension": 1,
        "source_urls": source_urls,
        "palette": palette,
        "preview_data": _generate_polygon_data(
            descriptor,
            fill_count=_suggest_fill_count(descriptor),
            geometry=geometry,
            palette_variants=palette["variants"],
        ),
    }


def build_install_plan(
    sketch_path: Path,
    metadata: InstallMetadata,
    *,
    root: Path = ROOT_DIR,
    patch_size: int = 4,
    allow_strip: bool = False,
    reconcile: bool = False,
) -> tuple[PlannedWrite, ...]:
    input_data = load_sketch(sketch_path)
    report = sketch(input_data, patch_size=patch_size)
    if not report.is_valid:
        raise ValueError(
            "Sketch validation failed; run `python -m tools tilings sketch` for details."
        )
    if not allow_strip and not 0.5 <= report.rendered_aspect_ratio <= 2.0:
        raise ValueError(
            f"Rendered aspect ratio {report.rendered_aspect_ratio:.3f} is strip-shaped. "
            "Package a more balanced unit cell or pass --allow-strip."
        )

    geometry = input_data.geometry
    descriptor_path = root / _DESCRIPTOR_DIR / f"{geometry}.json"
    metadata_path = root / _METADATA_DIR / f"{geometry}.json"
    canonical_reference_path = root / _REFERENCE_DIR / f"{_module_name(geometry)}.py"
    reference_path = (
        _existing_reference_path(root, geometry) or canonical_reference_path
        if reconcile
        else canonical_reference_path
    )
    sketch_directory = (root / _SKETCH_DIR).resolve()
    permanent_sketch_path = (
        sketch_path
        if reconcile and sketch_path.resolve().parent == sketch_directory
        else root / _SKETCH_DIR / f"{_module_name(geometry)}.py"
    )
    for path in (descriptor_path, metadata_path, reference_path):
        if path.exists() and not reconcile:
            raise ValueError(f"Refusing to overwrite existing generated file: {path}")

    existing_metadata = (
        json.loads(metadata_path.read_text(encoding="utf-8"))
        if reconcile and metadata_path.exists()
        else None
    )
    kinds = tuple(sorted(report.kind_counts))
    descriptor = emit_descriptor_json(input_data)
    catalog_metadata = _metadata_payload(
        geometry=geometry,
        label=input_data.label,
        kinds=kinds,
        metadata=metadata,
        descriptor=cast(PreviewDescriptor, descriptor),
        existing=existing_metadata,
    )
    writes = [
        PlannedWrite(descriptor_path, json.dumps(descriptor, indent=2) + "\n"),
        PlannedWrite(metadata_path, json.dumps(catalog_metadata, indent=2) + "\n"),
        PlannedWrite(
            reference_path,
            emit_reference_spec(
                input_data,
                report,
                patch_size=patch_size,
                source_url=metadata.source_url,
            ),
        ),
    ]
    if sketch_path.resolve() != permanent_sketch_path.resolve():
        if permanent_sketch_path.exists() and not reconcile:
            raise ValueError(f"Permanent sketch path already exists: {permanent_sketch_path}")
        writes.append(PlannedWrite(permanent_sketch_path, sketch_path.read_text(encoding="utf-8")))
    return tuple(writes)


def _run(command: list[str], *, root: Path) -> None:
    executable = shutil.which(command[0]) or command[0]
    result = subprocess.run([executable, *command[1:]], cwd=root, check=False)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(command)}")


def apply_install_plan(writes: tuple[PlannedWrite, ...], *, root: Path = ROOT_DIR) -> None:
    tracked_paths = {write.path for write in writes}
    tracked_paths.update(root / path for path in _REGENERATED_PATHS)
    backups = {path: path.read_bytes() if path.exists() else None for path in tracked_paths}
    try:
        for write in writes:
            write.path.parent.mkdir(parents=True, exist_ok=True)
            write.path.write_text(write.content, encoding="utf-8")
        python_paths = [str(write.path) for write in writes if write.path.suffix == ".py"]
        if python_paths:
            _run([sys.executable, "-m", "ruff", "format", *python_paths], root=root)
            _run([sys.executable, "-m", "ruff", "check", *python_paths], root=root)
        _run([sys.executable, "-m", "tools", "tilings", "regenerate-catalog"], root=root)
    except Exception:
        for path, content in backups.items():
            if content is None:
                path.unlink(missing_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
        raise


def check_install(
    sketch_path: Path,
    *,
    root: Path = ROOT_DIR,
    patch_size: int = 4,
) -> tuple[str, ...]:
    input_data = load_sketch(sketch_path)
    report = sketch(input_data, patch_size=patch_size)
    geometry = input_data.geometry
    problems: list[str] = []
    if not report.is_valid:
        problems.append("sketch is invalid")
    descriptor_path = root / _DESCRIPTOR_DIR / f"{geometry}.json"
    metadata_path = root / _METADATA_DIR / f"{geometry}.json"
    if not descriptor_path.exists():
        problems.append("descriptor is missing")
    elif json.loads(descriptor_path.read_text(encoding="utf-8")) != emit_descriptor_json(
        input_data
    ):
        problems.append("descriptor is stale")
    if not metadata_path.exists():
        problems.append("catalog metadata is missing")
    else:
        catalog_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if catalog_metadata.get("label") != input_data.label:
            problems.append("catalog label is stale")
    if _existing_reference_path(root, geometry) is None:
        problems.append("reference spec is missing")
    return tuple(problems)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install a validated periodic sketch and authoritative catalog metadata.",
    )
    parser.add_argument("sketch", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument(
        "--reconcile",
        action="store_true",
        help="Upsert existing generated files and authoritative catalog metadata.",
    )
    parser.add_argument("--source-url")
    parser.add_argument("--picker-order", type=int)
    parser.add_argument("--default-cell-size", type=int, default=12)
    parser.add_argument("--min-cell-size", type=int, default=8)
    parser.add_argument("--max-cell-size", type=int, default=20)
    parser.add_argument("--default-rule", default="life-b2-s23")
    parser.add_argument("--palette", action="append", default=[], metavar="KIND=TOKEN")
    parser.add_argument("--patch-size", type=int, default=4)
    parser.add_argument("--allow-strip", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.check:
        problems = list(check_install(args.sketch, patch_size=args.patch_size))
        freshness = subprocess.run(
            [sys.executable, "-m", "tools", "tilings", "regenerate-catalog", "--check"],
            cwd=ROOT_DIR,
            check=False,
            capture_output=True,
            text=True,
        )
        if freshness.returncode:
            problems.append("periodic catalog surfaces are stale")
        if problems:
            for problem in problems:
                print(f"FAIL: {problem}", file=sys.stderr)
            return 1
        print("Periodic tiling installation is current.")
        return 0
    if args.source_url is None or args.picker_order is None:
        parser.error("--source-url and --picker-order are required unless --check is used.")
    input_data = load_sketch(args.sketch)
    kinds = tuple(sorted({str(face["kind"]) for face in input_data.faces}))
    try:
        metadata = InstallMetadata(
            source_url=args.source_url,
            picker_order=args.picker_order,
            default_cell_size=args.default_cell_size,
            min_cell_size=args.min_cell_size,
            max_cell_size=args.max_cell_size,
            default_rule=args.default_rule,
            palette_tokens=_parse_palette(args.palette, kinds),
        )
        writes = build_install_plan(
            args.sketch,
            metadata,
            patch_size=args.patch_size,
            allow_strip=args.allow_strip,
            reconcile=args.reconcile,
        )
        if args.dry_run:
            print("Planned writes:")
            for write in writes:
                print(f"  {write.path.relative_to(ROOT_DIR)}")
            for path in _REGENERATED_PATHS:
                print(f"  {path}")
            return 0
        apply_install_plan(writes)
    except (OSError, ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    action = "Reconciled" if args.reconcile else "Installed"
    print(f"{action} periodic tiling '{input_data.geometry}'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
