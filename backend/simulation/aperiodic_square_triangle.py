from __future__ import annotations

from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    PatchRecord,
    Vec,
    patch_from_records,
    polygon_centroid,
    rounded_point,
)


def _bit_parity(value: int) -> int:
    return int(bin(abs(int(value))).count("1") % 2)


def _square_record(x: int, y: int) -> PatchRecord:
    vertices = (
        (float(x), float(y)),
        (float(x + 1), float(y)),
        (float(x + 1), float(y + 1)),
        (float(x), float(y + 1)),
    )
    centroid = polygon_centroid(tuple(Vec(px, py) for px, py in vertices))
    return {
        "id": f"sqtri:s:{x}:{y}",
        "kind": "square-triangle-square",
        "center": rounded_point(centroid),
        "vertices": tuple(rounded_point(vertex) for vertex in vertices),
        "tile_family": "square-triangle",
        "orientation_token": "square",
    }


def _triangle_record(
    *,
    x: int,
    y: int,
    index: int,
    vertices: tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
    orientation_token: str,
    chirality_token: str,
) -> PatchRecord:
    centroid = polygon_centroid(tuple(Vec(px, py) for px, py in vertices))
    return {
        "id": f"sqtri:t:{x}:{y}:{index}",
        "kind": "square-triangle-triangle",
        "center": rounded_point(centroid),
        "vertices": tuple(rounded_point(vertex) for vertex in vertices),
        "tile_family": "square-triangle",
        "orientation_token": orientation_token,
        "chirality_token": chirality_token,
    }


def build_square_triangle_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = max(0, int(patch_depth))
    size = max(1, 2 ** resolved_depth)
    records: list[PatchRecord] = []
    for y in range(size):
        for x in range(size):
            parity = _bit_parity(x) ^ _bit_parity(y)
            if parity == 0 and ((x + y + resolved_depth) % 3 != 1):
                records.append(_square_record(x, y))
                continue
            if ((x + y + resolved_depth) % 2) == 0:
                records.append(
                    _triangle_record(
                        x=x,
                        y=y,
                        index=0,
                        vertices=((x, y), (x + 1, y), (x + 1, y + 1)),
                        orientation_token="diag-ne",
                        chirality_token="left",
                    )
                )
                records.append(
                    _triangle_record(
                        x=x,
                        y=y,
                        index=1,
                        vertices=((x, y), (x + 1, y + 1), (x, y + 1)),
                        orientation_token="diag-ne",
                        chirality_token="right",
                    )
                )
            else:
                records.append(
                    _triangle_record(
                        x=x,
                        y=y,
                        index=0,
                        vertices=((x, y), (x + 1, y), (x, y + 1)),
                        orientation_token="diag-nw",
                        chirality_token="left",
                    )
                )
                records.append(
                    _triangle_record(
                        x=x,
                        y=y,
                        index=1,
                        vertices=((x + 1, y), (x + 1, y + 1), (x, y + 1)),
                        orientation_token="diag-nw",
                        chirality_token="right",
                    )
                )
    return patch_from_records(resolved_depth, records)
