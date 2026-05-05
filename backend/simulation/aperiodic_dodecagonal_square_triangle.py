from __future__ import annotations

import math
from collections import defaultdict, deque
from functools import lru_cache

from backend.simulation.aperiodic_family_manifest import (
    DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
    DODECAGONAL_SQUARE_TRIANGLE_TILE_FAMILY,
    DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
)
from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    PatchRecord,
    patch_from_records,
)


# Decorated 3.12.12 Archimedean tiling.
#
# The classical Archimedean (3.12.12) tiling places one regular dodecagon and
# one equilateral triangle around each vertex (hexagonal lattice of dodecagon
# centres separated by 2 + sqrt(3) and shared with one triangle per gap). We
# decompose every regular dodecagon into its canonical layout of six unit
# squares and twelve unit equilateral triangles, then keep the bridging
# triangles between dodecagons. The result:
#
#  - is built only from unit squares and unit equilateral triangles
#  - tiles the plane exactly (the underlying 3.12.12 Archimedean tiling does)
#  - is locally 12-fold symmetric inside every former-dodecagon region
#  - is periodic at the dodecagonal-supercell scale, so it scales to any
#    requested patch_depth without a vendored data dependency
#
# This is not the canonical Schlottmann quasi-periodic square-triangle tiling
# (that would need marked prototiles for the substitution to close). It is a
# deterministic generator that gives the family its dodecagonal flavour and
# scales without depth limits.

_TILE_FAMILY = DODECAGONAL_SQUARE_TRIANGLE_TILE_FAMILY
_SQUARE_KIND = DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND
_TRIANGLE_KIND = DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND
_TRIANGLE_CHIRALITIES = ("red", "yellow", "blue")

_SQRT3 = math.sqrt(3.0)
_COORD_DECIMALS = 6

# Unit hexagon circumradius is 1; its apothem is sqrt(3)/2. The decorated
# dodecagon's apothem is (2 + sqrt(3))/2 (hexagon apothem + one square edge).
_HEX_APOTHEM = _SQRT3 / 2.0
_DODEC_APOTHEM = (2.0 + _SQRT3) / 2.0
_DODEC_LATTICE_PITCH = 2.0 * _DODEC_APOTHEM  # 2 + sqrt(3)
_LATTICE_BASIS_X = (_DODEC_LATTICE_PITCH, 0.0)
_LATTICE_BASIS_Y = (
    _DODEC_LATTICE_PITCH * 0.5,
    _DODEC_LATTICE_PITCH * (_SQRT3 / 2.0),
)


def _round_coord(value: float) -> float:
    return round(value, _COORD_DECIMALS)


def _polygon_center(
    vertices: tuple[tuple[float, float], ...],
) -> tuple[float, float]:
    count = len(vertices)
    return (
        sum(vertex[0] for vertex in vertices) / count,
        sum(vertex[1] for vertex in vertices) / count,
    )


def _round_vertices(
    vertices: tuple[tuple[float, float], ...],
) -> tuple[tuple[float, float], ...]:
    return tuple((_round_coord(vertex[0]), _round_coord(vertex[1])) for vertex in vertices)


def _orientation_token_from_first_edge(
    vertices: tuple[tuple[float, float], ...],
) -> str:
    edge = (
        vertices[1][0] - vertices[0][0],
        vertices[1][1] - vertices[0][1],
    )
    angle = math.degrees(math.atan2(edge[1], edge[0])) % 360.0
    return str(int(round(angle / 30.0) * 30) % 360)


