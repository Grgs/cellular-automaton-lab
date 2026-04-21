from __future__ import annotations

from collections import Counter

import math

from shapely.geometry import Polygon
from shapely.ops import unary_union

from generator import (
    MAX_PATCH_DEPTH,
    SQUARE_KIND,
    TRIANGLE_KIND,
    build_dodecagonal_square_triangle_patch,
)


def _union_metrics(patch_depth: int) -> tuple[int, int, int, bool]:
    patch = build_dodecagonal_square_triangle_patch(patch_depth)
    polygons = [Polygon(cell["vertices"]) for cell in patch["cells"]]
    merged = unary_union(polygons)
    total_area = sum(polygon.area for polygon in polygons)
    union_area = sum(
        geometry.area
        for geometry in (merged.geoms if hasattr(merged, "geoms") else [merged])
    )
    components = len(merged.geoms) if hasattr(merged, "geoms") else 1
    holes = sum(
        len(geometry.interiors)
        for geometry in (merged.geoms if hasattr(merged, "geoms") else [merged])
        if hasattr(geometry, "interiors")
    )
    return len(polygons), components, holes, math.isclose(total_area, union_area, rel_tol=0.0, abs_tol=1e-7)


def test_depth_zero_is_single_center_square() -> None:
    patch = build_dodecagonal_square_triangle_patch(0)

    assert patch["patch_depth"] == 0
    assert len(patch["cells"]) == 1

    cell = patch["cells"][0]
    assert cell["kind"] == SQUARE_KIND
    assert cell["chirality_token"] is None
    assert cell["neighbors"] == ()
    assert cell["tile_family"] == "dodecagonal-square-triangle"
    assert cell["orientation_token"] in {"60", "150", "240", "330"}


def test_depth_five_crop_is_connected_and_hole_free() -> None:
    cell_count, components, holes, area_matches = _union_metrics(5)

    assert cell_count == 60
    assert components == 1
    assert holes == 0
    assert area_matches


def test_depth_seven_stays_connected_and_hole_free() -> None:
    cell_count, components, holes, area_matches = _union_metrics(MAX_PATCH_DEPTH)

    assert cell_count == 111
    assert components == 1
    assert holes == 0
    assert area_matches


def test_neighbor_links_are_reciprocal() -> None:
    patch = build_dodecagonal_square_triangle_patch(5)
    by_id = {cell["id"]: cell for cell in patch["cells"]}

    for cell in patch["cells"]:
        for neighbor_id in cell["neighbors"]:
            assert cell["id"] in by_id[neighbor_id]["neighbors"]


def test_depth_five_contains_both_public_kinds() -> None:
    patch = build_dodecagonal_square_triangle_patch(5)
    kinds = Counter(cell["kind"] for cell in patch["cells"])

    assert kinds[SQUARE_KIND] > 0
    assert kinds[TRIANGLE_KIND] > 0
