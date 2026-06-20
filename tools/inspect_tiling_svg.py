from __future__ import annotations

import argparse
import json
import math
import pprint
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

_NUMBER = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?")
_KIND_BY_SIDES = {
    3: "triangle",
    4: "square",
    5: "pentagon",
    6: "hexagon",
    8: "octagon",
    10: "decagon",
    12: "dodecagon",
}


@dataclass(frozen=True)
class InspectedPolygon:
    kind: str
    regular: bool
    center: tuple[float, float]
    vertices: tuple[tuple[float, float], ...]
    mean_edge: float


@dataclass(frozen=True)
class SvgInspection:
    polygon_count: int
    kind_counts: dict[str, int]
    regular_polygon_count: int
    bounds: tuple[float, float, float, float]
    candidate_translations: tuple[tuple[float, float, int], ...]
    polygons: tuple[InspectedPolygon, ...]


def _points_from_element(element: ET.Element) -> tuple[tuple[float, float], ...] | None:
    tag = element.tag.rsplit("}", 1)[-1]
    raw = element.get("points") if tag in {"polygon", "polyline"} else element.get("d")
    if raw is None:
        return None
    if tag == "path":
        commands = re.findall(r"[A-Za-z]", raw)
        if any(command not in {"M", "L", "Z"} for command in commands):
            return None
    numbers = [float(value) for value in _NUMBER.findall(raw)]
    if len(numbers) < 6 or len(numbers) % 2:
        return None
    points = tuple((numbers[index], numbers[index + 1]) for index in range(0, len(numbers), 2))
    if len(points) > 3 and points[0] == points[-1]:
        points = points[:-1]
    return points


def _edge_lengths(vertices: tuple[tuple[float, float], ...]) -> tuple[float, ...]:
    return tuple(
        math.hypot(
            vertices[(index + 1) % len(vertices)][0] - vertex[0],
            vertices[(index + 1) % len(vertices)][1] - vertex[1],
        )
        for index, vertex in enumerate(vertices)
    )


def _interior_angles(vertices: tuple[tuple[float, float], ...]) -> tuple[float, ...]:
    angles: list[float] = []
    for index, vertex in enumerate(vertices):
        previous = vertices[(index - 1) % len(vertices)]
        following = vertices[(index + 1) % len(vertices)]
        left = (previous[0] - vertex[0], previous[1] - vertex[1])
        right = (following[0] - vertex[0], following[1] - vertex[1])
        denominator = math.hypot(*left) * math.hypot(*right)
        if denominator <= 1e-12:
            return ()
        cosine = max(
            -1.0,
            min(1.0, (left[0] * right[0] + left[1] * right[1]) / denominator),
        )
        angles.append(math.acos(cosine))
    return tuple(angles)


def _inspect_polygon(vertices: tuple[tuple[float, float], ...]) -> InspectedPolygon:
    edges = _edge_lengths(vertices)
    angles = _interior_angles(vertices)
    mean_edge = sum(edges) / len(edges)
    tolerance = max(mean_edge * 0.02, 1e-6)
    sides = len(vertices)
    expected_angle = (sides - 2) * math.pi / sides
    regular = (
        mean_edge > 0
        and max(abs(edge - mean_edge) for edge in edges) <= tolerance
        and bool(angles)
        and max(abs(angle - expected_angle) for angle in angles) <= math.radians(2)
    )
    return InspectedPolygon(
        kind=_KIND_BY_SIDES.get(sides, f"polygon-{sides}") if regular else f"polygon-{sides}",
        regular=regular,
        center=(
            sum(x for x, _ in vertices) / sides,
            sum(y for _, y in vertices) / sides,
        ),
        vertices=vertices,
        mean_edge=mean_edge,
    )


def _candidate_translations(
    polygons: tuple[InspectedPolygon, ...],
) -> tuple[tuple[float, float, int], ...]:
    counts: Counter[tuple[float, float]] = Counter()
    by_kind: dict[str, list[InspectedPolygon]] = {}
    for polygon in polygons:
        by_kind.setdefault(polygon.kind, []).append(polygon)
    for same_kind in by_kind.values():
        for index, left in enumerate(same_kind):
            for right in same_kind[index + 1 :]:
                dx = right.center[0] - left.center[0]
                dy = right.center[1] - left.center[1]
                if dx < 0 or (abs(dx) < 1e-9 and dy < 0):
                    dx, dy = -dx, -dy
                if math.hypot(dx, dy) > 1e-6:
                    counts[(round(dx, 6), round(dy, 6))] += 1
    ranked = sorted(
        ((dx, dy, count) for (dx, dy), count in counts.items() if count >= 2),
        key=lambda item: (-item[2], math.hypot(item[0], item[1]), item[0], item[1]),
    )
    return tuple(ranked[:12])


