"""Shared exact-arithmetic substitution helper for pinwheel-family generators.

Both ``aperiodic_pinwheel.py`` (Conway-Radin pinwheel, 1:2:sqrt(5)) and
``aperiodic_pinwheel_2_1.py`` (Bielefeld pinwheel-2-1, 1:4:sqrt(17))
share the same scaffold:

  - A canonically-oriented base right triangle with vertices in
    (small-angle, right-angle, large-angle) order
  - A list of children expressed in the base triangle's local coordinates
  - A ``_map_local`` similarity that places each child inside any parent
    of the same canonical orientation
  - Per-record metadata (kind, tile_family, orientation token, chirality
    token) and a recursive ``_collect`` walk that emits depth-d cells

This module provides:

  - ``ExactPoint`` / ``ExactTriangle`` type aliases over ``Fraction``
  - Stateless ``orientation_token`` and ``chirality_token`` helpers
  - ``ExactSimilaritySubstitution`` dataclass: per-family substitution
    parameters plus ``subdivide`` / ``collect_exact_records`` /
    ``build_patch`` methods that consume them

Adding another pinwheel-family substitution (e.g. a 3-prototile variant)
then becomes a single dataclass declaration.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    ExactPatchRecord,
    patch_from_exact_records,
)


ExactPoint = tuple[Fraction, Fraction]
ExactTriangle = tuple[ExactPoint, ExactPoint, ExactPoint]


def orientation_token(vertices: ExactTriangle) -> str:
    """Return the longest-edge angle (degrees, mod 360) as a string token."""
    edges: list[tuple[Fraction, ExactPoint, ExactPoint]] = []
    for index, start in enumerate(vertices):
        end = vertices[(index + 1) % len(vertices)]
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        edges.append((dx * dx + dy * dy, start, end))
    _, start, end = max(edges, key=lambda item: item[0])
    angle = math.degrees(math.atan2(float(end[1] - start[1]), float(end[0] - start[0])))
    return str(int(round(angle)) % 360)


def chirality_token(vertices: ExactTriangle) -> str:
    """Return "left" if the (small, right, large) ordering is counter-clockwise."""
    (ax, ay), (bx, by), (cx, cy) = vertices
    area_twice = ((bx - ax) * (cy - ay)) - ((cx - ax) * (by - ay))
    return "left" if area_twice >= 0 else "right"


@dataclass(frozen=True)
class ExactSimilaritySubstitution:
    """Parameterized exact-Fraction substitution for canonical right triangles.

    The base triangle's long leg runs from ``base_triangle[0]`` (small-angle
    vertex) to ``base_triangle[1]`` (right-angle vertex); its short leg runs
    from ``base_triangle[1]`` to ``base_triangle[2]`` (large-angle vertex).
    ``_map_local`` divides the local x-coordinate by the long-leg length, so
    children expressed in local coords with x in ``[0, long_leg]`` and y in
    ``[0, short_leg]`` land inside any parent of the same canonical shape.

    ``children`` is a tuple of ``(kind, local_vertices)`` pairs -- the kind
    label lets families with multiple prototile sizes (e.g. pinwheel-2-1)
    distinguish them.

    ``roots`` is a tuple of depth-0 triangles in *world* coordinates (not
    local). Pairing two roots into a rectangle is the convention used by
    both pinwheel and pinwheel-2-1.
    """

    base_triangle: ExactTriangle
    children: tuple[tuple[str, ExactTriangle], ...]
    roots: tuple[ExactTriangle, ...]
    id_prefix: str
    tile_family: str
    root_kind: str
    inflation_factor: float
    neighbor_mode: str = "segment_overlap"

    @property
    def _long_leg(self) -> Fraction:
        return self.base_triangle[1][0] - self.base_triangle[0][0]

    def map_local(self, parent: ExactTriangle, point: ExactPoint) -> ExactPoint:
        """Map a local-coords point into ``parent``'s world position."""
        (ax, ay), (bx, by), (cx, cy) = parent
        x_value, y_value = point
        delta_x = bx - ax
        delta_y = by - ay
        long_leg = self._long_leg
        return (
            ax + (delta_x * x_value / long_leg) + ((cx - bx) * y_value),
            ay + (delta_y * x_value / long_leg) + ((cy - by) * y_value),
        )

    def subdivide(self, parent: ExactTriangle) -> tuple[tuple[str, ExactTriangle], ...]:
        """Return the kinded children of ``parent`` in world coordinates."""
        return tuple(
            (
                kind,
                (
                    self.map_local(parent, child[0]),
                    self.map_local(parent, child[1]),
                    self.map_local(parent, child[2]),
                ),
            )
            for kind, child in self.children
        )

    def _record(self, path: str, kind: str, vertices: ExactTriangle) -> ExactPatchRecord:
        return {
            "id": f"{self.id_prefix}:{path}",
            "kind": kind,
            "vertices": vertices,
            "tile_family": self.tile_family,
            "orientation_token": orientation_token(vertices),
            "chirality_token": chirality_token(vertices),
        }

    def _collect(
        self,
        kind: str,
        vertices: ExactTriangle,
        remaining_depth: int,
        path: str,
        records: list[ExactPatchRecord],
    ) -> None:
        if remaining_depth <= 0:
            records.append(self._record(path, kind, vertices))
            return
        for index, (child_kind, child_vertices) in enumerate(self.subdivide(vertices)):
            self._collect(
                child_kind, child_vertices, remaining_depth - 1, f"{path}.{index}", records
            )

    def collect_exact_records(self, patch_depth: int) -> tuple[ExactPatchRecord, ...]:
        """Walk the substitution to ``patch_depth`` and return exact-Fraction records."""
        resolved_depth = max(0, int(patch_depth))
        records: list[ExactPatchRecord] = []
        for index, root in enumerate(self.roots):
            self._collect(self.root_kind, root, resolved_depth, f"root{index}", records)
        return tuple(records)

    def build_patch(self, patch_depth: int) -> AperiodicPatch:
        """Build a float-coordinate ``AperiodicPatch`` from the substitution."""
        resolved_depth = max(0, int(patch_depth))
        inflation_scale = self.inflation_factor**resolved_depth
        patch = patch_from_exact_records(
            resolved_depth,
            list(self.collect_exact_records(resolved_depth)),
            float_scale=inflation_scale,
            vertex_precision=None,
            neighbor_mode=self.neighbor_mode,  # type: ignore[arg-type]
        )
        return AperiodicPatch(
            patch_depth=patch.patch_depth,
            width=max(3, patch.width),
            height=max(3, patch.height),
            cells=patch.cells,
        )


__all__ = [
    "ExactPoint",
    "ExactSimilaritySubstitution",
    "ExactTriangle",
    "chirality_token",
    "orientation_token",
]
