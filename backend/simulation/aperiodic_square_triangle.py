from __future__ import annotations

import math

from backend.simulation.aperiodic_support import AperiodicPatch, AperiodicPatchCell, patch_from_cells


_SQRT3_OVER_2 = math.sqrt(3) / 2
_SQUARE_KIND = "square-triangle-square"
_TRIANGLE_KIND = "square-triangle-triangle"
_RING_STEP = 2.6


def _rotate(point: tuple[float, float], angle: float) -> tuple[float, float]:
    cosine = math.cos(angle)
    sine = math.sin(angle)
    x_value, y_value = point
    return (
        (x_value * cosine) - (y_value * sine),
        (x_value * sine) + (y_value * cosine),
    )


def _translate(
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


def _polygon_center(vertices: tuple[tuple[float, float], ...]) -> tuple[float, float]:
    return (
        round(sum(vertex[0] for vertex in vertices) / len(vertices), 6),
        round(sum(vertex[1] for vertex in vertices) / len(vertices), 6),
    )


def _cell(
    cell_id: str,
    kind: str,
    vertices: tuple[tuple[float, float], ...],
    *,
    tile_family: str,
    neighbors: tuple[str, ...],
    orientation_token: str | None = None,
    chirality_token: str | None = None,
) -> AperiodicPatchCell:
    return AperiodicPatchCell(
        id=cell_id,
        kind=kind,
        center=_polygon_center(vertices),
        vertices=vertices,
        neighbors=neighbors,
        tile_family=tile_family,
        orientation_token=orientation_token,
        chirality_token=chirality_token,
    )


def build_square_triangle_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = max(0, int(patch_depth))
    rings = 1 + (resolved_depth * 2)
    sector_count = 12
    cells_by_id: dict[str, AperiodicPatchCell] = {}

    square_vertices = (
        (-0.5, -0.5),
        (0.5, -0.5),
        (0.5, 0.5),
        (-0.5, 0.5),
    )
    triangle_up = (
        (-0.5, 0.5),
        (0.5, 0.5),
        (0.0, 0.5 + _SQRT3_OVER_2),
    )
    triangle_left = (
        (-1.0, 0.5 + _SQRT3_OVER_2),
        (-0.5, 0.5),
        (0.0, 0.5 + _SQRT3_OVER_2),
    )
    triangle_right = (
        (0.0, 0.5 + _SQRT3_OVER_2),
        (0.5, 0.5),
        (1.0, 0.5 + _SQRT3_OVER_2),
    )

    for ring in range(rings):
        radius = ring * _RING_STEP
        sectors = 1 if ring == 0 else sector_count
        for sector in range(sectors):
            angle = 0.0 if ring == 0 else sector * (math.pi / 6)
            if ring > 0:
                angle += (ring % 2) * (math.pi / 12)
            center = (radius * math.cos(angle), radius * math.sin(angle))
            square_id = f"sqtri:s:{ring}:{sector}"
            square_orientation = str(int(round(math.degrees(angle + (math.pi / 4)))) % 360)

            square = _cell(
                square_id,
                _SQUARE_KIND,
                _translate(square_vertices, angle=angle, center=center),
                tile_family="square-triangle",
                neighbors=(),
                orientation_token=square_orientation,
            )
            cells_by_id[square_id] = square

            triangle_specs: list[
                tuple[
                    str,
                    tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
                    str,
                    str,
                ]
            ] = [
                (f"sqtri:t:{ring}:{sector}:apex", triangle_up, "apex", "left"),
                (f"sqtri:t:{ring}:{sector}:left", triangle_left, "left", "left"),
                (f"sqtri:t:{ring}:{sector}:right", triangle_right, "right", "right"),
            ]

            for triangle_id, local_vertices, orientation_token, chirality_token in triangle_specs:
                triangle_neighbors = (square_id,) if orientation_token == "apex" else ()
                cells_by_id[triangle_id] = _cell(
                    triangle_id,
                    _TRIANGLE_KIND,
                    _translate(local_vertices, angle=angle, center=center),
                    tile_family="square-triangle",
                    neighbors=triangle_neighbors,
                    orientation_token=orientation_token,
                    chirality_token=chirality_token,
                )

    # Rebuild cells with ring/sector connectivity so the topology remains connected.
    resolved_cells: list[AperiodicPatchCell] = []
    for cell_id, cell in sorted(cells_by_id.items()):
        neighbors = set(cell.neighbors)
        parts = cell_id.split(":")
        if parts[1] == "s":
            ring = int(parts[2])
            sector = int(parts[3])
            sectors = 1 if ring == 0 else sector_count
            neighbors.add(f"sqtri:t:{ring}:{sector}:apex")
            if ring > 0:
                neighbors.add(f"sqtri:s:{ring}:{(sector - 1) % sectors}")
                neighbors.add(f"sqtri:s:{ring}:{(sector + 1) % sectors}")
                parent_sectors = 1 if ring - 1 == 0 else sector_count
                neighbors.add(f"sqtri:s:{ring - 1}:{sector % parent_sectors}")
                if ring + 1 < rings:
                    child_sectors = 1 if ring + 1 == 0 else sector_count
                    neighbors.add(f"sqtri:s:{ring + 1}:{sector % child_sectors}")
            elif rings > 1:
                for sector_index in range(sector_count):
                    neighbors.add(f"sqtri:s:1:{sector_index}")
        elif parts[1] == "t":
            ring = int(parts[2])
            sector = int(parts[3])
            variant = parts[4]
            if variant == "apex":
                neighbors.add(f"sqtri:s:{ring}:{sector}")
                neighbors.add(f"sqtri:t:{ring}:{sector}:left")
                neighbors.add(f"sqtri:t:{ring}:{sector}:right")
            elif variant == "left":
                neighbors.add(f"sqtri:t:{ring}:{sector}:apex")
                if ring > 0:
                    neighbors.add(f"sqtri:t:{ring}:{(sector - 1) % sector_count}:right")
            elif variant == "right":
                neighbors.add(f"sqtri:t:{ring}:{sector}:apex")
                if ring > 0:
                    neighbors.add(f"sqtri:t:{ring}:{(sector + 1) % sector_count}:left")

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
            )
        )

    return patch_from_cells(resolved_depth, resolved_cells)
