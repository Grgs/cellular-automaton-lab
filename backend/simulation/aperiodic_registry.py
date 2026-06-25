from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from backend.simulation.aperiodic_ammann_beenker import build_ammann_beenker_patch
from backend.simulation.aperiodic_chair import build_chair_patch
from backend.simulation.aperiodic_dodecagonal_square_triangle import (
    build_dodecagonal_square_triangle_patch,
)
from backend.simulation.aperiodic_enneagonal_9_fold import build_enneagonal_9_fold_patch
from backend.simulation.aperiodic_family_manifest import (
    AMMANN_BEENKER_GEOMETRY,
    APERIODIC_FAMILY_MANIFEST,
    CHAIR_GEOMETRY,
    DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
    ENNEAGONAL_9_FOLD_GEOMETRY,
    HAT_MONOTILE_GEOMETRY,
    HEPTAGONAL_7_FOLD_GEOMETRY,
    PENROSE_P1_GEOMETRY,
    PENROSE_P1_PBS_GEOMETRY,
    PENROSE_P2_GEOMETRY,
    PINWHEEL_2_1_GEOMETRY,
    PINWHEEL_GEOMETRY,
    ROBINSON_TRIANGLES_GEOMETRY,
    SHIELD_GEOMETRY,
    SOCOLAR_12_FOLD_GEOMETRY,
    SPECTRE_GEOMETRY,
    SPHINX_GEOMETRY,
    TAYLOR_SOCOLAR_GEOMETRY,
    TUEBINGEN_TRIANGLE_GEOMETRY,
    TURTLE_MONOTILE_GEOMETRY,
)
from backend.simulation.aperiodic_hat import build_hat_patch
from backend.simulation.aperiodic_heptagonal_7_fold import build_heptagonal_7_fold_patch
from backend.simulation.aperiodic_penrose_p1 import build_penrose_p1_patch
from backend.simulation.aperiodic_penrose_p1_pbs import build_penrose_p1_pbs_patch
from backend.simulation.aperiodic_penrose_p2 import build_penrose_p2_patch
from backend.simulation.aperiodic_pinwheel import build_pinwheel_patch
from backend.simulation.aperiodic_pinwheel_2_1 import build_pinwheel_2_1_patch
from backend.simulation.aperiodic_robinson_triangles import build_robinson_triangles_patch
from backend.simulation.aperiodic_shield import build_shield_patch
from backend.simulation.aperiodic_socolar_12_fold import build_socolar_12_fold_patch
from backend.simulation.aperiodic_spectre import build_spectre_patch
from backend.simulation.aperiodic_sphinx import build_sphinx_patch
from backend.simulation.aperiodic_support import AperiodicPatch
from backend.simulation.aperiodic_taylor_socolar import build_taylor_socolar_patch
from backend.simulation.aperiodic_tuebingen_triangle import build_tuebingen_triangle_patch
from backend.simulation.aperiodic_turtle import build_turtle_patch

AperiodicPatchBuilder = Callable[[int], AperiodicPatch]


@dataclass(frozen=True)
class AperiodicFamilyDefinition:
    geometry_key: str
    builder_kind: str
    build_patch: AperiodicPatchBuilder


_APERIODIC_PATCH_BUILDERS: dict[str, AperiodicPatchBuilder] = {
    PENROSE_P1_GEOMETRY: build_penrose_p1_patch,
    PENROSE_P1_PBS_GEOMETRY: build_penrose_p1_pbs_patch,
    PENROSE_P2_GEOMETRY: build_penrose_p2_patch,
    AMMANN_BEENKER_GEOMETRY: build_ammann_beenker_patch,
    SPECTRE_GEOMETRY: build_spectre_patch,
    TAYLOR_SOCOLAR_GEOMETRY: build_taylor_socolar_patch,
    SPHINX_GEOMETRY: build_sphinx_patch,
    HAT_MONOTILE_GEOMETRY: build_hat_patch,
    TURTLE_MONOTILE_GEOMETRY: build_turtle_patch,
    CHAIR_GEOMETRY: build_chair_patch,
    ROBINSON_TRIANGLES_GEOMETRY: build_robinson_triangles_patch,
    TUEBINGEN_TRIANGLE_GEOMETRY: build_tuebingen_triangle_patch,
    DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY: build_dodecagonal_square_triangle_patch,
    SHIELD_GEOMETRY: build_shield_patch,
    PINWHEEL_GEOMETRY: build_pinwheel_patch,
    PINWHEEL_2_1_GEOMETRY: build_pinwheel_2_1_patch,
    SOCOLAR_12_FOLD_GEOMETRY: build_socolar_12_fold_patch,
    ENNEAGONAL_9_FOLD_GEOMETRY: build_enneagonal_9_fold_patch,
    HEPTAGONAL_7_FOLD_GEOMETRY: build_heptagonal_7_fold_patch,
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
