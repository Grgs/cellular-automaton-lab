from __future__ import annotations

import argparse
import ast
import json
import re
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
    update_preview_source,
)
from tools.sketch_tiling import emit_descriptor_json, emit_reference_spec, load_sketch, sketch

_DESCRIPTOR_DIR = Path("backend/simulation/data/periodic_face_patterns")
_REFERENCE_DIR = Path("backend/simulation/reference_specs/periodic")
_SKETCH_DIR = Path("tools/sketch_examples")
_MANIFEST_PATH = Path("backend/simulation/topology_family_manifest.py")
_PALETTE_PATH = Path("frontend/canvas/family-dead-palette-manifest.json")
_PREVIEW_PATH = Path("frontend/controls/tiling-preview-data.ts")
_BOOTSTRAP_PATH = Path("frontend/test-fixtures/bootstrap-data.json")
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


def _constant_name(geometry: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", geometry.upper()).strip("_") + "_GEOMETRY"


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


def _manifest_assignment(tree: ast.Module) -> ast.Assign | ast.AnnAssign:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == "TOPOLOGY_FAMILY_MANIFEST"
                for target in node.targets
            ):
                return node
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "TOPOLOGY_FAMILY_MANIFEST"
        ):
            return node
    raise ValueError("TOPOLOGY_FAMILY_MANIFEST assignment was not found.")


def update_manifest_source(
    source: str,
    *,
    geometry: str,
    label: str,
    metadata: InstallMetadata,
    reconcile: bool = False,
) -> str:
    tree = ast.parse(source)
    assignment = _manifest_assignment(tree)
    if assignment.end_lineno is None or assignment.lineno is None:
        raise ValueError("Topology manifest source positions are unavailable.")
    constant = _constant_name(geometry)
    constants = {
        target.id: node.value.value
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (node.targets if isinstance(node, ast.Assign) else (node.target,))
        if isinstance(target, ast.Name)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    }
    manifest_value = assignment.value
    if not isinstance(manifest_value, ast.Dict):
        raise ValueError("TOPOLOGY_FAMILY_MANIFEST must be a dictionary literal.")
    existing_entry: tuple[ast.expr, ast.expr] | None = None
    for key, value in zip(manifest_value.keys, manifest_value.values, strict=True):
        if key is None:
            continue
        resolved_key = (
            constants.get(key.id)
            if isinstance(key, ast.Name)
            else key.value
            if isinstance(key, ast.Constant)
            else None
        )
        if resolved_key == geometry:
            existing_entry = (key, value)
            break
    existing_constant = next(
        (name for name, value in constants.items() if value == geometry),
        None,
    )
    if (existing_entry is not None or existing_constant is not None) and not reconcile:
        raise ValueError(f"Geometry '{geometry}' is already present in the topology manifest.")

    lines = source.splitlines(keepends=True)
    constant_line = f"{constant} = {json.dumps(geometry)}\n\n"
    entry_constant = existing_constant or constant
    entry = (
        f"    {entry_constant}: _single_variant_family(\n"
        f"        tiling_family={entry_constant},\n"
        f"        label={json.dumps(label)},\n"
        '        picker_group="Periodic Mixed",\n'
        f"        picker_order={metadata.picker_order},\n"
        '        family="mixed",\n'
        '        viewport_sync_mode="backend-sync",\n'
        "        sizing_policy=SizingPolicyDefinition(\n"
        f"            CELL_SIZE_CONTROL, {metadata.default_cell_size}, "
        f"{metadata.min_cell_size}, {metadata.max_cell_size}\n"
        "        ),\n"
        f"        default_rule={json.dumps(metadata.default_rule)},\n"
        "        minimum_grid_dimension=1,\n"
        "    ),\n"
    )
    if existing_entry is not None:
        key, value = existing_entry
        if key.lineno is None or value.end_lineno is None:
            raise ValueError("Existing topology manifest entry has no source position.")
        lines[key.lineno - 1 : value.end_lineno] = entry.splitlines(keepends=True)
        return "".join(lines)

    if existing_constant is None:
        lines.insert(assignment.lineno - 1, constant_line)
        closing_index = assignment.end_lineno
    else:
        closing_index = assignment.end_lineno - 1
    lines.insert(closing_index, entry)
    return "".join(lines)


def _palette_entry(geometry: str, kinds: tuple[str, ...], tokens: dict[str, str]) -> dict[str, Any]:
    missing = sorted(set(kinds) - set(tokens))
    if missing:
        raise ValueError(
            "Missing palette tokens for: " + ", ".join(missing) + ". Pass --palette kind=token."
        )
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