def _polygon_elements(
    element: ET.Element,
    inherited_fill: str | None = None,
    inherited_fill_visible: bool = True,
) -> list[tuple[tuple[float, float], ...]]:
    style = {
        key.strip(): value.strip()
        for declaration in element.get("style", "").split(";")
        if ":" in declaration
        for key, value in (declaration.split(":", 1),)
    }
    style_fill = style.get("fill")
    fill = element.get("fill", style_fill if style_fill is not None else inherited_fill)
    opacity_raw = element.get("fill-opacity", style.get("fill-opacity"))
    fill_visible = inherited_fill_visible
    if opacity_raw is not None:
        try:
            fill_visible = float(opacity_raw) > 0
        except ValueError:
            fill_visible = opacity_raw not in {"0", "00"}
    found: list[tuple[tuple[float, float], ...]] = []
    points = _points_from_element(element)
    if points is not None and fill != "none" and fill_visible:
        found.append(points)
    for child in element:
        found.extend(_polygon_elements(child, fill, fill_visible))
    return found


def inspect_svg(path: Path) -> SvgInspection:
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    if any(element.get("transform") for element in root.iter()):
        raise ValueError("SVG transforms are not supported; flatten transforms before inspection.")
    polygons = tuple(_inspect_polygon(points) for points in _polygon_elements(root))
    if not polygons:
        raise ValueError(f"No straight-sided polygons found in {path}.")
    vertices = [vertex for polygon in polygons for vertex in polygon.vertices]
    return SvgInspection(
        polygon_count=len(polygons),
        kind_counts=dict(sorted(Counter(polygon.kind for polygon in polygons).items())),
        regular_polygon_count=sum(polygon.regular for polygon in polygons),
        bounds=(
            min(x for x, _ in vertices),
            min(y for _, y in vertices),
            max(x for x, _ in vertices),
            max(y for _, y in vertices),
        ),
        candidate_translations=_candidate_translations(polygons),
        polygons=polygons,
    )


def render_sketch_starter(path: Path, inspection: SvgInspection) -> str:
    min_x, min_y, max_x, max_y = inspection.bounds
    faces = []
    for index, polygon in enumerate(inspection.polygons, start=1):
        vertices = tuple((round(x - min_x, 6), round(y - min_y, 6)) for x, y in polygon.vertices)
        faces.append(
            {
                "slot": f"f{index}",
                "kind": polygon.kind,
                "prefix": "f",
                "vertices": vertices,
            }
        )
    return (
        f'"""Imported sketch starter from {path.name}.\n\n'
        "Reduce this sampled patch to an exact periodic unit cell before installation.\n"
        '"""\n\n'
        "from typing import Any\n\n"
        'GEOMETRY = "replace-me"\n'
        'LABEL = "Replace Me"\n'
        f"CELL_WIDTH = {max_x - min_x:.6f}\n"
        f"CELL_HEIGHT = {max_y - min_y:.6f}\n"
        "ROW_OFFSET_X = 0.0\n\n"
        f"FACES: list[dict[str, Any]] = {pprint.pformat(faces, width=100, sort_dicts=False)}\n"
    )


def _json_payload(inspection: SvgInspection) -> dict[str, object]:
    payload = asdict(inspection)
    payload["polygons"] = [asdict(polygon) for polygon in inspection.polygons]
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect straight-sided polygons and periodic translation candidates in an SVG.",
    )
    parser.add_argument("svg", type=Path, help="Reference SVG to inspect")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument(
        "--sketch-output", type=Path, help="Write a normalized editable sketch starter"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        inspection = inspect_svg(args.svg)
    except (OSError, ET.ParseError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    if args.sketch_output:
        args.sketch_output.parent.mkdir(parents=True, exist_ok=True)
        args.sketch_output.write_text(
            render_sketch_starter(args.svg, inspection),
            encoding="utf-8",
        )
    if args.json:
        print(json.dumps(_json_payload(inspection), indent=2))
    else:
        print(f"polygons: {inspection.polygon_count}")
        print(f"regular polygons: {inspection.regular_polygon_count}")
        print(f"kinds: {inspection.kind_counts}")
        print(f"bounds: {inspection.bounds}")
        print("candidate translations (dx, dy, support):")
        for candidate in inspection.candidate_translations:
            print(f"  {candidate}")
        if args.sketch_output:
            print(f"sketch starter: {args.sketch_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
