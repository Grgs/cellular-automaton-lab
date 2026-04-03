from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from backend.simulation.aperiodic_ammann_beenker import build_ammann_beenker_patch
from backend.simulation.aperiodic_chair import build_chair_patch
from backend.simulation.aperiodic_penrose_p2 import build_penrose_p2_patch
from backend.simulation.aperiodic_robinson_triangles import build_robinson_triangles_patch
from backend.simulation.aperiodic_sphinx import build_sphinx_patch
from backend.simulation.aperiodic_spectre import build_spectre_patch
from backend.simulation.aperiodic_support import AperiodicPatch
from backend.simulation.aperiodic_taylor_socolar import build_taylor_socolar_patch
from backend.simulation.topology_catalog import (
    AMMANN_BEENKER_GEOMETRY,
    CHAIR_GEOMETRY,
    PENROSE_P2_GEOMETRY,
    ROBINSON_TRIANGLES_GEOMETRY,
    SPHINX_GEOMETRY,
    SPECTRE_GEOMETRY,
    TAYLOR_SOCOLAR_GEOMETRY,
)


AperiodicPatchBuilder = Callable[[int], AperiodicPatch]


@dataclass(frozen=True)
class AperiodicFamilyDefinition:
    geometry_key: str
    builder_kind: str
    build_patch: AperiodicPatchBuilder


_APERIODIC_FAMILIES: dict[str, AperiodicFamilyDefinition] = {
    PENROSE_P2_GEOMETRY: AperiodicFamilyDefinition(
        geometry_key=PENROSE_P2_GEOMETRY,
        builder_kind="compatibility_patch",
        build_patch=build_penrose_p2_patch,
    ),
    AMMANN_BEENKER_GEOMETRY: AperiodicFamilyDefinition(
        geometry_key=AMMANN_BEENKER_GEOMETRY,
        builder_kind="compatibility_patch",
        build_patch=build_ammann_beenker_patch,
    ),
    SPECTRE_GEOMETRY: AperiodicFamilyDefinition(
        geometry_key=SPECTRE_GEOMETRY,
        builder_kind="substitution_recipe",
        build_patch=build_spectre_patch,
    ),
    TAYLOR_SOCOLAR_GEOMETRY: AperiodicFamilyDefinition(
        geometry_key=TAYLOR_SOCOLAR_GEOMETRY,
        builder_kind="substitution_recipe",
        build_patch=build_taylor_socolar_patch,
    ),
    SPHINX_GEOMETRY: AperiodicFamilyDefinition(
        geometry_key=SPHINX_GEOMETRY,
        builder_kind="substitution_recipe",
        build_patch=build_sphinx_patch,
    ),
    CHAIR_GEOMETRY: AperiodicFamilyDefinition(
        geometry_key=CHAIR_GEOMETRY,
        builder_kind="substitution_recipe",
        build_patch=build_chair_patch,
    ),
    ROBINSON_TRIANGLES_GEOMETRY: AperiodicFamilyDefinition(
        geometry_key=ROBINSON_TRIANGLES_GEOMETRY,
        builder_kind="substitution_recipe",
        build_patch=build_robinson_triangles_patch,
    ),
}


def build_registered_aperiodic_patch(geometry: str, patch_depth: int) -> AperiodicPatch:
    try:
        family = _APERIODIC_FAMILIES[geometry]
    except KeyError as error:
        raise ValueError(f"Unsupported aperiodic geometry '{geometry}'.") from error
    return family.build_patch(int(patch_depth))
