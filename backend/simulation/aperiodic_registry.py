from __future__ import annotations

from collections.abc import Callable

from backend.simulation.aperiodic_ammann_beenker import build_ammann_beenker_patch
from backend.simulation.aperiodic_penrose_p2 import build_penrose_p2_patch
from backend.simulation.aperiodic_spectre import build_spectre_patch
from backend.simulation.aperiodic_support import AperiodicPatch
from backend.simulation.aperiodic_taylor_socolar import build_taylor_socolar_patch
from backend.simulation.topology_catalog import (
    AMMANN_BEENKER_GEOMETRY,
    PENROSE_P2_GEOMETRY,
    SPECTRE_GEOMETRY,
    TAYLOR_SOCOLAR_GEOMETRY,
)


AperiodicPatchBuilder = Callable[[int], AperiodicPatch]


_APERIODIC_PATCH_BUILDERS: dict[str, AperiodicPatchBuilder] = {
    PENROSE_P2_GEOMETRY: build_penrose_p2_patch,
    AMMANN_BEENKER_GEOMETRY: build_ammann_beenker_patch,
    SPECTRE_GEOMETRY: build_spectre_patch,
    TAYLOR_SOCOLAR_GEOMETRY: build_taylor_socolar_patch,
}


def build_registered_aperiodic_patch(geometry: str, patch_depth: int) -> AperiodicPatch:
    try:
        builder = _APERIODIC_PATCH_BUILDERS[geometry]
    except KeyError as error:
        raise ValueError(f"Unsupported aperiodic geometry '{geometry}'.") from error
    return builder(int(patch_depth))
