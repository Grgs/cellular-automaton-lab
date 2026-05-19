from __future__ import annotations

from backend.simulation.reference_specs.types import ReferenceFamilySpec

from . import penrose
from . import ammann_beenker
from . import spectre
from . import taylor_socolar
from . import sphinx
from . import chair
from . import robinson_triangles
from . import hat_monotile
from . import tuebingen_triangle
from . import dodecagonal_square_triangle
from . import shield
from . import pinwheel
from . import pinwheel_2_1

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
