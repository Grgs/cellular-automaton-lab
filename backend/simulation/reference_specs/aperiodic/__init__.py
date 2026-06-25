from __future__ import annotations

from backend.simulation.reference_specs.types import ReferenceFamilySpec

from . import (
    ammann_beenker,
    chair,
    dodecagonal_square_triangle,
    enneagonal_9_fold,
    hat_monotile,
    hendecagonal_11_fold,
    heptagonal_7_fold,
    penrose,
    pinwheel,
    pinwheel_2_1,
    robinson_triangles,
    shield,
    socolar_12_fold,
    spectre,
    sphinx,
    taylor_socolar,
    tuebingen_triangle,
    turtle_monotile,
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
    **turtle_monotile.SPECS,
    **tuebingen_triangle.SPECS,
    **dodecagonal_square_triangle.SPECS,
    **shield.SPECS,
    **pinwheel.SPECS,
    **pinwheel_2_1.SPECS,
    **socolar_12_fold.SPECS,
    **enneagonal_9_fold.SPECS,
    **heptagonal_7_fold.SPECS,
    **hendecagonal_11_fold.SPECS,
}

__all__ = ["APERIODIC_REFERENCE_FAMILY_SPECS"]
