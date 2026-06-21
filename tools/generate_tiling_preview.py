"""Generate POLYGON_PREVIEW_DATA entries for tiling-preview-data.ts.

Periodic-face mode (default): reads face template vertices from the
periodic-face descriptor directory, scales them to fit the 120x72 SVG viewbox,
and prints a ready-to-paste polygon data string. The viewbox is centered
on the highest-degree vertex; a 3x3 grid of unit cells is tiled and
clipped to the viewbox.

Aperiodic mode (``--aperiodic``): builds the actual depth-N patch via
``build_registered_aperiodic_patch``, scales it to the 120x72 viewbox,
and emits color-coded polygon data using the family's ``selectorFields``
from ``frontend/canvas/family-dead-palette-manifest.json`` to assign
color indices (e.g. by ``chirality_token`` for pinwheel, by ``kind`` for
pinwheel-2-1). Replaces hand-coded entries with deterministic geometry.

Usage:
    py -3 tools/generate_tiling_preview.py --geometry kisrhombille
    py -3 tools/generate_tiling_preview.py --geometry kisrhombille --fill-count 1
    py -3 tools/generate_tiling_preview.py --list
    py -3 tools/generate_tiling_preview.py --geometry kisrhombille --write
    py -3 tools/generate_tiling_preview.py --aperiodic --geometry pinwheel --depth 1
    py -3 tools/generate_tiling_preview.py --aperiodic --list
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping, Sequence
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict, cast

if TYPE_CHECKING:
    from backend.simulation.topology import LatticeCell

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.periodic_face_pattern_data import (  # noqa: E402
    load_periodic_face_pattern_payloads,
)

_PALETTE_MANIFEST_PATH = ROOT / "frontend" / "canvas" / "family-dead-palette-manifest.json"
_PREVIEW_DATA_PATH = ROOT / "frontend" / "controls" / "tiling-preview-data.ts"
_VIEWBOX_W = 120
_VIEWBOX_H = 72
_VIEWBOX_MARGIN = 4

# The three regular tilings render via dedicated code in tiling-preview.ts
# and never need a POLYGON_PREVIEW_DATA entry.
_INLINE_RENDER_KEYS = frozenset({"square", "hex", "triangle"})

# Per-family depth suggestions for aperiodic thumbnails: pick the lowest
# depth that produces a visually-informative patch (typically 10-50 cells).
# Used when ``--depth`` is not passed explicitly.
_APERIODIC_DEFAULT_DEPTHS: dict[str, int] = {
    "pinwheel": 1,
    "pinwheel-2-1": 1,
    "sphinx": 2,
    "chair": 2,
    "robinson-triangles": 1,
    "tuebingen-triangle": 1,
    "hat-monotile": 1,
    "shield": 1,
    "spectre": 1,
    "taylor-socolar": 1,
    "ammann-beenker": 1,
    "dodecagonal-square-triangle": 1,
    "penrose-p3-rhombs": 1,
    "penrose-p2-kite-dart": 1,
    "penrose-p1-pentagon-diamond": 0,
    "penrose-p1-pentagon-boat-star": 0,
}


class PreviewVertex(TypedDict):
    x: float
    y: float


class PreviewFace(TypedDict):
    kind: str
    vertices: list[PreviewVertex]


class PreviewDescriptor(TypedDict, total=False):
    label: str
    cell_count_per_unit: int
    row_offset_x: float
    faces: list[PreviewFace]
    unit_width: float
    unit_height: float


class PaletteVariant(TypedDict):
    selector: dict[str, str]
    color: str | dict[str, str]


def preview_entry_source(geometry: str, polygon_data: str) -> str:
    quoted = f'"{geometry}"' if "-" in geometry else geometry
    return f'    {quoted}:\n        "{polygon_data}",'


def update_preview_source(source: str, geometry: str, polygon_data: str) -> tuple[str, bool]:
    entry = preview_entry_source(geometry, polygon_data)
    key = re.escape(geometry)
    pattern = re.compile(
        rf'^    (?:(?:"{key}")|(?:{key})):\s*(?:\n\s*)?"[^"]*",',
        re.MULTILINE,
    )
    match = pattern.search(source)
    if match:
        updated = source[: match.start()] + entry + source[match.end() :]
        return updated, updated != source
    marker = "\n};"
    if marker not in source:
        raise ValueError("Could not find POLYGON_PREVIEW_DATA closing marker.")
    return source.replace(marker, f"\n{entry}{marker}", 1), True


def write_preview_entry(
    geometry: str,
    polygon_data: str,
    *,
    output_path: Path = _PREVIEW_DATA_PATH,
    check: bool = False,
) -> bool:
    source = output_path.read_text(encoding="utf-8")
    updated, changed = update_preview_source(source, geometry, polygon_data)
    if check:
        return not changed
    if changed:
        output_path.write_text(updated, encoding="utf-8")
    return True


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def _tiled_vertices(
    faces: list[PreviewFace],
    *,
    unit_width: float,
    unit_height: float,
    row_offset_x: float,
) -> list[tuple[float, float]]:
    vertices: list[tuple[float, float]] = []
    for ix in range(-1, 3):
        for iy in range(-1, 2):
            dx = (ix * unit_width) + (row_offset_x if iy % 2 != 0 else 0.0)
            dy = iy * unit_height
            for face in faces:
                for vertex in face["vertices"]:
                    vertices.append((vertex["x"] + dx, vertex["y"] + dy))
    return vertices


def _vertex_degree_map(
    faces: list[PreviewFace],
    *,
    unit_width: float,
    unit_height: float,
    row_offset_x: float,
) -> dict[tuple[float, float], int]:
    """Count how many tiled faces share each vertex."""
    counts: dict[tuple[float, float], int] = {}
    for ix in range(-1, 3):
        for iy in range(-1, 2):
            dx = (ix * unit_width) + (row_offset_x if iy % 2 != 0 else 0.0)
            dy = iy * unit_height
            for face in faces:
                for vertex in face["vertices"]:
                    key = (vertex["x"] + dx, vertex["y"] + dy)
                    counts[key] = counts.get(key, 0) + 1
    return counts


def _best_center(
    faces: list[PreviewFace],
    *,
    unit_width: float,
    unit_height: float,
    row_offset_x: float,
) -> tuple[float, float]:
    """Return the vertex with the highest template share count.

    Ties are broken by choosing the vertex closest to the bounding-box
    centre of all template vertices, favouring interior points over edges.
    """
    degree = _vertex_degree_map(
        faces,
        unit_width=unit_width,
        unit_height=unit_height,
        row_offset_x=row_offset_x,
    )
    max_degree = max(degree.values())
    candidates = [v for v, d in degree.items() if d == max_degree]
    if len(candidates) == 1:
        return candidates[0]
    # Tie-break: pick the candidate nearest the centroid of the tiled sample.
    tiled_vertices = _tiled_vertices(
        faces,
        unit_width=unit_width,
        unit_height=unit_height,
        row_offset_x=row_offset_x,
    )
    all_x = [vertex[0] for vertex in tiled_vertices]
    all_y = [vertex[1] for vertex in tiled_vertices]
    cx = sum(all_x) / len(all_x)
    cy = sum(all_y) / len(all_y)
    return min(candidates, key=lambda v: (v[0] - cx) ** 2 + (v[1] - cy) ** 2)


@cache
def _palette_variants_for_geometry(geometry: str) -> tuple[PaletteVariant, ...]:
    manifest = json.loads(_PALETTE_MANIFEST_PATH.read_text(encoding="utf-8"))
    for entry in manifest["families"]:
        if entry["geometry"] == geometry:
            return tuple(entry.get("variants", ()))
    return ()


def _source_value(source: Mapping[str, Any] | object, field: str) -> str | None:
    if isinstance(source, Mapping):
        value = source.get(field)
    else:
        value = getattr(source, field, None)
    return None if value is None else str(value)


def _variant_matches_source(
    source: Mapping[str, Any] | object,
    variant: PaletteVariant,
) -> bool:
    return all(
        _source_value(source, field) == str(expected)
        for field, expected in variant["selector"].items()
    )


def _color_token(color: str | dict[str, str]) -> str:
    if isinstance(color, str):
        return color
    return color.get("token", "")


def _palette_fill_for_source(
    geometry: str | None,
    source: Mapping[str, Any] | object,
    fallback: str,
    palette_variants: Sequence[PaletteVariant] | None = None,
) -> str:
    if not geometry:
        return fallback
    variants = (
        _palette_variants_for_geometry(geometry) if palette_variants is None else palette_variants
    )
    for variant in variants:
        if _variant_matches_source(source, variant):
            token = _color_token(variant["color"])
            if token:
                return token
    return fallback


def _generate_polygon_data(
    descriptor: PreviewDescriptor,
    *,
    fill_count: int = 1,
    geometry: str | None = None,
    palette_tokens: Mapping[str, str] | None = None,
    palette_variants: Sequence[PaletteVariant] | None = None,
) -> str:
    """Return the polygon data string for a tiling descriptor.

    Args:
        descriptor: One periodic-face geometry descriptor.
        fill_count: Number of distinct fill indices to cycle through.
            Use 1 for uniform Laves tilings; use the number of distinct
            cell kinds for Archimedean tilings.
    """
    faces = descriptor["faces"]
    unit_w: float = descriptor["unit_width"]
    unit_h: float = descriptor["unit_height"]
    row_offset_x: float = descriptor.get("row_offset_x", 0.0)

    # Scale: fit the unit cell height exactly into the viewbox.
    scale = _VIEWBOX_H / unit_h

    # Center the viewbox on the most connected interior vertex in a tiled sample.
    cx_orig, cy_orig = _best_center(
        faces,
        unit_width=unit_w,
        unit_height=unit_h,
        row_offset_x=row_offset_x,
    )
    offset_x = _VIEWBOX_W / 2 - cx_orig * scale
    offset_y = _VIEWBOX_H / 2 - cy_orig * scale

    def tx(x: float, y: float) -> tuple[int, int]:
        return round(x * scale + offset_x), round(y * scale + offset_y)

    # Tile a 3x3 grid of unit cells; keep only polygons that visibly overlap
    # the viewbox [0, _VIEWBOX_W] x [0, _VIEWBOX_H] (strict intersection).
    polygons: list[tuple[str, list[tuple[int, int]]]] = []
    for ix in range(-1, 3):
        for iy in range(-1, 2):
            dx = (ix * unit_w) + (row_offset_x if iy % 2 != 0 else 0.0)
            dy = iy * unit_h
            for slot_index, face in enumerate(faces):
                vpts = [tx(v["x"] + dx, v["y"] + dy) for v in face["vertices"]]
                xs = [p[0] for p in vpts]
                ys = [p[1] for p in vpts]
                if max(xs) > 0 and min(xs) < _VIEWBOX_W and max(ys) > 0 and min(ys) < _VIEWBOX_H:
                    fill_index = str(slot_index % fill_count)
                    kind = str(face.get("kind", ""))
                    if palette_tokens and kind in palette_tokens:
                        fill_index = palette_tokens[kind]
                    else:
                        fill_index = _palette_fill_for_source(
                            geometry,
                            face,
                            fill_index,
                            palette_variants,
                        )
                    polygons.append((fill_index, vpts))

    parts = []
    for fill_index, pts in polygons:
        coords = " ".join(f"{x},{y}" for x, y in pts)
        parts.append(f"{fill_index}:{coords}")

    return ";".join(parts)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _load_descriptors() -> dict[str, PreviewDescriptor]:
    return cast(dict[str, PreviewDescriptor], load_periodic_face_pattern_payloads())


def _list_geometries(descriptors: dict[str, PreviewDescriptor]) -> None:
    print("Available periodic-face geometries:")
    for key in sorted(descriptors):
        print(f"  {key}")


def _suggest_fill_count(descriptor: PreviewDescriptor) -> int:
    """Guess the right fill_count from the face kinds in the descriptor.

    For tilings with a single face kind, 1 fill is appropriate. For tilings
    with multiple face kinds, the number of distinct kinds is returned.
    """
    kinds = {f["kind"] for f in descriptor["faces"]}
    return len(kinds)


# ---------------------------------------------------------------------------
# Aperiodic mode
# ---------------------------------------------------------------------------


def _load_palette_selector_fields(geometry: str) -> tuple[str, ...]:
    """Return the palette manifest's ``selectorFields`` for an aperiodic family.

    Empty tuple means the family is rendered uniformly in the picker.
    """
    manifest = json.loads(_PALETTE_MANIFEST_PATH.read_text(encoding="utf-8"))
    for entry in manifest["families"]:
        if entry["geometry"] != geometry:
            continue
        browser_coverage = entry.get("browserAliasCoverage", {})
        return tuple(browser_coverage.get("selectorFields", ()))
    return ()


def _color_index_for_cell(
    cell: LatticeCell,
    selector_fields: tuple[str, ...],
    value_to_index: dict[tuple[str, ...], int],
) -> int:
    """Assign a stable color index to a cell based on its selector-field values."""
    if not selector_fields:
        return 0
    key = tuple(str(getattr(cell, field, "") or "") for field in selector_fields)
    if key not in value_to_index:
        value_to_index[key] = len(value_to_index)
    return value_to_index[key]


def _aperiodic_polygon_data(geometry: str, depth: int) -> tuple[str, int, int]:
    """Build polygon data + cell count + assigned color count for an aperiodic family.

    Uses ``build_topology`` (which dispatches to both the aperiodic registry
    and the Penrose multigrid path) so every aperiodic geometry is covered.
    """
    from backend.simulation.topology import build_topology

    patch = build_topology(geometry, 0, 0, depth)
    selector_fields = _load_palette_selector_fields(geometry)

    # Aperiodic cells always carry vertex polygons; narrow the optional type
    # so mypy stops complaining about ``None`` iteration on the bbox walk.
    cells = [cell for cell in patch.cells if cell.vertices]
    if not cells:
        raise ValueError(f"Patch for {geometry!r} at depth {depth} has no polygon cells.")
    all_x = [v[0] for c in cells for v in c.vertices or ()]
    all_y = [v[1] for c in cells for v in c.vertices or ()]
    if not all_x:
        raise ValueError(f"Patch for {geometry!r} at depth {depth} has no cells.")
    bbox_w = max(all_x) - min(all_x)
    bbox_h = max(all_y) - min(all_y)

    # Fit the patch into the viewbox with a small margin; preserve aspect.
    available_w = _VIEWBOX_W - 2 * _VIEWBOX_MARGIN
    available_h = _VIEWBOX_H - 2 * _VIEWBOX_MARGIN
    if bbox_w <= 0 or bbox_h <= 0:
        scale = 1.0
    else:
        scale = min(available_w / bbox_w, available_h / bbox_h)
    rendered_w = bbox_w * scale
    rendered_h = bbox_h * scale
    origin_x = (_VIEWBOX_W - rendered_w) / 2 - min(all_x) * scale
    origin_y = (_VIEWBOX_H - rendered_h) / 2 - min(all_y) * scale

    def tx(x: float, y: float) -> tuple[int, int]:
        return round(x * scale + origin_x), round(y * scale + origin_y)

    # Stable selector -> color index mapping in cell traversal order.
    value_to_index: dict[tuple[str, ...], int] = {}
    parts: list[str] = []
    fills: set[str] = set()
    for cell in cells:
        fallback_index = str(_color_index_for_cell(cell, selector_fields, value_to_index))
        fill = _palette_fill_for_source(geometry, cell, fallback_index)
        fills.add(fill)
        coords = " ".join(f"{x},{y}" for x, y in (tx(v[0], v[1]) for v in cell.vertices or ()))
        parts.append(f"{fill}:{coords}")

    return ";".join(parts), len(cells), max(1, len(fills))


def _list_aperiodic_geometries() -> None:
    print("Available aperiodic geometries (default depth shown in parens):")
    for geometry in sorted(_APERIODIC_DEFAULT_DEPTHS):
        print(f"  {geometry} ({_APERIODIC_DEFAULT_DEPTHS[geometry]})")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--geometry",
        metavar="KEY",
        help="Geometry key to generate preview data for (e.g. kisrhombille)",
    )
    parser.add_argument(
        "--fill-count",
        type=int,
        default=None,
        metavar="N",
        help=(
            "Number of distinct fill indices to cycle through (default: auto-detected "
            "from face kinds — 1 for uniform Laves tilings, N for N distinct cell kinds). "
            "Periodic mode only."
        ),
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available geometry keys and exit",
    )
    parser.add_argument(
        "--aperiodic",
        action="store_true",
        help=(
            "Build the polygon data from a real depth-N aperiodic patch instead of "
            "reading from the periodic-face descriptor directory."
        ),
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=None,
        metavar="N",
        help=(
            "Aperiodic patch depth (default: per-family value in "
            "_APERIODIC_DEFAULT_DEPTHS). Aperiodic mode only."
        ),
    )
    output_mode = parser.add_mutually_exclusive_group()
    output_mode.add_argument(
        "--write",
        action="store_true",
        help="Write or replace the generated entry in tiling-preview-data.ts.",
    )
    output_mode.add_argument(
        "--check",
        action="store_true",
        help="Exit nonzero when tiling-preview-data.ts does not contain the generated entry.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()

    args = parser.parse_args(argv)

    if args.aperiodic:
        if args.list:
            _list_aperiodic_geometries()
            return 0
        if not args.geometry:
            parser.error("--geometry is required with --aperiodic (or use --list).")
        depth = (
            args.depth
            if args.depth is not None
            else _APERIODIC_DEFAULT_DEPTHS.get(args.geometry, 1)
        )
        polygon_data, cell_count, color_count = _aperiodic_polygon_data(args.geometry, depth)
        print(f"// {args.geometry} depth {depth} -- {cell_count} cells, {color_count} color(s)")
        if args.write or args.check:
            current = write_preview_entry(args.geometry, polygon_data, check=args.check)
            if not current:
                print(f"Preview entry for '{args.geometry}' is stale.", file=sys.stderr)
                return 1
            print(
                f"Preview entry for '{args.geometry}' "
                f"{'is current' if args.check else 'was written'}: {_PREVIEW_DATA_PATH}"
            )
            return 0
        print(preview_entry_source(args.geometry, polygon_data))
        return 0

    descriptors = _load_descriptors()

    if args.list:
        _list_geometries(descriptors)
        return 0

    if not args.geometry:
        parser.error("--geometry is required (or use --list to see available keys)")

    key = args.geometry
    if key in _INLINE_RENDER_KEYS:
        print(
            f"'{key}' uses dedicated inline rendering in tiling-preview.ts "
            f"and does not need a POLYGON_PREVIEW_DATA entry.",
            file=sys.stderr,
        )
        return 1

    if key not in descriptors:
        available = ", ".join(sorted(descriptors))
        print(
            f"Geometry '{key}' has no periodic-face descriptor.\nAvailable: {available}",
            file=sys.stderr,
        )
        return 1

    descriptor = descriptors[key]
    fill_count = args.fill_count if args.fill_count is not None else _suggest_fill_count(descriptor)
    suggested = _suggest_fill_count(descriptor)
    if fill_count != suggested:
        print(
            f"Note: auto-detected fill_count would be {suggested} "
            f"(based on {suggested} face kind(s)); using {fill_count}.",
            file=sys.stderr,
        )

    polygon_data = _generate_polygon_data(descriptor, fill_count=fill_count, geometry=key)
    label = descriptor.get("label", key)
    faces_per_unit = descriptor.get("cell_count_per_unit", "?")

    print(f"// {label} — {faces_per_unit} faces per unit cell")
    if args.write or args.check:
        current = write_preview_entry(key, polygon_data, check=args.check)
        if not current:
            print(f"Preview entry for '{key}' is stale.", file=sys.stderr)
            return 1
        print(
            f"Preview entry for '{key}' "
            f"{'is current' if args.check else 'was written'}: {_PREVIEW_DATA_PATH}"
        )
        return 0
    print(preview_entry_source(key, polygon_data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
