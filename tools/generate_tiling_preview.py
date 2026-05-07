"""Generate POLYGON_PREVIEW_DATA entries for tiling-preview-data.ts.

For each periodic face tiling, reads the face template vertices from
periodic_face_patterns.json, scales them to fit the 120x72 SVG viewbox used
by the tiling picker, and prints a ready-to-paste polygon data string.

The viewbox is centered on the highest-degree vertex — typically the most
visually striking point (e.g. the 12-fold rosette center in kisrhombille, the
hexagonal star in floret-pentagonal). A 3x3 grid of unit cells is tiled and
clipped to the viewbox so edges are filled without blank margins.

Usage:
    py -3 tools/generate_tiling_preview.py --geometry kisrhombille
    py -3 tools/generate_tiling_preview.py --geometry kisrhombille --fill-count 1
    py -3 tools/generate_tiling_preview.py --list
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_DATA_PATH = ROOT / "backend" / "simulation" / "data" / "periodic_face_patterns.json"
_VIEWBOX_W = 120
_VIEWBOX_H = 72

# The three regular tilings render via dedicated code in tiling-preview.ts
# and never need a POLYGON_PREVIEW_DATA entry.
_INLINE_RENDER_KEYS = frozenset({"square", "hex", "triangle"})


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


def _generate_polygon_data(
    descriptor: PreviewDescriptor,
    *,
    fill_count: int = 1,
) -> str:
    """Return the polygon data string for a tiling descriptor.

    Args:
        descriptor: One entry from periodic_face_patterns.json.
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
    polygons: list[tuple[int, list[tuple[int, int]]]] = []
    for ix in range(-1, 3):
        for iy in range(-1, 2):
            dx = (ix * unit_w) + (row_offset_x if iy % 2 != 0 else 0.0)
            dy = iy * unit_h
            for slot_index, face in enumerate(faces):
                vpts = [tx(v["x"] + dx, v["y"] + dy) for v in face["vertices"]]
                xs = [p[0] for p in vpts]
                ys = [p[1] for p in vpts]
                if max(xs) > 0 and min(xs) < _VIEWBOX_W and max(ys) > 0 and min(ys) < _VIEWBOX_H:
                    fill_index = slot_index % fill_count
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
    return json.loads(_DATA_PATH.read_text(encoding="utf-8"))


def _list_geometries(descriptors: dict[str, PreviewDescriptor]) -> None:
    print("Available geometries in periodic_face_patterns.json:")
    for key in sorted(descriptors):
        print(f"  {key}")


def _suggest_fill_count(descriptor: PreviewDescriptor) -> int:
    """Guess the right fill_count from the face kinds in the descriptor.

    For tilings with a single face kind, 1 fill is appropriate. For tilings
    with multiple face kinds, the number of distinct kinds is returned.
    """
    kinds = {f["kind"] for f in descriptor["faces"]}
    return len(kinds)


def main(argv: list[str] | None = None) -> int:
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
            "from face kinds — 1 for uniform Laves tilings, N for N distinct cell kinds)"
        ),
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available geometry keys and exit",
    )

    args = parser.parse_args(argv)
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
            f"Geometry '{key}' not found in periodic_face_patterns.json.\nAvailable: {available}",
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

    polygon_data = _generate_polygon_data(descriptor, fill_count=fill_count)
    label = descriptor.get("label", key)
    faces_per_unit = descriptor.get("cell_count_per_unit", "?")

    print(f"// {label} — {faces_per_unit} faces per unit cell")
    print(f"    {key}:")
    print(f'        "{polygon_data}",')
    return 0


if __name__ == "__main__":
    sys.exit(main())
