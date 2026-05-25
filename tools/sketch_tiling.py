"""Standalone tiling sketch / validation tool.

Lets you iterate on a candidate periodic tiling *without* wiring it into the
backend manifests. Takes a Python sketch file describing the faces of a unit
cell, builds a 3x3 patch using the same builder the backend uses, then
reports overlaps, T-junctions, vertex configurations with angle sums, and
emits an SVG visualization and a JSON descriptor stub ready to paste into
``backend/simulation/data/periodic_face_patterns.json``.

Sketch file format (a regular Python module)::

    import math
    EDGE = 52.0
    H = round(EDGE * math.sqrt(3) / 2, 6)

    GEOMETRY = "my-tiling"             # optional; used in JSON stub
    LABEL = "My Tiling"                # optional
    BASE_EDGE = EDGE                   # optional
    CELL_WIDTH = 2 * EDGE
    CELL_HEIGHT = 2 * H + EDGE
    ROW_OFFSET_X = 0.0                 # optional, default 0

    FACES = [
        {
            "slot": "ua",
            "kind": "triangle",
            "vertices": [(0, 0), (EDGE, 0), (EDGE / 2, H)],
            # optional:
            # "prefix": "t",
            # "center": (26, 15.011),     # default = centroid
            # "repeat_x_extra": 0,
            # "repeat_y_extra": 0,
        },
        ...
    ]

Usage::

    py tools/sketch_tiling.py path/to/sketch.py
    py tools/sketch_tiling.py path/to/sketch.py --svg out.svg --json out.json
    py tools/sketch_tiling.py path/to/sketch.py --patch-size 4

Exit code is 0 if the sketch produces a valid tiling (no overlaps, all
interior edges matched, every vertex's interior-angle sum is 360 degrees);
non-zero otherwise.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.simulation.periodic_face_tilings import (  # noqa: E402
    FaceTemplate,
    PeriodicFaceCell,
    _pattern_cells,
)

_COORD_PRECISION = 4  # decimals; matches backend's edge-key precision
_OVERLAP_AREA_TOLERANCE = 1e-3
_COLLINEAR_TOLERANCE = 1e-4
_ANGLE_TOLERANCE_DEGREES = 0.5


@dataclass(frozen=True)
class SketchInput:
    faces: tuple[dict[str, Any], ...]
    cell_width: float
    cell_height: float
    row_offset_x: float = 0.0
    base_edge: float | None = None
    geometry: str = "sketch-tiling"
    label: str = "Sketch Tiling"


@dataclass(frozen=True)
class OverlapPair:
    left_id: str
    right_id: str
    area: float


@dataclass(frozen=True)
class UnmatchedEdge:
    endpoints: tuple[tuple[float, float], tuple[float, float]]
    cells: tuple[str, ...]


@dataclass(frozen=True)
class TJunction:
    vertex: tuple[float, float]
    edge_endpoints: tuple[tuple[float, float], tuple[float, float]]
    edge_cell_id: str
    vertex_cells: tuple[str, ...]


@dataclass(frozen=True)
class VertexConfiguration:
    position: tuple[float, float]
    polygons: tuple[tuple[str, str], ...]  # (cell_id, kind)
    angle_sum_degrees: float


@dataclass(frozen=True)
class SketchReport:
    cells: tuple[PeriodicFaceCell, ...]
    kind_counts: dict[str, int]
    degree_histogram: dict[int, int]
    overlaps: tuple[OverlapPair, ...]
    unmatched_edges: tuple[UnmatchedEdge, ...]
    t_junctions: tuple[TJunction, ...]
    vertex_configurations: tuple[VertexConfiguration, ...]
    interior_vertex_kinds: dict[tuple[str, ...], int]

    @property
    def is_valid(self) -> bool:
        # An interior vertex has 4+ polygons meeting at it (a boundary
        # corner has 1-2; a boundary edge has 2-3). Require every such
        # interior vertex to have an angle sum within tolerance of 360 deg.
        return (
            not self.overlaps
            and not self.t_junctions
            and not self.unmatched_edges
            and all(
                abs(v.angle_sum_degrees - 360.0) <= _ANGLE_TOLERANCE_DEGREES
                for v in self.vertex_configurations
                if len({cell_id for cell_id, _ in v.polygons}) >= 4
            )
        )


# --- Sketch loading ---------------------------------------------------------


def load_sketch(path: Path) -> SketchInput:
    """Load a sketch module from a Python file."""
    spec = importlib.util.spec_from_file_location("sketch_module", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import sketch module from {path}.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    try:
        faces = tuple(module.FACES)
        cell_width = float(module.CELL_WIDTH)
        cell_height = float(module.CELL_HEIGHT)
    except AttributeError as error:
        raise RuntimeError(
            f"Sketch {path} must define FACES (list), CELL_WIDTH, CELL_HEIGHT."
        ) from error

    return SketchInput(
        faces=faces,
        cell_width=cell_width,
        cell_height=cell_height,
        row_offset_x=float(getattr(module, "ROW_OFFSET_X", 0.0)),
        base_edge=getattr(module, "BASE_EDGE", None),
        geometry=str(getattr(module, "GEOMETRY", "sketch-tiling")),
        label=str(getattr(module, "LABEL", "Sketch Tiling")),
    )


def _to_face_templates(sketch: SketchInput) -> tuple[FaceTemplate, ...]:
    templates: list[FaceTemplate] = []
    for index, face in enumerate(sketch.faces):
        if "vertices" not in face or "slot" not in face or "kind" not in face:
            raise ValueError(f"Face #{index} missing required key (slot, kind, vertices): {face!r}")
        vertices = tuple((float(v[0]), float(v[1])) for v in face["vertices"])
        center_raw = face.get("center")
        if center_raw is None:
            cx = sum(v[0] for v in vertices) / len(vertices)
            cy = sum(v[1] for v in vertices) / len(vertices)
            center: tuple[float, float] = (cx, cy)
        else:
            center = (float(center_raw[0]), float(center_raw[1]))
        templates.append(
            FaceTemplate(
                slot=str(face["slot"]),
                kind=str(face["kind"]),
                prefix=str(face.get("prefix", str(face["kind"])[:1] or "f")),
                center=center,
                vertices=vertices,
                repeat_x_extra=int(face.get("repeat_x_extra", 0)),
                repeat_y_extra=int(face.get("repeat_y_extra", 0)),
            )
        )
    return tuple(templates)


# --- Geometry helpers -------------------------------------------------------


def _round_vertex(point: tuple[float, float]) -> tuple[float, float]:
    return (round(point[0], _COORD_PRECISION), round(point[1], _COORD_PRECISION))


def _edge_key(
    p1: tuple[float, float], p2: tuple[float, float]
) -> tuple[tuple[float, float], tuple[float, float]]:
    a, b = _round_vertex(p1), _round_vertex(p2)
    return (a, b) if a <= b else (b, a)


def _interior_angle_at(cell: PeriodicFaceCell, vertex: tuple[float, float]) -> float:
    """Interior angle (radians) of `cell` at the given vertex, or 0 if absent."""
    rounded = _round_vertex(vertex)
    vertices = cell.vertices
    n = len(vertices)
    for index in range(n):
        if _round_vertex(vertices[index]) == rounded:
            prev_v = vertices[(index - 1) % n]
            next_v = vertices[(index + 1) % n]
            v1 = (prev_v[0] - vertex[0], prev_v[1] - vertex[1])
            v2 = (next_v[0] - vertex[0], next_v[1] - vertex[1])
            dot = v1[0] * v2[0] + v1[1] * v2[1]
            cross = v1[0] * v2[1] - v1[1] * v2[0]
            return math.atan2(abs(cross), dot)
    return 0.0


# --- Analysis passes --------------------------------------------------------


def _check_overlaps(cells: Sequence[PeriodicFaceCell]) -> tuple[OverlapPair, ...]:
    from shapely.geometry import Polygon  # local import to keep module light

    polygons = {cell.id: Polygon(cell.vertices) for cell in cells}
    overlaps: list[OverlapPair] = []
    items = list(polygons.items())
    for i, (left_id, left) in enumerate(items):
        if not left.is_valid:
            continue
        for right_id, right in items[i + 1 :]:
            if not right.is_valid:
                continue
            if not left.intersects(right):
                continue
            intersection = left.intersection(right)
            if intersection.is_empty or intersection.area <= _OVERLAP_AREA_TOLERANCE:
                continue
            overlaps.append(OverlapPair(left_id, right_id, intersection.area))
    overlaps.sort(key=lambda o: -o.area)
    return tuple(overlaps)


def _build_edge_map(
    cells: Sequence[PeriodicFaceCell],
) -> dict[tuple[tuple[float, float], tuple[float, float]], list[str]]:
    edge_map: dict[tuple[tuple[float, float], tuple[float, float]], list[str]] = defaultdict(list)
    for cell in cells:
        vertices = cell.vertices
        for index in range(len(vertices)):
            edge_map[_edge_key(vertices[index], vertices[(index + 1) % len(vertices)])].append(
                cell.id
            )
    return edge_map


def _check_t_junctions(
    cells: Sequence[PeriodicFaceCell],
    patch_bounds: tuple[float, float, float, float],
) -> tuple[TJunction, ...]:
    """A T-junction = some vertex sits on the interior of another face's edge."""
    rounded_vertex_to_cells: dict[tuple[float, float], set[str]] = defaultdict(set)
    for cell in cells:
        for v in cell.vertices:
            rounded_vertex_to_cells[_round_vertex(v)].add(cell.id)

    min_x, min_y, max_x, max_y = patch_bounds

    def is_interior(point: tuple[float, float]) -> bool:
        margin = 1e-3
        return (
            min_x + margin < point[0] < max_x - margin
            and min_y + margin < point[1] < max_y - margin
        )

    t_junctions: list[TJunction] = []
    for cell in cells:
        vertices = cell.vertices
        n = len(vertices)
        for index in range(n):
            a = vertices[index]
            b = vertices[(index + 1) % n]
            ab = (b[0] - a[0], b[1] - a[1])
            ab_len_sq = ab[0] ** 2 + ab[1] ** 2
            if ab_len_sq < 1e-9:
                continue
            edge_endpoints_rounded = {_round_vertex(a), _round_vertex(b)}
            for vertex, cells_here in rounded_vertex_to_cells.items():
                if vertex in edge_endpoints_rounded:
                    continue
                if cell.id in cells_here:
                    continue
                if not is_interior(vertex):
                    continue
                av = (vertex[0] - a[0], vertex[1] - a[1])
                cross = av[0] * ab[1] - av[1] * ab[0]
                if abs(cross) > _COLLINEAR_TOLERANCE * math.sqrt(ab_len_sq):
                    continue
                projection = (av[0] * ab[0] + av[1] * ab[1]) / ab_len_sq
                if not (0.001 < projection < 0.999):
                    continue
                t_junctions.append(
                    TJunction(
                        vertex=vertex,
                        edge_endpoints=(_round_vertex(a), _round_vertex(b)),
                        edge_cell_id=cell.id,
                        vertex_cells=tuple(sorted(cells_here)),
                    )
                )
    return tuple(t_junctions)


