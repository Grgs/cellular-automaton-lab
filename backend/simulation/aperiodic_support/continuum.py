"""Deform one tiling into another by rescaling edges by length class.

This is the engine behind the Tile(a, b) aperiodic-monotile continuum (Smith,
Myers, Kaplan, Goodman-Strauss 2023). Members of the continuum share one
combinatorial tiling; moving between them only changes the two edge lengths.
So a member can be built exactly from an already-verified sibling by walking the
shared-edge graph and rescaling each edge by its length class, without
re-deriving any substitution geometry. The Turtle (``Tile(sqrt(3), 1)``) is
built this way from the Hat (``Tile(1, sqrt(3))``); see
:mod:`backend.simulation.aperiodic_turtle`.
"""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Callable

from .types import COORDINATE_PRECISION, AperiodicPatch

_Point = tuple[float, float]
_VertexKey = tuple[float, float]


def edge_scaled_vertex_map(
    patch: AperiodicPatch,
    edge_scale: Callable[[_Point, _Point], float],
    *,
    key_precision: int = COORDINATE_PRECISION,
    origin: _Point = (0.0, 0.0),
) -> Callable[[_Point], _Point]:
    """Return a function mapping each vertex of ``patch`` to a re-integrated point.

    The patch's vertices are connected into a shared-edge graph (endpoints that
    round to the same ``key_precision`` are identified). Starting from ``origin``
    the graph is walked breadth-first, and each edge ``(start, end)`` contributes
    ``edge_scale(start, end) * (end - start)`` to the running position. The
    returned callable looks a vertex up by the same rounding, so callers can map
    every cell's vertices through it.

    The result is well defined (independent of the walk order) only when every
    closed loop in the graph has zero net displacement under ``edge_scale`` --
    the "balance" property that holds across the Tile(a, b) continuum, where
    each edge class's vectors sum to zero around every cell. Callers are
    responsible for supplying an ``edge_scale`` that preserves that property; an
    unbalanced scaling silently yields an order-dependent (torn) result.

    The patch is assumed to be edge-connected. Disconnected components are each
    anchored at ``origin`` independently, which is only meaningful when there is
    a single component.
    """

    def key(point: _Point) -> _VertexKey:
        return (round(point[0], key_precision), round(point[1], key_precision))

    adjacency: dict[_VertexKey, set[_VertexKey]] = defaultdict(set)
    source_position: dict[_VertexKey, _Point] = {}
    for cell in patch.cells:
        vertices = cell.vertices
        count = len(vertices)
        for index in range(count):
            start = vertices[index]
            end = vertices[(index + 1) % count]
            start_key = key(start)
            end_key = key(end)
            source_position[start_key] = start
            source_position[end_key] = end
            adjacency[start_key].add(end_key)
            adjacency[end_key].add(start_key)

    mapped: dict[_VertexKey, _Point] = {}
    for root in adjacency:
        if root in mapped:
            continue
        mapped[root] = origin
        queue: deque[_VertexKey] = deque((root,))
        while queue:
            current = queue.popleft()
            current_source = source_position[current]
            current_mapped = mapped[current]
            for neighbor in adjacency[current]:
                if neighbor in mapped:
                    continue
                neighbor_source = source_position[neighbor]
                scale = edge_scale(current_source, neighbor_source)
                mapped[neighbor] = (
                    current_mapped[0] + scale * (neighbor_source[0] - current_source[0]),
                    current_mapped[1] + scale * (neighbor_source[1] - current_source[1]),
                )
                queue.append(neighbor)

    def map_vertex(point: _Point) -> _Point:
        return mapped[key(point)]

    return map_vertex
