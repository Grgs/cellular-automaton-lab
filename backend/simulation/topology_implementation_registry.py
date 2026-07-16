from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from backend.simulation.aperiodic_family_manifest import (
    APERIODIC_FAMILY_IDS,
    PENROSE_P1_DISTRIBUTED_GEOMETRY,
    PENROSE_P1_GEOMETRY,
    PENROSE_P1_PBS_GEOMETRY,
    PENROSE_VERTEX_GEOMETRY,
    SPHINX_COMPACT_PAIR_GEOMETRY,
    SPHINX_WIDE_PAIR_GEOMETRY,
)
from backend.simulation.periodic_face_tilings import PERIODIC_FACE_TILING_GEOMETRIES
from backend.simulation.topology_family_manifest import (
    HEX_GEOMETRY,
    SQUARE_GEOMETRY,
    TRIANGLE_GEOMETRY,
)

if TYPE_CHECKING:
    from backend.simulation.topology_types import LatticeCell

BuilderKind = Literal["regular_grid", "periodic_face", "substitution_patch"]
RenderKind = Literal["regular_grid", "polygon_periodic", "polygon_aperiodic"]
TopologyImplementationBuilder = Callable[
    [str, int, int, int | None],
    "TopologyBuildCells",
]
TopologyCellCountEstimator = Callable[[str, int, int, int | None], int]


@dataclass(frozen=True)
class TopologyBuildCells:
    width: int
    height: int
    patch_depth: int | None
    cells: tuple[LatticeCell, ...]


@dataclass(frozen=True)
class TopologyImplementationDefinition:
    geometry_key: str
    builder_kind: BuilderKind
    render_kind: RenderKind
    builder_ref: TopologyImplementationBuilder
    estimate_cell_count_ref: TopologyCellCountEstimator | None


def _estimate_regular_cell_count(
    geometry: str, width: int, height: int, patch_depth: int | None
) -> int:
    del geometry, patch_depth
    return max(0, width) * max(0, height)


def _estimate_periodic_face_cell_count(
    geometry: str, width: int, height: int, patch_depth: int | None
) -> int:
    from backend.simulation.periodic_face_tilings import get_periodic_face_tiling_descriptor

    del patch_depth
    return get_periodic_face_tiling_descriptor(geometry).estimate_cell_count(width, height)


def _build_square_geometry(
    geometry: str,
    width: int,
    height: int,
    patch_depth: int | None,
) -> TopologyBuildCells:
    from backend.simulation.topology_regular import build_square_cells

    del geometry, patch_depth
    return TopologyBuildCells(
        width=width,
        height=height,
        patch_depth=None,
        cells=tuple(build_square_cells(width, height)),
    )


def _build_hex_geometry(
    geometry: str,
    width: int,
    height: int,
    patch_depth: int | None,
) -> TopologyBuildCells:
    from backend.simulation.topology_regular import build_hex_cells

    del geometry, patch_depth
    return TopologyBuildCells(
        width=width,
        height=height,
        patch_depth=None,
        cells=tuple(build_hex_cells(width, height)),
    )


def _build_triangle_geometry(
    geometry: str,
    width: int,
    height: int,
    patch_depth: int | None,
) -> TopologyBuildCells:
    from backend.simulation.topology_regular import build_triangle_cells

    del geometry, patch_depth
    return TopologyBuildCells(
        width=width,
        height=height,
        patch_depth=None,
        cells=tuple(build_triangle_cells(width, height)),
    )


def _build_periodic_face_geometry(
    geometry: str,
    width: int,
    height: int,
    patch_depth: int | None,
) -> TopologyBuildCells:
    from backend.simulation.topology_specialized import build_periodic_face_topology_cells

    del patch_depth
    return TopologyBuildCells(
        width=width,
        height=height,
        patch_depth=None,
        cells=build_periodic_face_topology_cells(geometry, width, height),
    )


def _build_aperiodic_geometry(
    geometry: str,
    width: int,
    height: int,
    patch_depth: int | None,
) -> TopologyBuildCells:
    from backend.simulation.topology_specialized import build_aperiodic_topology_cells

    del width, height
    patch_width, patch_height, resolved_patch_depth, cells = build_aperiodic_topology_cells(
        geometry,
        0 if patch_depth is None else int(patch_depth),
    )
    return TopologyBuildCells(
        width=patch_width,
        height=patch_height,
        patch_depth=resolved_patch_depth,
        cells=cells,
    )


_PERIODIC_FACE_GEOMETRIES = PERIODIC_FACE_TILING_GEOMETRIES

_APERIODIC_GEOMETRIES = (
    PENROSE_VERTEX_GEOMETRY,
    PENROSE_P1_DISTRIBUTED_GEOMETRY,
    PENROSE_P1_PBS_GEOMETRY,
    *(geometry for geometry in APERIODIC_FAMILY_IDS if geometry != PENROSE_P1_GEOMETRY),
    SPHINX_COMPACT_PAIR_GEOMETRY,
    SPHINX_WIDE_PAIR_GEOMETRY,
)

_IMPLEMENTATIONS = {
    SQUARE_GEOMETRY: TopologyImplementationDefinition(
        geometry_key=SQUARE_GEOMETRY,
        builder_kind="regular_grid",
        render_kind="regular_grid",
        builder_ref=_build_square_geometry,
        estimate_cell_count_ref=_estimate_regular_cell_count,
    ),
    HEX_GEOMETRY: TopologyImplementationDefinition(
        geometry_key=HEX_GEOMETRY,
        builder_kind="regular_grid",
        render_kind="regular_grid",
        builder_ref=_build_hex_geometry,
        estimate_cell_count_ref=_estimate_regular_cell_count,
    ),
    TRIANGLE_GEOMETRY: TopologyImplementationDefinition(
        geometry_key=TRIANGLE_GEOMETRY,
        builder_kind="regular_grid",
        render_kind="regular_grid",
        builder_ref=_build_triangle_geometry,
        estimate_cell_count_ref=_estimate_regular_cell_count,
    ),
    **{
        geometry: TopologyImplementationDefinition(
            geometry_key=geometry,
            builder_kind="periodic_face",
            render_kind="polygon_periodic",
            builder_ref=_build_periodic_face_geometry,
            estimate_cell_count_ref=_estimate_periodic_face_cell_count,
        )
        for geometry in _PERIODIC_FACE_GEOMETRIES
    },
    **{
        geometry: TopologyImplementationDefinition(
            geometry_key=geometry,
            builder_kind="substitution_patch",
            render_kind="polygon_aperiodic",
            builder_ref=_build_aperiodic_geometry,
            estimate_cell_count_ref=None,
        )
        for geometry in _APERIODIC_GEOMETRIES
    },
}


def get_topology_implementation(
    geometry_key: str | None,
) -> TopologyImplementationDefinition:
    resolved_geometry = str(geometry_key or SQUARE_GEOMETRY)
    return _IMPLEMENTATIONS.get(resolved_geometry, _IMPLEMENTATIONS[SQUARE_GEOMETRY])


def render_kind_for_geometry(geometry_key: str | None) -> str:
    return get_topology_implementation(geometry_key).render_kind


def describe_topology_implementations() -> tuple[TopologyImplementationDefinition, ...]:
    return tuple(_IMPLEMENTATIONS.values())