def _vertex_configurations(
    cells: Sequence[PeriodicFaceCell],
) -> tuple[VertexConfiguration, ...]:
    rounded_vertex_to_cells: dict[tuple[float, float], list[PeriodicFaceCell]] = defaultdict(list)
    for cell in cells:
        seen: set[tuple[float, float]] = set()
        for v in cell.vertices:
            r = _round_vertex(v)
            if r in seen:
                continue  # collinear-vertex polygon meets vertex only once
            seen.add(r)
            rounded_vertex_to_cells[r].append(cell)

    configurations: list[VertexConfiguration] = []
    for vertex, cells_here in sorted(rounded_vertex_to_cells.items()):
        angle_sum_rad = sum(_interior_angle_at(c, vertex) for c in cells_here)
        polygons = tuple((c.id, c.kind) for c in cells_here)
        configurations.append(
            VertexConfiguration(
                position=vertex,
                polygons=polygons,
                angle_sum_degrees=math.degrees(angle_sum_rad),
            )
        )
    return tuple(configurations)


# --- Top-level entry --------------------------------------------------------


def sketch(input_data: SketchInput, *, patch_size: int = 3) -> SketchReport:
    """Build a patch and run all the analysis passes; return a structured report."""
    templates = _to_face_templates(input_data)
    cells = _pattern_cells(
        unit_width=input_data.cell_width,
        unit_height=input_data.cell_height,
        faces=templates,
        row_offset_x=input_data.row_offset_x,
        id_pattern="{prefix}:{slot}:{x}:{y}",
        width=patch_size,
        height=patch_size,
    )

    kind_counts = dict(Counter(c.kind for c in cells))
    degree_hist = dict(sorted(Counter(len(c.neighbors) for c in cells).items()))

    # For boundary classification we use the LOGICAL patch rectangle (the
    # NxN box of unit cells), not the polygon bounding box. Straddler
    # polygons that extend outside the logical patch are normal — the
    # important thing is which edges sit on the logical boundary.
    logical_bounds = (
        0.0,
        0.0,
        input_data.cell_width * patch_size,
        input_data.cell_height * patch_size,
    )

    overlaps = _check_overlaps(cells)

    edge_map = _build_edge_map(cells)
    unmatched_edges = tuple(
        UnmatchedEdge(endpoints=key, cells=tuple(sorted(set(cell_ids))))
        for key, cell_ids in sorted(edge_map.items())
        if (
            (len(set(cell_ids)) == 1 and _is_interior_edge(key, logical_bounds))
            or len(set(cell_ids)) >= 3
        )
    )

    t_junctions = _check_t_junctions(cells, logical_bounds)

    vertex_configs = _vertex_configurations(cells)

    # Interior vertex kind histogram (vertices whose angle sum ~= 360 deg)
    interior_kinds: Counter[tuple[str, ...]] = Counter()
    for cfg in vertex_configs:
        if abs(cfg.angle_sum_degrees - 360.0) <= _ANGLE_TOLERANCE_DEGREES:
            kinds = tuple(sorted(kind for _, kind in cfg.polygons))
            interior_kinds[kinds] += 1

    return SketchReport(
        cells=cells,
        kind_counts=kind_counts,
        degree_histogram=degree_hist,
        overlaps=overlaps,
        unmatched_edges=unmatched_edges,
        t_junctions=t_junctions,
        vertex_configurations=vertex_configs,
        interior_vertex_kinds=dict(interior_kinds),
    )


