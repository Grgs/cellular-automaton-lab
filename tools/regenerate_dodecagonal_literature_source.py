from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_PDF = (
    ROOT / "docs" / "contracts" / "dodecagonal-square-triangle-generator" / "bielefeld-patch.pdf"
)
DEFAULT_OUTPUT_PATH = (
    ROOT / "backend" / "simulation" / "data" / "dodecagonal_square_triangle_literature_source.json"
)

SEED_CELL_INDEX = 3557
VERTEX_SNAP_TOLERANCE = 0.005
EDGE_PRECISION = 6

SQUARE_KIND = "dodecagonal-square-triangle-square"
TRIANGLE_KIND = "dodecagonal-square-triangle-triangle"

RED_FILL = (0.541, 0.141, 0.133)
YELLOW_FILL = (1.0, 0.8, 0.4)
BLUE_FILL = (0.42, 0.451, 0.639)


class DodecagonalLiteratureSourceError(ValueError):
    pass


@dataclass(frozen=True)
class _SourceCell:
    index: int
    kind: str
    chirality: str | None
    vertices: tuple[tuple[float, float], ...]
    neighbors: tuple[int, ...]


def _edge_angle(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 360.0


def _ordered_vertices(points: list[tuple[float, float]]) -> tuple[tuple[float, float], ...]:
    cx = sum(x for x, _ in points) / len(points)
    cy = sum(y for _, y in points) / len(points)
    cyclic = sorted(points, key=lambda point: math.atan2(point[1] - cy, point[0] - cx))
    return _rotate_vertices(tuple(cyclic))


def _rotate_vertices(
    vertices: tuple[tuple[float, float], ...],
) -> tuple[tuple[float, float], ...]:
    rotations: list[tuple[float, tuple[tuple[float, float], ...]]] = []
    for offset in range(len(vertices)):
        rotated = vertices[offset:] + vertices[:offset]
        angle = _edge_angle(rotated[0], rotated[1])
        rotations.append((round(angle, 6), tuple(rotated)))
    return min(rotations, key=lambda item: item[0])[1]


def _polygon_center(vertices: tuple[tuple[float, float], ...]) -> tuple[float, float]:
    count = len(vertices)
    return (
        sum(x for x, _ in vertices) / count,
        sum(y for _, y in vertices) / count,
    )


def _extract_fill_vertices(drawing: dict[str, Any]) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for item in drawing["items"]:
        if item[0] == "l":
            points.append((float(item[1].x), float(item[1].y)))
            points.append((float(item[2].x), float(item[2].y)))
        elif item[0] == "re":
            rect = item[1]
            points.extend(
                (
                    (float(rect.x0), float(rect.y0)),
                    (float(rect.x0), float(rect.y1)),
                    (float(rect.x1), float(rect.y1)),
                    (float(rect.x1), float(rect.y0)),
                )
            )

    deduped: list[tuple[float, float]] = []
    seen: set[tuple[float, float]] = set()
    for point in points:
        if point in seen:
            continue
        seen.add(point)
        deduped.append(point)
    return deduped


def _classify_cell(fill: tuple[float, float, float], vertex_count: int) -> tuple[str, str | None]:
    if vertex_count == 4:
        return SQUARE_KIND, None
    if fill == RED_FILL:
        return TRIANGLE_KIND, "red"
    if fill == YELLOW_FILL:
        return TRIANGLE_KIND, "yellow"
    if fill == BLUE_FILL:
        return TRIANGLE_KIND, "blue"
    raise DodecagonalLiteratureSourceError(f"Unexpected triangle fill {fill!r}.")


def _canonical_edge(
    left: tuple[float, float],
    right: tuple[float, float],
) -> tuple[tuple[float, float], tuple[float, float]]:
    rounded_left = (round(left[0], EDGE_PRECISION), round(left[1], EDGE_PRECISION))
    rounded_right = (round(right[0], EDGE_PRECISION), round(right[1], EDGE_PRECISION))
    return (
        (rounded_left, rounded_right)
        if rounded_left <= rounded_right
        else (rounded_right, rounded_left)
    )


def _cluster_points(
    points: set[tuple[float, float]],
) -> dict[tuple[float, float], tuple[float, float]]:
    clusters: list[list[tuple[float, float]]] = []
    point_cluster: dict[tuple[float, float], int] = {}
    for point in sorted(points):
        best_cluster_index: int | None = None
        best_distance: float | None = None
        for cluster_index, cluster_points in enumerate(clusters):
            center = _polygon_center(tuple(cluster_points))
            distance = math.dist(point, center)
            if distance > VERTEX_SNAP_TOLERANCE:
                continue
            if best_distance is None or distance < best_distance:
                best_cluster_index = cluster_index
                best_distance = distance
        if best_cluster_index is None:
            clusters.append([point])
            point_cluster[point] = len(clusters) - 1
            continue
        clusters[best_cluster_index].append(point)
        point_cluster[point] = best_cluster_index

    cluster_centers = tuple(_polygon_center(tuple(cluster)) for cluster in clusters)
    return {point: cluster_centers[cluster_index] for point, cluster_index in point_cluster.items()}


def _rebuild_neighbors(
    cells: dict[int, _SourceCell],
) -> dict[int, tuple[int, ...]]:
    edge_map: defaultdict[
        tuple[tuple[float, float], tuple[float, float]],
        list[int],
    ] = defaultdict(list)
    for index, cell in cells.items():
        for vertex_index, left in enumerate(cell.vertices):
            right = cell.vertices[(vertex_index + 1) % len(cell.vertices)]
            edge_map[_canonical_edge(left, right)].append(index)

    neighbor_map: defaultdict[int, set[int]] = defaultdict(set)
    for owners in edge_map.values():
        unique_owners = tuple(sorted(set(owners)))
        if len(unique_owners) != 2:
            continue
        left_owner, right_owner = unique_owners
        neighbor_map[left_owner].add(right_owner)
        neighbor_map[right_owner].add(left_owner)
    return {index: tuple(sorted(neighbor_map[index])) for index in cells}


def regenerate_literature_source_payload(
    source_pdf: Path = DEFAULT_SOURCE_PDF,
) -> dict[str, object]:
    if not source_pdf.exists():
        raise DodecagonalLiteratureSourceError(f"Missing literature source PDF: {source_pdf}")

    document = fitz.open(source_pdf)
    try:
        page = document[0]
        unique_cells: dict[
            tuple[tuple[tuple[float, float], ...], tuple[float, float, float]],
            tuple[tuple[tuple[float, float], ...], tuple[float, float, float]],
        ] = {}
        for drawing in page.get_drawings():
            if drawing["type"] != "f":
                continue
            raw_vertices = _extract_fill_vertices(drawing)
            if len(raw_vertices) not in (3, 4):
                continue
            rounded_fill = tuple(round(float(channel), 3) for channel in drawing["fill"])
            if len(rounded_fill) != 3:
                raise DodecagonalLiteratureSourceError(
                    f"Unexpected fill tuple {rounded_fill!r} in literature PDF."
                )
            fill = (rounded_fill[0], rounded_fill[1], rounded_fill[2])
            ordered = _ordered_vertices(raw_vertices)
            unique_cells.setdefault((ordered, fill), (ordered, fill))
    finally:
        document.close()

    snap_map = _cluster_points(
        {vertex for vertices, _fill in unique_cells.values() for vertex in vertices}
    )

    snapped_cells: dict[int, _SourceCell] = {}
    for index, (vertices, fill) in enumerate(unique_cells.values()):
        snapped_vertices = _rotate_vertices(tuple(snap_map[vertex] for vertex in vertices))
        kind, chirality = _classify_cell(fill, len(snapped_vertices))
        snapped_cells[index] = _SourceCell(
            index=index,
            kind=kind,
            chirality=chirality,
            vertices=snapped_vertices,
            neighbors=(),
        )

    if SEED_CELL_INDEX not in snapped_cells:
        raise DodecagonalLiteratureSourceError(
            f"Seed cell index {SEED_CELL_INDEX} was not present in the reconstructed source."
        )

    neighbors_by_index = _rebuild_neighbors(snapped_cells)
    cells = [
        {
            "index": index,
            "kind": snapped_cells[index].kind,
            "chirality": snapped_cells[index].chirality,
            "vertices": [[float(x), float(y)] for x, y in snapped_cells[index].vertices],
            "neighbors": list(neighbors_by_index[index]),
        }
        for index in sorted(snapped_cells)
    ]
    return {
        "seed_index": SEED_CELL_INDEX,
        "cells": cells,
    }


def _format_payload(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2) + "\n"


def payload_has_drift(
    output_path: Path = DEFAULT_OUTPUT_PATH,
    *,
    source_pdf: Path = DEFAULT_SOURCE_PDF,
) -> bool:
    if not output_path.exists():
        return True
    current = json.loads(output_path.read_text(encoding="utf-8"))
    regenerated = regenerate_literature_source_payload(source_pdf)
    return current != regenerated


def write_literature_source(
    output_path: Path = DEFAULT_OUTPUT_PATH,
    *,
    source_pdf: Path = DEFAULT_SOURCE_PDF,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        _format_payload(regenerate_literature_source_payload(source_pdf)),
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Regenerate the backend-owned dodecagonal square-triangle literature source "
            "JSON from the checked-in Bielefeld PDF."
        )
    )
    parser.add_argument(
        "--source-pdf",
        type=Path,
        default=DEFAULT_SOURCE_PDF,
        help="Path to the checked-in Bielefeld PDF source.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Destination JSON path. Defaults to the checked-in backend source file.",
    )
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    source_pdf = Path(args.source_pdf)
    output_path = Path(args.output)
    try:
        if bool(args.check):
            if payload_has_drift(output_path, source_pdf=source_pdf):
                print("Dodecagonal literature source drift detected:")
                print(f"  source: {source_pdf}")
                print(f"  output: {output_path}")
                return 1
            print("Dodecagonal literature source is up to date.")
            return 0

        write_literature_source(output_path, source_pdf=source_pdf)
        print("Regenerated dodecagonal literature source:")
        print(f"  source: {source_pdf}")
        print(f"  output: {output_path}")
        return 0
    except DodecagonalLiteratureSourceError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
