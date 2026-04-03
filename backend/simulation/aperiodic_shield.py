from __future__ import annotations

from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    PatchRecord,
    Vec,
    patch_from_records,
    polygon_centroid,
    rounded_point,
)


def _centroid(vertices: tuple[tuple[float, float], ...]) -> tuple[float, float]:
    return rounded_point(polygon_centroid(tuple(Vec(x, y) for x, y in vertices)))


def _square_record(x: int, y: int) -> PatchRecord:
    vertices = (
        (float(x - 1), float(y) + 0.5),
        (float(x), float(y) + 0.5),
        (float(x), float(y) + 1.5),
        (float(x - 1), float(y) + 1.5),
    )
    return {
        "id": f"shield:square:{x}:{y}",
        "kind": "shield-square",
        "center": _centroid(vertices),
        "vertices": tuple(rounded_point(vertex) for vertex in vertices),
        "tile_family": "shield",
    }


def _right_square_record(x: int, y: int) -> PatchRecord:
    vertices = (
        (float(x + 1), float(y) + 0.5),
        (float(x + 2), float(y) + 0.5),
        (float(x + 2), float(y) + 1.5),
        (float(x + 1), float(y) + 1.5),
    )
    return {
        "id": f"shield:outer-square:{x}:{y}",
        "kind": "shield-square",
        "center": _centroid(vertices),
        "vertices": tuple(rounded_point(vertex) for vertex in vertices),
        "tile_family": "shield",
    }


def _triangle_record(
    *,
    block_x: int,
    block_y: int,
    index: int,
    vertices: tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
) -> PatchRecord:
    return {
        "id": f"shield:triangle:{block_x}:{block_y}:{index}",
        "kind": "shield-triangle",
        "center": _centroid(vertices),
        "vertices": tuple(rounded_point(vertex) for vertex in vertices),
        "tile_family": "shield",
        "decoration_tokens": ("corner",),
        "chirality_token": "left" if index % 2 == 0 else "right",
    }


def _shield_record(block_x: int, block_y: int) -> PatchRecord:
    x = float(block_x)
    y = float(block_y)
    vertices = (
        (x, y + 0.5),
        (x + 0.5, y),
        (x + 1.0, y + 0.5),
        (x + 1.0, y + 1.5),
        (x + 0.5, y + 2.0),
        (x, y + 1.5),
    )
    return {
        "id": f"shield:shield:{block_x}:{block_y}",
        "kind": "shield-shield",
        "center": _centroid(vertices),
        "vertices": tuple(rounded_point(vertex) for vertex in vertices),
        "tile_family": "shield",
        "decoration_tokens": ("arrow-ring", "cross"),
        "orientation_token": "vertical",
    }


def build_shield_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = max(0, int(patch_depth))
    rows = max(1, 2 ** resolved_depth)
    records: list[PatchRecord] = []
    for block_y in range(rows):
        x = 0
        y = block_y * 2
        records.append(_shield_record(x, y))
        records.append(_square_record(x, y))
        records.append(_right_square_record(x, y))
        records.append(
            _triangle_record(
                block_x=x,
                block_y=y,
                index=0,
                vertices=((x, y), (x + 0.5, y), (x, y + 0.5)),
            )
        )
        records.append(
            _triangle_record(
                block_x=x,
                block_y=y,
                index=1,
                vertices=((x + 0.5, y), (x + 1, y), (x + 1, y + 0.5)),
            )
        )
        records.append(
            _triangle_record(
                block_x=x,
                block_y=y,
                index=2,
                vertices=((x, y + 1.5), (x + 0.5, y + 2), (x, y + 2)),
            )
        )
        records.append(
            _triangle_record(
                block_x=x,
                block_y=y,
                index=3,
                vertices=((x + 1, y + 1.5), (x + 1, y + 2), (x + 0.5, y + 2)),
            )
        )
    return patch_from_records(resolved_depth, records)