def _triangle_chirality_from_centroid(
    vertices: tuple[tuple[float, float], ...],
) -> str:
    centroid = _polygon_center(vertices)
    angle = (
        math.degrees(
            math.atan2(
                vertices[0][1] - centroid[1],
                vertices[0][0] - centroid[0],
            )
        )
        % 360.0
    )
    bucket = int(angle // 120) % 3
    return _TRIANGLE_CHIRALITIES[bucket]


def _hex_corner(index: int) -> tuple[float, float]:
    """Unit hexagon corner k at distance 1 from origin, k = 0 at angle 0."""
    angle = math.radians(60.0 * index)
    return (math.cos(angle), math.sin(angle))


def _square_outer_corner_at(hex_corner_index: int, edge_index: int) -> tuple[float, float]:
    """Outer corner of the square sitting on hexagon edge `edge_index`,
    at the side adjacent to hexagon corner `hex_corner_index` (which must be
    edge_index or edge_index+1 mod 6).
    """
    inner = _hex_corner(hex_corner_index)
    edge_a = _hex_corner(edge_index)
    edge_b = _hex_corner((edge_index + 1) % 6)
    midpoint = ((edge_a[0] + edge_b[0]) / 2.0, (edge_a[1] + edge_b[1]) / 2.0)
    radial_norm = math.hypot(midpoint[0], midpoint[1])
    radial_unit = (midpoint[0] / radial_norm, midpoint[1] / radial_norm)
    return (inner[0] + radial_unit[0], inner[1] + radial_unit[1])


@lru_cache(maxsize=1)
def _supercell_unit_tiles() -> tuple[
    tuple[str, tuple[tuple[float, float], ...]],
    ...,
]:
    """Tiles inside one supercell, expressed in the supercell's local frame
    (origin at the dodecagon centre)."""
    tiles: list[tuple[str, tuple[tuple[float, float], ...]]] = []

    # Six inner equilateral triangles forming the central regular hexagon: one
    # corner at the origin, the other two at adjacent hexagon corners.
    for index in range(6):
        corner_a = _hex_corner(index)
        corner_b = _hex_corner((index + 1) % 6)
        tiles.append(("triangle", ((0.0, 0.0), corner_a, corner_b)))

    # Six unit squares, one on each hexagon edge, extending outward.
    for edge_index in range(6):
        inner_a = _hex_corner(edge_index)
        inner_b = _hex_corner((edge_index + 1) % 6)
        outer_a = _square_outer_corner_at(edge_index, edge_index)
        outer_b = _square_outer_corner_at((edge_index + 1) % 6, edge_index)
        tiles.append(("square", (inner_a, inner_b, outer_b, outer_a)))

    # Six outer equilateral triangles, one per hexagon corner, between the two
    # adjacent squares.
    for hex_corner_index in range(6):
        apex = _hex_corner(hex_corner_index)
        # The two squares adjacent to this hexagon corner are on edges
        # (corner_index - 1) and (corner_index) (mod 6).
        left_edge = (hex_corner_index - 1) % 6
        right_edge = hex_corner_index
        outer_left = _square_outer_corner_at(hex_corner_index, left_edge)
        outer_right = _square_outer_corner_at(hex_corner_index, right_edge)
        tiles.append(("triangle", (apex, outer_right, outer_left)))

    # Two bridging triangles claimed by this supercell from the underlying
    # 3.12.12 Archimedean tiling. Each dodecagon is surrounded by six bridging
    # triangles (one per dodecagon corner where three dodecagons meet); each
    # triangle is shared by three dodecagons. To partition them across
    # supercells we claim only the triangles whose relative angle from the
    # supercell centre falls in {30 deg, 90 deg}. The orbit-of-three under
    # 120-degree rotation guarantees each plane triangle is claimed by exactly
    # one supercell.
    bridge_angles_deg = (30.0, 90.0)
    bridge_apex_distance = _DODEC_APOTHEM + (_SQRT3 / 2.0)
    for angle_deg in bridge_angles_deg:
        angle = math.radians(angle_deg)
        # The bridging triangle has one vertex (the apex) pointing away from
        # this dodecagon's centre, and an opposite edge that lies along the
        # dodecagon edge at distance _DODEC_APOTHEM in the same direction.
        edge_mid = (
            _DODEC_APOTHEM * math.cos(angle),
            _DODEC_APOTHEM * math.sin(angle),
        )
        perp_x = -math.sin(angle)
        perp_y = math.cos(angle)
        edge_a = (edge_mid[0] + 0.5 * perp_x, edge_mid[1] + 0.5 * perp_y)
        edge_b = (edge_mid[0] - 0.5 * perp_x, edge_mid[1] - 0.5 * perp_y)
        apex = (
            bridge_apex_distance * math.cos(angle),
            bridge_apex_distance * math.sin(angle),
        )
        tiles.append(("triangle", (edge_a, apex, edge_b)))

    return tuple(tiles)


def _supercell_anchor(
    column: int,
    row: int,
) -> tuple[float, float]:
    return (
        column * _LATTICE_BASIS_X[0] + row * _LATTICE_BASIS_Y[0],
        column * _LATTICE_BASIS_X[1] + row * _LATTICE_BASIS_Y[1],
    )


def _supercell_records(
    column: int,
    row: int,
) -> list[PatchRecord]:
    anchor = _supercell_anchor(column, row)
    records: list[PatchRecord] = []
    for tile_index, (tile_kind, local_vertices) in enumerate(_supercell_unit_tiles()):
        translated = tuple(
            (vertex[0] + anchor[0], vertex[1] + anchor[1]) for vertex in local_vertices
        )
        rounded = _round_vertices(translated)
        center = _polygon_center(rounded)
        if tile_kind == "square":
            records.append(
                {
                    "id": f"dst:dec:S:{column}:{row}:{tile_index}",
                    "kind": _SQUARE_KIND,
                    "center": (_round_coord(center[0]), _round_coord(center[1])),
                    "vertices": rounded,
                    "tile_family": _TILE_FAMILY,
                    "orientation_token": _orientation_token_from_first_edge(rounded),
                    "chirality_token": None,
                    "decoration_tokens": None,
                }
            )
        else:
            records.append(
                {
                    "id": f"dst:dec:T:{column}:{row}:{tile_index}",
                    "kind": _TRIANGLE_KIND,
                    "center": (_round_coord(center[0]), _round_coord(center[1])),
                    "vertices": rounded,
                    "tile_family": _TILE_FAMILY,
                    "orientation_token": _orientation_token_from_first_edge(rounded),
                    "chirality_token": _triangle_chirality_from_centroid(rounded),
                    "decoration_tokens": None,
                }
            )
    return records


def _depth_to_supercell_radius(patch_depth: int) -> int:
    if patch_depth <= 0:
        return 1
    # Empirically each ring of supercells covers roughly four BFS-edge hops.
    return max(1, int(math.ceil(patch_depth / 4.0)) + 1)


def _generate_records_within_radius(
    supercell_radius: int,
) -> list[PatchRecord]:
    records: list[PatchRecord] = []
    for column in range(-supercell_radius, supercell_radius + 1):
        for row in range(-supercell_radius, supercell_radius + 1):
            records.extend(_supercell_records(column, row))
    return records


def _seed_record_id(records: list[PatchRecord]) -> str:
    candidates = [record for record in records if record["kind"] == _SQUARE_KIND]
    pool = candidates if candidates else records
    return min(
        pool,
        key=lambda record: (
            record["center"][0] ** 2 + record["center"][1] ** 2,
            record["id"],
        ),
    )["id"]


def _bfs_distances_via_edge_sharing(
    records: list[PatchRecord],
    seed_id: str,
) -> dict[str, int]:
    edge_to_records: dict[
        tuple[tuple[float, float], tuple[float, float]],
        list[str],
    ] = defaultdict(list)
    for record in records:
        vertices = record["vertices"]
        for index in range(len(vertices)):
            head = vertices[index]
            tail = vertices[(index + 1) % len(vertices)]
            head_key = (
                round(head[0], _COORD_DECIMALS),
                round(head[1], _COORD_DECIMALS),
            )
            tail_key = (
                round(tail[0], _COORD_DECIMALS),
                round(tail[1], _COORD_DECIMALS),
            )
            edge_key = (head_key, tail_key) if head_key < tail_key else (tail_key, head_key)
            edge_to_records[edge_key].append(record["id"])

    adjacency: dict[str, set[str]] = defaultdict(set)
    for owners in edge_to_records.values():
        if len(owners) < 2:
            continue
        for left_index in range(len(owners)):
            for right_index in range(left_index + 1, len(owners)):
                left = owners[left_index]
                right = owners[right_index]
                if left == right:
                    continue
                adjacency[left].add(right)
                adjacency[right].add(left)

    distances: dict[str, int] = {seed_id: 0}
    queue: deque[str] = deque((seed_id,))
    while queue:
        current = queue.popleft()
        for neighbor in adjacency[current]:
            if neighbor in distances:
                continue
            distances[neighbor] = distances[current] + 1
            queue.append(neighbor)
    return distances


def build_dodecagonal_square_triangle_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = int(patch_depth)
    if resolved_depth < 0:
        raise ValueError("patch_depth must be non-negative")

    supercell_radius = _depth_to_supercell_radius(resolved_depth)
    records = _generate_records_within_radius(supercell_radius)
    seed_id = _seed_record_id(records)
    distances = _bfs_distances_via_edge_sharing(records, seed_id)

    while max(distances.values(), default=0) < resolved_depth:
        supercell_radius += 1
        records = _generate_records_within_radius(supercell_radius)
        seed_id = _seed_record_id(records)
        distances = _bfs_distances_via_edge_sharing(records, seed_id)

    selected_ids = {
        cell_id for cell_id, distance in distances.items() if distance <= resolved_depth
    }
    cropped = [record for record in records if record["id"] in selected_ids]
    return patch_from_records(
        resolved_depth,
        cropped,
        edge_precision=_COORD_DECIMALS,
    )
