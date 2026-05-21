"""Back-compat shim that re-exports the full ``aperiodic_support`` surface.

The implementation is split across focused submodules:

  - ``.types``     -- type aliases + frozen dataclasses + TypedDict records
  - ``.geometry``  -- vertex / edge / centroid / extent helpers
  - ``.affine``    -- 2D affine math + orientation/chirality tokens
  - ``.neighbors`` -- edge-neighbour detection (float + exact-Fraction)
  - ``.patches``   -- high-level patch constructors

Importing ``from backend.simulation.aperiodic_support import X`` keeps working
because everything is re-exported here. New code is welcome to import from the
submodules directly when only one concern is needed.

The ``X as X`` re-export aliases satisfy ruff's F401 "unused import" check by
signalling that the imports are deliberately public re-exports.
"""

from __future__ import annotations

from .affine import affine_apply as affine_apply
from .affine import affine_chirality_token as affine_chirality_token
from .affine import affine_inverse as affine_inverse
from .affine import affine_linear_determinant as affine_linear_determinant
from .affine import affine_multiply as affine_multiply
from .affine import affine_orientation_token as affine_orientation_token
from .affine import id_from_anchor as id_from_anchor
from .affine import id_from_transform as id_from_transform
from .affine import rotation as rotation
from .affine import scale as scale
from .affine import translation as translation
from .affine import translation_to as translation_to
from .geometry import canonical_edge as canonical_edge
from .geometry import compatibility_extent as compatibility_extent
from .geometry import encode_float as encode_float
from .geometry import exact_canonical_edge as exact_canonical_edge
from .geometry import polygon_centroid as polygon_centroid
from .geometry import rounded_point as rounded_point
from .neighbors import build_edge_neighbors as build_edge_neighbors
from .neighbors import build_exact_neighbors as build_exact_neighbors
from .patches import patch_from_cells as patch_from_cells
from .patches import patch_from_exact_records as patch_from_exact_records
from .patches import patch_from_records as patch_from_records
from .types import AFFINE_IDENTITY as AFFINE_IDENTITY
from .types import AFFINE_REFLECT_X as AFFINE_REFLECT_X
from .types import COORDINATE_PRECISION as COORDINATE_PRECISION
from .types import Affine as Affine
from .types import AperiodicPatch as AperiodicPatch
from .types import AperiodicPatchCell as AperiodicPatchCell
from .types import ExactNeighborMode as ExactNeighborMode
from .types import ExactPatchRecord as ExactPatchRecord
from .types import NeighborMode as NeighborMode
from .types import PatchRecord as PatchRecord
from .types import Vec as Vec
