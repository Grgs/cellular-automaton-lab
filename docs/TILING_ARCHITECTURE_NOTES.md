# Tiling Architecture Notes

This is the short version of how tilings fit into the app.

## Generator Families

- Regular grids
  - built from neighbor-offset tables in `backend/simulation/topology_regular.py`
  - examples: `square`, `hex`, `triangle`
- Periodic mixed / periodic-face families
  - built from descriptor data in `backend/simulation/periodic_face_tilings.py`
  - examples: Archimedean variants, Cairo, Rhombille, dual/uniform-derived mixed tilings
- Aperiodic families
  - built through `backend/simulation/aperiodic_registry.py`
  - implementation contracts distinguish true substitutions, exact-affine
    paths, canonical patches, and known deviations
  - shared helpers live in `backend/simulation/aperiodic_substitution.py` and the `backend/simulation/aperiodic_support/` package (`affine.py`, `geometry.py`, `neighbors.py`, `patches.py`, `types.py`)
  - examples include substitution families, multigrid crops, exact-affine
    Pinwheel variants, continuum deformations, and the cut-and-project
    `socolar-hexagonal` generator

## Verification Layers

- `python -m tools tilings validate`
  - geometric sanity only
  - asks “does the topology build, connect, and look internally valid?”
- `python -m tools tilings verify`
  - source-backed reference verification
  - asks “does the canonical sample match the literature-backed invariants we encoded?”

## Why The Verifier Uses Different Sample Modes

- Regular and periodic families are checked on canonical `3x3` samples because the app builds finite open-boundary boards for those geometries.
- Aperiodic families are checked on patch-depth samples because that is the public sizing mode and the natural way their generators expose structure.

## Exact-Record Special Cases

- `pinwheel` and `pinwheel-2-1` use exact-affine records for construction and
  verification.
- The goal is to avoid trusting rounded float edge coincidence for families
  with dense orientation diversity.
- `socolar-hexagonal` uses exact `Z[zeta12]` module coordinates and
  `Q(sqrt(3))` acceptance-window tests before final float serialization.
- Other families verify through normal topology payloads unless their
  construction needs a stronger exact-record path.

## Where To Extend Things

- Add or refine source-backed invariants:
  - `backend/simulation/literature_reference_specs.py`
- Change how observations are collected:
  - `backend/simulation/literature_reference_verification.py`
- Add stronger periodic-face descriptor checks:
  - `backend/simulation/periodic_face_tilings.py`
- Add or change generator behavior:
  - the relevant builder under `backend/simulation/`
