from __future__ import annotations

from backend.simulation.reference_specs.types import ReferenceFamilySpec

from . import archimedean
from . import trihexagonal_3_6_3_6
from . import cairo_pentagonal
from . import rhombille
from . import deltoidal_hexagonal
from . import tetrakis_square
from . import triakis_triangular
from . import deltoidal_trihexagonal
from . import prismatic_pentagonal
from . import floret_pentagonal
from . import snub_square_dual
from . import type_7_pentagonal
from . import kisrhombille
from . import tiltwork
from . import pythagorean

PERIODIC_REFERENCE_FAMILY_SPECS: dict[str, ReferenceFamilySpec] = {
    **archimedean.SPECS,
    **trihexagonal_3_6_3_6.SPECS,
    **cairo_pentagonal.SPECS,
    **rhombille.SPECS,
    **deltoidal_hexagonal.SPECS,
    **tetrakis_square.SPECS,
    **triakis_triangular.SPECS,
    **deltoidal_trihexagonal.SPECS,
    **prismatic_pentagonal.SPECS,
    **floret_pentagonal.SPECS,
    **snub_square_dual.SPECS,
    **type_7_pentagonal.SPECS,
    **kisrhombille.SPECS,
    **tiltwork.SPECS,
    **pythagorean.SPECS,
}

__all__ = ["PERIODIC_REFERENCE_FAMILY_SPECS"]
