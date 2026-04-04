# Tiling Verification Status

This file tracks the current verification level for every tiling family in the app.

Legend:

- `Geometric sanity`: passes `py -3 tools/validate_tilings.py`
- `Literature verification`: passes `py -3 tools/verify_reference_tilings.py`
- `Strength`: how strong the current literature check is

## Current Status

| Group | Geometries | Geometric sanity | Literature verification | Strength | Notes |
| --- | --- | --- | --- | --- | --- |
| Regular grids | `square`, `hex`, `triangle` | PASS | PASS | Sample-level exact | Verified on canonical open-boundary `3x3` samples with exact totals, adjacency pairs, degree histograms, and signatures. |
| Classic aperiodic | `penrose-p3-rhombs`, `penrose-p3-rhombs-vertex`, `penrose-p2-kite-dart`, `ammann-beenker` | PASS | PASS | Patch-level exact | Verified by patch-depth counts, allowed kinds, adjacency invariants, and deterministic signatures. |
| Newer substitution aperiodic | `spectre`, `taylor-socolar`, `sphinx`, `robinson-triangles`, `tuebingen-triangle`, `square-triangle` | PASS | PASS | Mixed | Stronger than render checks, but still mostly based on low-depth counts, metadata, adjacency, and signatures rather than full substitution-matrix proofs. Separate no-overlap diagnostics now also flag overlap regressions in the families that still fail positive-area overlap checks. |
| Newer substitution aperiodic | `hat-monotile`, `chair`, `shield`, `pinwheel` | PASS | PASS | Mixed, stricter staged graduated to pass | Hat now uses a deterministic multi-hat root cluster with the expected reflected-neighbor local pattern, Chair now exposes a deterministic multiscale chair hierarchy, Shield now carries recursive decoration-state variants, and Pinwheel now expands on the exact-affine inflation path instead of subdividing inside a fixed rectangle. Separate no-overlap diagnostics now keep Chair clean and explicitly flag overlap regressions for the currently problematic families. |
| Periodic mixed / periodic-face | `archimedean-4-8-8`, `archimedean-3-12-12`, `archimedean-3-4-6-4`, `archimedean-4-6-12`, `archimedean-3-3-4-3-4`, `archimedean-3-3-3-4-4`, `archimedean-3-3-3-3-6`, `trihexagonal-3-6-3-6`, `cairo-pentagonal`, `rhombille`, `deltoidal-hexagonal`, `tetrakis-square`, `triakis-triangular`, `deltoidal-trihexagonal`, `prismatic-pentagonal`, `floret-pentagonal`, `snub-square-dual` | PASS | PASS | Sample-level exact + descriptor semantics | Verified on canonical `3x3` samples with exact totals, kind counts, adjacency sets, degree histograms, deterministic signatures, and periodic-face descriptor semantics including slot vocabularies, ID-pattern round-trips, translation behavior, and row offsets. |

## Next Up

- Upgrade periodic mixed verification from `3x3` sample checks to stronger source-backed structural invariants such as vertex configurations and dual-family relationships.
- Replace the remaining generic fallback sources with stronger family-specific references where available.
- Add richer canonical-patch fixtures for substitution families that currently rely mostly on signatures and count invariants.