def _is_interior_edge(
    key: tuple[tuple[float, float], tuple[float, float]],
    patch_bounds: tuple[float, float, float, float],
) -> bool:
    """An edge is interior if neither endpoint sits on the patch bounding box."""
    min_x, min_y, max_x, max_y = patch_bounds
    margin = 1e-3
    for x, y in key:
        on_boundary = (
            abs(x - min_x) < margin
            or abs(x - max_x) < margin
            or abs(y - min_y) < margin
            or abs(y - max_y) < margin
        )
        if on_boundary:
            return False
    return True


# --- Rendering and JSON emission --------------------------------------------


_DEFAULT_PALETTE = (
    "#f8d4a8",
    "#a8d4f8",
    "#d4f8a8",
    "#f8a8d4",
    "#a8f8d4",
    "#d4a8f8",
    "#f8f0a8",
    "#d4d4f8",
)


def render_svg(
    cells: Sequence[PeriodicFaceCell],
    output_path: Path,
    *,
    margin: float = 30.0,
) -> None:
    min_x = min(v[0] for c in cells for v in c.vertices)
    max_x = max(v[0] for c in cells for v in c.vertices)
    min_y = min(v[1] for c in cells for v in c.vertices)
    max_y = max(v[1] for c in cells for v in c.vertices)
    kinds = sorted({c.kind for c in cells})
    color_for_kind = {k: _DEFAULT_PALETTE[i % len(_DEFAULT_PALETTE)] for i, k in enumerate(kinds)}

    width = max_x - min_x + 2 * margin
    height = max_y - min_y + 2 * margin

    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{min_x - margin:.3f} {min_y - margin:.3f} {width:.3f} {height:.3f}">',
        "<style>polygon { stroke: #1f2430; stroke-width: 1; fill-opacity: 0.65; }</style>",
    ]
    for cell in cells:
        pts = " ".join(f"{v[0]:.3f},{v[1]:.3f}" for v in cell.vertices)
        color = color_for_kind[cell.kind]
        lines.append(
            f'<polygon points="{pts}" fill="{color}">'
            f"<title>{cell.id} ({cell.kind})</title>"
            f"</polygon>"
        )
    # Legend
    legend_x = min_x
    legend_y = min_y - margin + 12
    for i, kind in enumerate(kinds):
        block_x = legend_x + i * 110
        lines.append(
            f'<rect x="{block_x:.1f}" y="{legend_y - 12:.1f}" width="18" height="12" '
            f'fill="{color_for_kind[kind]}" stroke="#1f2430"/>'
        )
        lines.append(
            f'<text x="{block_x + 22:.1f}" y="{legend_y - 2:.1f}" '
            f'font-family="sans-serif" font-size="10">{kind}</text>'
        )
    lines.append("</svg>")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def emit_descriptor_json(input_data: SketchInput) -> dict[str, Any]:
    faces_json: list[dict[str, Any]] = []
    all_vertices: list[tuple[float, float]] = []
    for face in input_data.faces:
        vertices = [(float(v[0]), float(v[1])) for v in face["vertices"]]
        all_vertices.extend(vertices)
        center_raw = face.get("center")
        if center_raw is None:
            cx = sum(v[0] for v in vertices) / len(vertices)
            cy = sum(v[1] for v in vertices) / len(vertices)
        else:
            cx, cy = float(center_raw[0]), float(center_raw[1])
        entry: dict[str, Any] = {
            "slot": face["slot"],
            "kind": face["kind"],
            "prefix": face.get("prefix", str(face["kind"])[:1] or "f"),
            "center": {"x": round(cx, 6), "y": round(cy, 6)},
            "vertices": [{"x": round(v[0], 6), "y": round(v[1], 6)} for v in vertices],
        }
        if face.get("repeat_x_extra"):
            entry["repeat_x_extra"] = int(face["repeat_x_extra"])
        if face.get("repeat_y_extra"):
            entry["repeat_y_extra"] = int(face["repeat_y_extra"])
        faces_json.append(entry)

    min_x = min(v[0] for v in all_vertices)
    max_x = max(v[0] for v in all_vertices)
    min_y = min(v[1] for v in all_vertices)
    max_y = max(v[1] for v in all_vertices)

    descriptor = {
        "geometry": input_data.geometry,
        "label": input_data.label,
        "base_edge": input_data.base_edge or input_data.cell_width / 2,
        "unit_width": input_data.cell_width,
        "unit_height": input_data.cell_height,
        "min_dimension": 1,
        "min_x": round(min(min_x, 0.0), 6),
        "min_y": round(min(min_y, 0.0), 6),
        "max_x": round(max(max_x, input_data.cell_width), 6),
        "max_y": round(max(max_y, input_data.cell_height), 6),
        "cell_count_per_unit": len(input_data.faces),
        "faces": faces_json,
    }
    if input_data.row_offset_x:
        descriptor["row_offset_x"] = input_data.row_offset_x
    return {input_data.geometry: descriptor}