def update_palette_source(
    source: str,
    entry: dict[str, Any],
    *,
    reconcile: bool = False,
) -> str:
    payload = json.loads(source)
    families = payload.get("families")
    if not isinstance(families, list):
        raise ValueError("Palette manifest does not contain a families list.")
    geometry = entry["geometry"]
    existing_index = next(
        (
            index
            for index, family in enumerate(families)
            if isinstance(family, dict) and family.get("geometry") == geometry
        ),
        None,
    )
    if existing_index is not None:
        if not reconcile:
            raise ValueError(f"Palette entry for '{geometry}' already exists.")
        existing_family = families[existing_index]
        existing_labels = {
            variant.get("selector", {}).get("kind"): variant.get("label")
            for variant in existing_family.get("variants", [])
            if isinstance(variant, dict)
        }
        for variant in entry.get("variants", []):
            kind = variant.get("selector", {}).get("kind")
            if kind in existing_labels and existing_labels[kind]:
                variant["label"] = existing_labels[kind]
        if families[existing_index] == entry:
            return source
        marker = f'"geometry": {json.dumps(geometry)}'
        marker_index = source.find(marker)
        object_start = source.rfind("{", 0, marker_index)
        if marker_index < 0 or object_start < 0:
            raise ValueError(f"Palette source block for '{geometry}' was not found.")
        depth = 0
        in_string = False
        escaped = False
        object_end = -1
        for index in range(object_start, len(source)):
            character = source[index]
            if in_string:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    in_string = False
                continue
            if character == '"':
                in_string = True
            elif character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    object_end = index + 1
                    break
        if object_end < 0:
            raise ValueError(f"Palette source block for '{geometry}' is unterminated.")
        rendered = json.dumps(entry, indent=2)
        indented = "\n".join("    " + line for line in rendered.splitlines())
        return source[:object_start] + indented.lstrip() + source[object_end:]
    rendered = json.dumps(entry, indent=2)
    indented = "\n".join("    " + line for line in rendered.splitlines())
    marker = "\n  ]\n}"
    if marker not in source:
        raise ValueError("Palette manifest closing marker was not found.")
    separator = "," if families else ""
    return source.replace(marker, f"{separator}\n{indented}{marker}", 1)


def _parse_palette(values: list[str], kinds: tuple[str, ...]) -> dict[str, str]:
    tokens = {kind: _DEFAULT_TOKENS[kind] for kind in kinds if kind in _DEFAULT_TOKENS}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Invalid palette mapping '{value}'; expected kind=token.")
        kind, token = value.split("=", 1)
        if not kind or not token:
            raise ValueError(f"Invalid palette mapping '{value}'; expected kind=token.")
        tokens[kind] = token
    return tokens


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
    descriptor = emit_descriptor_json(input_data)
    descriptor_path = root / _DESCRIPTOR_DIR / f"{geometry}.json"
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
    for path in (descriptor_path, reference_path):
        if path.exists() and not reconcile:
            raise ValueError(f"Refusing to overwrite existing generated file: {path}")

    kinds = tuple(sorted(report.kind_counts))
    palette_entry = _palette_entry(geometry, kinds, metadata.palette_tokens)
    manifest_path = root / _MANIFEST_PATH
    palette_path = root / _PALETTE_PATH
    preview_path = root / _PREVIEW_PATH
    manifest_source = update_manifest_source(
        manifest_path.read_text(encoding="utf-8"),
        geometry=geometry,
        label=input_data.label,
        metadata=metadata,
        reconcile=reconcile,
    )
    palette_source = update_palette_source(
        palette_path.read_text(encoding="utf-8"),
        palette_entry,
        reconcile=reconcile,
    )
    preview_descriptor = cast(PreviewDescriptor, descriptor)
    polygon_data = _generate_polygon_data(
        preview_descriptor,
        fill_count=_suggest_fill_count(preview_descriptor),
        geometry=geometry,
        palette_tokens=metadata.palette_tokens,
    )
    preview_source, _ = update_preview_source(
        preview_path.read_text(encoding="utf-8"), geometry, polygon_data
    )
    reference_source = emit_reference_spec(
        input_data,
        report,
        patch_size=patch_size,
        source_url=metadata.source_url,
    )
    writes = [
        PlannedWrite(descriptor_path, json.dumps(descriptor, indent=2) + "\n"),
        PlannedWrite(reference_path, reference_source),
        PlannedWrite(manifest_path, manifest_source),
        PlannedWrite(palette_path, palette_source),
        PlannedWrite(preview_path, preview_source),
    ]
    if sketch_path.resolve() != permanent_sketch_path.resolve():
        if permanent_sketch_path.exists() and not reconcile:
            raise ValueError(f"Permanent sketch path already exists: {permanent_sketch_path}")
        writes.append(PlannedWrite(permanent_sketch_path, sketch_path.read_text(encoding="utf-8")))
    return tuple(writes)


