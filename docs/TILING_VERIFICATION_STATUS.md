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
| Newer substitution aperiodic | `spectre`, `taylor-socolar`, `sphinx`, `robinson-triangles`, `tuebingen-triangle` | PASS | PASS | Mixed | Stronger than render checks, but still mostly based on low-depth counts, metadata, adjacency, signatures, and now contiguity checks rather than full substitution-matrix proofs. Global overlap validation is strict, and the representative render-space overlap fixtures are clean. |
| Newer substitution aperiodic | `hat-monotile` | PASS | PASS | Mixed, stronger | Hat is connected, overlap-clean, and hole-free under the canonical sample checks, while still preserving the reflected-neighbor chirality pattern used by the literature verifier. |
| Experimental aperiodic | `chair` | PASS | PASS | Mixed | Kept in the `Experimental` picker group while browser-visible pattern correctness is re-verified; current automated checks still cover the multiscale chair hierarchy and representative size diversity. |
| Experimental aperiodic | `shield` | PASS | PASS | Mixed, stronger | Kept in the `Experimental` picker group while browser-visible pattern correctness is re-verified; automated checks still cover connectivity, hole freedom, and decoration-token diversity. |
| Experimental aperiodic | `square-triangle` | PASS | PASS | Mixed, depth-3 canonical | Kept in the `Experimental` picker group while browser-visible pattern correctness is re-verified; automated checks still cover the cleaned dense depth-3 canonical sample, kind counts, metadata diversity, and signature. |
| Experimental aperiodic | `pinwheel` | PASS | PASS | Mixed, exact-path stronger | Kept in the `Experimental` picker group while browser-visible pattern correctness is re-verified; automated checks still cover the exact-affine neighbor path, orientation diversity, and expanding support. |
| Periodic mixed / periodic-face | `archimedean-4-8-8`, `archimedean-3-12-12`, `archimedean-3-4-6-4`, `archimedean-4-6-12`, `archimedean-3-3-4-3-4`, `archimedean-3-3-3-4-4`, `archimedean-3-3-3-3-6`, `trihexagonal-3-6-3-6`, `cairo-pentagonal`, `rhombille`, `deltoidal-hexagonal`, `tetrakis-square`, `triakis-triangular`, `deltoidal-trihexagonal`, `prismatic-pentagonal`, `floret-pentagonal`, `snub-square-dual` | PASS | PASS | Sample-level exact + descriptor semantics | Verified on canonical `3x3` samples with exact totals, kind counts, adjacency sets, degree histograms, deterministic signatures, and periodic-face descriptor semantics including slot vocabularies, ID-pattern round-trips, translation behavior, and row offsets. |

## Next Up

- Upgrade periodic mixed verification from `3x3` sample checks to stronger source-backed structural invariants such as vertex configurations and dual-family relationships.
- Replace the remaining generic fallback sources with stronger family-specific references where available.
- Add richer canonical-patch fixtures for substitution families that currently rely mostly on signatures, contiguity checks, and count invariants.