# --- CLI --------------------------------------------------------------------


def _print_report(input_data: SketchInput, report: SketchReport) -> None:
    print(f"=== sketch report: {input_data.geometry} ===")
    print(f"cell: {input_data.cell_width} x {input_data.cell_height}")
    print(f"face templates: {len(input_data.faces)}")
    print(f"patch cells: {len(report.cells)}")
    print(f"kind counts: {report.kind_counts}")
    print(f"degree histogram: {report.degree_histogram}")

    print()
    if report.overlaps:
        print(f"OVERLAPS: {len(report.overlaps)}")
        for overlap in report.overlaps[:5]:
            print(f"  {overlap.left_id} / {overlap.right_id}: area = {overlap.area:.6f}")
        if len(report.overlaps) > 5:
            print(f"  ... and {len(report.overlaps) - 5} more")
    else:
        print("overlaps: none")

    if report.t_junctions:
        print(f"T-JUNCTIONS: {len(report.t_junctions)}")
        for tj in report.t_junctions[:5]:
            print(
                f"  vertex {tj.vertex} sits on edge "
                f"{tj.edge_endpoints[0]}-{tj.edge_endpoints[1]} of {tj.edge_cell_id}"
            )
        if len(report.t_junctions) > 5:
            print(f"  ... and {len(report.t_junctions) - 5} more")
    else:
        print("T-junctions: none")

    if report.unmatched_edges:
        print(f"UNMATCHED INTERIOR EDGES: {len(report.unmatched_edges)}")
        for edge in report.unmatched_edges[:5]:
            print(f"  edge {edge.endpoints} on cell(s) {edge.cells}")
    else:
        print("unmatched interior edges: none")

    print()
    print("interior vertex configurations:")
    for kinds, count in sorted(report.interior_vertex_kinds.items(), key=lambda kv: -kv[1]):
        print(f"  {count:4d}x  {kinds}")

    bad_angle_vertices = [
        v
        for v in report.vertex_configurations
        if abs(v.angle_sum_degrees - 360.0) > _ANGLE_TOLERANCE_DEGREES
        and len({cell_id for cell_id, _ in v.polygons}) >= 4
    ]
    if bad_angle_vertices:
        print()
        print(f"VERTICES WITH NON-360 DEG ANGLE SUM (likely interior): {len(bad_angle_vertices)}")
        for v in bad_angle_vertices[:5]:
            print(f"  {v.position}: {v.angle_sum_degrees:.2f} deg ({len(v.polygons)} polygons)")

    print()
    print("RESULT:", "VALID" if report.is_valid else "INVALID")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sketch and validate a candidate tiling without backend wiring.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("sketch", type=Path, help="Path to a sketch .py file")
    parser.add_argument("--svg", type=Path, help="Write an SVG visualization to this path")
    parser.add_argument(
        "--json", type=Path, dest="json_path", help="Write a JSON descriptor stub to this path"
    )
    parser.add_argument(
        "--patch-size",
        type=int,
        default=3,
        help="Build an NxN patch for validation (default: 3)",
    )
    args = parser.parse_args(argv)

    input_data = load_sketch(args.sketch)
    report = sketch(input_data, patch_size=args.patch_size)
    _print_report(input_data, report)

    if args.svg:
        render_svg(report.cells, args.svg)
        print(f"\nSVG written: {args.svg}")
    if args.json_path:
        descriptor = emit_descriptor_json(input_data)
        args.json_path.write_text(json.dumps(descriptor, indent=2) + "\n", encoding="utf-8")
        print(f"JSON descriptor stub written: {args.json_path}")

    return 0 if report.is_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
