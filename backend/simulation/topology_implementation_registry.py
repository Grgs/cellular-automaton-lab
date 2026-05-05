from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Literal

from backend.simulation.aperiodic_family_manifest import APERIODIC_FAMILY_IDS
from backend.simulation.topology_catalog_data import (
    AMMANN_BEENKER_GEOMETRY,
    ARCHIMEDEAN_31212_GEOMETRY,
    ARCHIMEDEAN_33336_GEOMETRY,
    ARCHIMEDEAN_33344_GEOMETRY,
    ARCHIMEDEAN_33434_GEOMETRY,
    ARCHIMEDEAN_3464_GEOMETRY,
    ARCHIMEDEAN_4612_GEOMETRY,
    ARCHIMEDEAN_488_GEOMETRY,
    CAIRO_GEOMETRY,
    CHAIR_GEOMETRY,
    DELTOIDAL_HEXAGONAL_GEOMETRY,
    DELTOIDAL_TRIHEXAGONAL_GEOMETRY,
    FLORET_PENTAGONAL_GEOMETRY,
    HAT_MONOTILE_GEOMETRY,
    HEX_GEOMETRY,
    KAGOME_GEOMETRY,
    PENROSE_GEOMETRY,
    PENROSE_P2_GEOMETRY,
    PENROSE_VERTEX_GEOMETRY,
    PINWHEEL_GEOMETRY,
    PRISMATIC_PENTAGONAL_GEOMETRY,
    RHOMBILLE_GEOMETRY,
    ROBINSON_TRIANGLES_GEOMETRY,
    SHIELD_GEOMETRY,
    SNUB_SQUARE_DUAL_GEOMETRY,
    SPHINX_GEOMETRY,
    SPECTRE_GEOMETRY,
    DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
    SQUARE_GEOMETRY,
    TAYLOR_SOCOLAR_GEOMETRY,
    TETRAKIS_SQUARE_GEOMETRY,
    TUEBINGEN_TRIANGLE_GEOMETRY,
    TRIAKIS_TRIANGULAR_GEOMETRY,
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


_PERIODIC_FACE_GEOMETRIES = (
    ARCHIMEDEAN_488_GEOMETRY,
    ARCHIMEDEAN_31212_GEOMETRY,
    ARCHIMEDEAN_3464_GEOMETRY,
    ARCHIMEDEAN_4612_GEOMETRY,
    ARCHIMEDEAN_33434_GEOMETRY,
    ARCHIMEDEAN_33344_GEOMETRY,
    ARCHIMEDEAN_33336_GEOMETRY,
    KAGOME_GEOMETRY,
    CAIRO_GEOMETRY,
    RHOMBILLE_GEOMETRY,
    DELTOIDAL_HEXAGONAL_GEOMETRY,
    DELTOIDAL_TRIHEXAGONAL_GEOMETRY,
    TETRAKIS_SQUARE_GEOMETRY,
    TRIAKIS_TRIANGULAR_GEOMETRY,
    PRISMATIC_PENTAGONAL_GEOMETRY,
    FLORET_PENTAGONAL_GEOMETRY,
    SNUB_SQUARE_DUAL_GEOMETRY,
)

_APERIODIC_GEOMETRIES = (PENROSE_VERTEX_GEOMETRY, *APERIODIC_FAMILY_IDS)

_IMPLEMENTATIONS = {
    SQUARE_GEOMETRY: TopologyImplementationDefinition(
        geometry_key=SQUARE_GEOMETRY,
        builder_kind="regular_grid",
        render_kind="regular_grid",
        builder_ref=_build_square_geometry,
    ),
    HEX_GEOMETRY: TopologyImplementationDefinition(
        geometry_key=HEX_GEOMETRY,
        builder_kind="regular_grid",
        render_kind="regular_grid",
        builder_ref=_build_hex_geometry,
    ),
    TRIANGLE_GEOMETRY: TopologyImplementationDefinition(
        geometry_key=TRIANGLE_GEOMETRY,
        builder_kind="regular_grid",
        render_kind="regular_grid",
        builder_ref=_build_triangle_geometry,
    ),
    **{
        geometry: TopologyImplementationDefinition(
            geometry_key=geometry,
            builder_kind="periodic_face",
            render_kind="polygon_periodic",
            builder_ref=_build_periodic_face_geometry,
        )
        for geometry in _PERIODIC_FACE_GEOMETRIES
    },
    **{
        geometry: TopologyImplementationDefinition(
            geometry_key=geometry,
            builder_kind="substitution_patch",
            render_kind="polygon_aperiodic",
            builder_ref=_build_aperiodic_geometry,
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