def _run(command: list[str], *, root: Path) -> None:
    result = subprocess.run(command, cwd=root, check=False)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(command)}")


def apply_install_plan(writes: tuple[PlannedWrite, ...], *, root: Path = ROOT_DIR) -> None:
    bootstrap_path = root / _BOOTSTRAP_PATH
    backups: dict[Path, bytes | None] = {
        write.path: write.path.read_bytes() if write.path.exists() else None for write in writes
    }
    backups[bootstrap_path] = bootstrap_path.read_bytes() if bootstrap_path.exists() else None
    try:
        for write in writes:
            write.path.parent.mkdir(parents=True, exist_ok=True)
            write.path.write_text(write.content, encoding="utf-8")
        python_paths = [str(write.path) for write in writes if write.path.suffix == ".py"]
        if python_paths:
            _run([sys.executable, "-m", "ruff", "format", *python_paths], root=root)
            _run([sys.executable, "-m", "ruff", "check", *python_paths], root=root)
        if any(write.path == root / _PREVIEW_PATH for write in writes):
            _run(
                ["npm", "exec", "prettier", "--", "--write", str(_PREVIEW_PATH)],
                root=root,
            )
        _run(
            [
                sys.executable,
                "-m",
                "tools",
                "bootstrap",
                "export",
                str(_BOOTSTRAP_PATH),
            ],
            root=root,
        )
        _run([sys.executable, "-m", "tools", "tilings", "validate"], root=root)
        _run([sys.executable, "-m", "tools", "tilings", "verify"], root=root)
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
    expected_descriptor = emit_descriptor_json(input_data)
    if not descriptor_path.exists():
        problems.append("descriptor is missing")
    elif json.loads(descriptor_path.read_text(encoding="utf-8")) != expected_descriptor:
        problems.append("descriptor is stale")
    reference_directory = root / _REFERENCE_DIR
    reference_exists = any(
        f'"{geometry}"' in path.read_text(encoding="utf-8")
        for path in reference_directory.glob("*.py")
    )
    if not reference_exists:
        problems.append("reference spec is missing")
    manifest_source = (root / _MANIFEST_PATH).read_text(encoding="utf-8")
    if geometry not in manifest_source:
        problems.append("topology manifest entry is missing")
    palette = json.loads((root / _PALETTE_PATH).read_text(encoding="utf-8"))
    palette_family = next(
        (family for family in palette.get("families", []) if family.get("geometry") == geometry),
        None,
    )
    if palette_family is None:
        problems.append("palette entry is missing")
    palette_tokens = {
        variant["selector"]["kind"]: variant["color"]["token"]
        for variant in (palette_family or {}).get("variants", [])
        if "kind" in variant.get("selector", {})
        and isinstance(variant.get("color"), dict)
        and "token" in variant["color"]
    }
    descriptor = cast(PreviewDescriptor, expected_descriptor)
    polygon_data = _generate_polygon_data(
        descriptor,
        fill_count=_suggest_fill_count(descriptor),
        geometry=geometry,
        palette_tokens=palette_tokens,
    )
    _, changed = update_preview_source(
        (root / _PREVIEW_PATH).read_text(encoding="utf-8"), geometry, polygon_data
    )
    if changed:
        problems.append("preview entry is missing or stale")
    return tuple(problems)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install a validated periodic sketch across catalog and generated surfaces.",
    )
    parser.add_argument("sketch", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument(
        "--reconcile",
        action="store_true",
        help="Upsert existing generated files and shared catalog metadata.",
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
            [sys.executable, "-m", "tools.generated_check", "--only", "bootstrap"],
            cwd=ROOT_DIR,
            check=False,
            capture_output=True,
            text=True,
        )
        if freshness.returncode:
            problems.append("standalone bootstrap fixture is stale")
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
        palette_tokens = _parse_palette(args.palette, kinds)
        metadata = InstallMetadata(
            source_url=args.source_url,
            picker_order=args.picker_order,
            default_cell_size=args.default_cell_size,
            min_cell_size=args.min_cell_size,
            max_cell_size=args.max_cell_size,
            default_rule=args.default_rule,
            palette_tokens=palette_tokens,
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
            print(f"  {_BOOTSTRAP_PATH}")
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
