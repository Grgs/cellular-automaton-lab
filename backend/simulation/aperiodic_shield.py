from __future__ import annotations

import math

from backend.simulation.aperiodic_support import AperiodicPatch, AperiodicPatchCell, patch_from_cells


_RING_STEP = 3.2


def _rotate(point: tuple[float, float], angle: float) -> tuple[float, float]:
    cosine = math.cos(angle)
    sine = math.sin(angle)
    x_value, y_value = point
    return (
        (x_value * cosine) - (y_value * sine),
        (x_value * sine) + (y_value * cosine),
    )


def _transform(
    vertices: tuple[tuple[float, float], ...],
    *,
    angle: float,
    center: tuple[float, float],
) -> tuple[tuple[float, float], ...]:
    cx, cy = center
    return tuple(
        (
            round(rotated[0] + cx, 6),
            round(rotated[1] + cy, 6),
        )
        for rotated in (_rotate(vertex, angle) for vertex in vertices)
    )


def _center(vertices: tuple[tuple[float, float], ...]) -> tuple[float, float]:
    return (
        round(sum(vertex[0] for vertex in vertices) / len(vertices), 6),
        round(sum(vertex[1] for vertex in vertices) / len(vertices), 6),
    )


def _cell(
    cell_id: str,
    kind: str,
    vertices: tuple[tuple[float, float], ...],
    *,
    neighbors: tuple[str, ...],
    orientation_token: str | None = None,
    chirality_token: str | None = None,
    decoration_tokens: tuple[str, ...] | None = None,
) -> AperiodicPatchCell:
    return AperiodicPatchCell(
        id=cell_id,
        kind=kind,
        center=_center(vertices),
        vertices=vertices,
        neighbors=neighbors,
        tile_family="shield",
        orientation_token=orientation_token,
        chirality_token=chirality_token,
        decoration_tokens=decoration_tokens,
    )


def build_shield_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = max(0, int(patch_depth))
    rings = 1 + (resolved_depth * 2)
    sector_count = 12
    cells_by_id: dict[str, AperiodicPatchCell] = {}

    shield_polygon = (
        (-0.5, -1.0),
        (0.0, -1.5),
        (0.5, -1.0),
        (0.5, 1.0),
        (0.0, 1.5),
        (-0.5, 1.0),
    )
    square_left = (
        (-1.5, -0.5),
        (-0.5, -0.5),
        (-0.5, 0.5),
        (-1.5, 0.5),
    )
    square_right = (
        (0.5, -0.5),
        (1.5, -0.5),
        (1.5, 0.5),
        (0.5, 0.5),
    )
    triangle_top_left = (
        (-0.5, -1.0),
        (0.0, -1.5),
        (-1.0, -1.5),
    )
    triangle_top_right = (
        (0.0, -1.5),
        (0.5, -1.0),
        (1.0, -1.5),
    )
    triangle_bottom_left = (
        (-1.0, 1.5),
        (0.0, 1.5),
        (-0.5, 1.0),
    )
    triangle_bottom_right = (
        (0.0, 1.5),
        (1.0, 1.5),
        (0.5, 1.0),
    )

    for ring in range(rings):
        radius = ring * _RING_STEP
        sectors = 1 if ring == 0 else sector_count
        for sector in range(sectors):
            angle = 0.0 if ring == 0 else sector * (math.pi / 6)
            if ring > 0:
                angle += (ring % 2) * (math.pi / 12)
            center = (radius * math.cos(angle), radius * math.sin(angle))
            orientation_token = str(int(round(math.degrees(angle))) % 360)

            shield_id = f"shield:shield:{ring}:{sector}"
            left_square_id = f"shield:square:{ring}:{sector}:left"
            right_square_id = f"shield:square:{ring}:{sector}:right"
            triangle_ids = (
                f"shield:triangle:{ring}:{sector}:top-left",
                f"shield:triangle:{ring}:{sector}:top-right",
                f"shield:triangle:{ring}:{sector}:bottom-left",
                f"shield:triangle:{ring}:{sector}:bottom-right",
            )

            cells_by_id[shield_id] = _cell(
                shield_id,
                "shield-shield",
                _transform(shield_polygon, angle=angle, center=center),
                neighbors=(left_square_id, right_square_id, *triangle_ids),
                orientation_token=orientation_token,
                decoration_tokens=("arrow-ring", "cross"),
            )
            cells_by_id[left_square_id] = _cell(
                left_square_id,
                "shield-square",
                _transform(square_left, angle=angle, center=center),
                neighbors=(shield_id,),
                orientation_token=orientation_token,
            )
            cells_by_id[right_square_id] = _cell(
                right_square_id,
                "shield-square",
                _transform(square_right, angle=angle, center=center),
                neighbors=(shield_id,),
                orientation_token=orientation_token,
            )

            triangles = (
                (triangle_ids[0], triangle_top_left, "left"),
                (triangle_ids[1], triangle_top_right, "right"),
                (triangle_ids[2], triangle_bottom_left, "left"),
                (triangle_ids[3], triangle_bottom_right, "right"),
            )
            for triangle_id, polygon, chirality_token in triangles:
                cells_by_id[triangle_id] = _cell(
                    triangle_id,
                    "shield-triangle",
                    _transform(polygon, angle=angle, center=center),
                    neighbors=(shield_id,),
                    orientation_token=orientation_token,
                    chirality_token=chirality_token,
                    decoration_tokens=("cross-arm",),
                )

    resolved_cells: list[AperiodicPatchCell] = []
    for cell_id, cell in sorted(cells_by_id.items()):
        neighbors = set(cell.neighbors)
        parts = cell_id.split(":")
        ring = int(parts[2])
        sector = int(parts[3])
        if parts[1] == "shield":
            sectors = 1 if ring == 0 else sector_count
            if ring > 0:
                neighbors.add(f"shield:shield:{ring}:{(sector - 1) % sectors}")
                neighbors.add(f"shield:shield:{ring}:{(sector + 1) % sectors}")
                if ring > 0:
                    parent_sectors = 1 if ring - 1 == 0 else sector_count
                    neighbors.add(f"shield:shield:{ring - 1}:{sector % parent_sectors}")
                if ring + 1 < rings:
                    child_sectors = 1 if ring + 1 == 0 else sector_count
                    neighbors.add(f"shield:shield:{ring + 1}:{sector % child_sectors}")
            elif rings > 1:
                for sector_index in range(sector_count):
                    neighbors.add(f"shield:shield:1:{sector_index}")

        resolved_cells.append(
            AperiodicPatchCell(
                id=cell.id,
                kind=cell.kind,
                center=cell.center,
                vertices=cell.vertices,
                neighbors=tuple(sorted(neighbor for neighbor in neighbors if neighbor in cells_by_id)),
                tile_family=cell.tile_family,
                orientation_token=cell.orientation_token,
                chirality_token=cell.chirality_token,
                decoration_tokens=cell.decoration_tokens,
            )
        )

    return patch_from_cells(resolved_depth, resolved_cells)
