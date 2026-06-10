from __future__ import annotations

from backend.simulation.reference_specs.types import ReferenceFamilySpec

from . import (
    ammann_beenker,
    chair,
    dodecagonal_square_triangle,
    hat_monotile,
    penrose,
    pinwheel,
    pinwheel_2_1,
    robinson_triangles,
    shield,
    spectre,
    sphinx,
    taylor_socolar,
    tuebingen_triangle,
)

APERIODIC_REFERENCE_FAMILY_SPECS: dict[str, ReferenceFamilySpec] = {
    **penrose.SPECS,
    **ammann_beenker.SPECS,
    **spectre.SPECS,
    **taylor_socolar.SPECS,
    **sphinx.SPECS,
    **chair.SPECS,
    **robinson_triangles.SPECS,
    **hat_monotile.SPECS,
    **tuebingen_triangle.SPECS,
    **dodecagonal_square_triangle.SPECS,
    **shield.SPECS,
    **pinwheel.SPECS,
    **pinwheel_2_1.SPECS,
}

__all__ = ["APERIODIC_REFERENCE_FAMILY_SPECS"]
