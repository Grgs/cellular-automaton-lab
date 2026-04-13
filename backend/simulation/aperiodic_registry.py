from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from backend.simulation.aperiodic_family_manifest import (
    AMMANN_BEENKER_GEOMETRY,
    APERIODIC_FAMILY_MANIFEST,
    CHAIR_GEOMETRY,
    DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
    HAT_MONOTILE_GEOMETRY,
    PENROSE_P2_GEOMETRY,
    PINWHEEL_GEOMETRY,
    ROBINSON_TRIANGLES_GEOMETRY,
    SHIELD_GEOMETRY,
    SPHINX_GEOMETRY,
    SPECTRE_GEOMETRY,
    TAYLOR_SOCOLAR_GEOMETRY,
    TUEBINGEN_TRIANGLE_GEOMETRY,
)
from backend.simulation.aperiodic_ammann_beenker import build_ammann_beenker_patch
from backend.simulation.aperiodic_chair import build_chair_patch
from backend.simulation.aperiodic_hat import build_hat_patch
from backend.simulation.aperiodic_penrose_p2 import build_penrose_p2_patch
from backend.simulation.aperiodic_pinwheel import build_pinwheel_patch
from backend.simulation.aperiodic_robinson_triangles import build_robinson_triangles_patch
from backend.simulation.aperiodic_shield import build_shield_patch
from backend.simulation.aperiodic_dodecagonal_square_triangle import build_dodecagonal_square_triangle_patch
from backend.simulation.aperiodic_sphinx import build_sphinx_patch
from backend.simulation.aperiodic_spectre import build_spectre_patch
from backend.simulation.aperiodic_support import AperiodicPatch
from backend.simulation.aperiodic_taylor_socolar import build_taylor_socolar_patch
from backend.simulation.aperiodic_tuebingen_triangle import build_tuebingen_triangle_patch


AperiodicPatchBuilder = Callable[[int], AperiodicPatch]


@dataclass(frozen=True)
class AperiodicFamilyDefinition:
    geometry_key: str
    builder_kind: str
    build_patch: AperiodicPatchBuilder


_APERIODIC_PATCH_BUILDERS: dict[str, AperiodicPatchBuilder] = {
    PENROSE_P2_GEOMETRY: build_penrose_p2_patch,
    AMMANN_BEENKER_GEOMETRY: build_ammann_beenker_patch,
    SPECTRE_GEOMETRY: build_spectre_patch,
    TAYLOR_SOCOLAR_GEOMETRY: build_taylor_socolar_patch,
    SPHINX_GEOMETRY: build_sphinx_patch,
    HAT_MONOTILE_GEOMETRY: build_hat_patch,
    CHAIR_GEOMETRY: build_chair_patch,
    ROBINSON_TRIANGLES_GEOMETRY: build_robinson_triangles_patch,
    TUEBINGEN_TRIANGLE_GEOMETRY: build_tuebingen_triangle_patch,
    DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY: build_dodecagonal_square_triangle_patch,
    SHIELD_GEOMETRY: build_shield_patch,
    PINWHEEL_GEOMETRY: build_pinwheel_patch,
}

_APERIODIC_FAMILIES: dict[str, AperiodicFamilyDefinition] = {
    geometry: AperiodicFamilyDefinition(
        geometry_key=geometry,
        builder_kind=APERIODIC_FAMILY_MANIFEST[geometry].builder_kind,
        build_patch=build_patch,
    )
    for geometry, build_patch in _APERIODIC_PATCH_BUILDERS.items()
}


def build_registered_aperiodic_patch(geometry: str, patch_depth: int) -> AperiodicPatch:
    try:
        family = _APERIODIC_FAMILIES[geometry]
    except KeyError as error:
        raise ValueError(f"Unsupported aperiodic geometry '{geometry}'.") from error
    return family.build_patch(int(patch_depth))
