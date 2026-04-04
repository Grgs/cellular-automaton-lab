# Tiling Architecture Notes

This is the short version of how tilings fit into the app.

## Generator Families

- Regular grids
  - built from neighbor-offset tables in `backend/simulation/topology_regular.py`
  - examples: `square`, `hex`, `triangle`
- Periodic mixed / periodic-face families
  - built from descriptor data in `backend/simulation/periodic_face_tilings.py`
  - examples: Archimedean variants, Cairo, Rhombille, dual/uniform-derived mixed tilings
- Aperiodic substitution families
  - built through `backend/simulation/aperiodic_registry.py`
  - shared helpers live in `backend/simulation/aperiodic_substitution.py` and `backend/simulation/aperiodic_support.py`
  - examples: Penrose, Ammann-Beenker, Spectre, Taylor-Socolar, Sphinx, Hat, Chair, Robinson, Tuebingen Triangle, Square-Triangle, Shield, Pinwheel

## Verification Layers

- `tools/validate_tilings.py`
  - geometric sanity only
  - asks “does the topology build, connect, and look internally valid?”
- `tools/verify_reference_tilings.py`
  - source-backed reference verification
  - asks “does the canonical sample match the literature-backed invariants we encoded?”

## Why The Verifier Uses Different Sample Modes

- Regular and periodic families are checked on canonical `3x3` samples because the app builds finite open-boundary boards for those geometries.
- Aperiodic families are checked on patch-depth samples because that is the public sizing mode and the natural way their generators expose structure.

## Exact-Affine Special Case

- `pinwheel` uses an exact-affine helper path for verification.
- The goal is to avoid trusting rounded float edge coincidence for a family with dense orientation diversity.
- Other families still verify through the normal topology payload unless they later need exact-record verification too.

## Where To Extend Things

- Add or refine source-backed invariants:
  - `backend/simulation/literature_reference_specs.py`
- Change how observations are collected:
  - `backend/simulation/literature_reference_verification.py`
- Add stronger periodic-face descriptor checks:
  - `backend/simulation/periodic_face_tilings.py`
- Add or change generator behavior:
  - the relevant builder under `backend/simulation/`
