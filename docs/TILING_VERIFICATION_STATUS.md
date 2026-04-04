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
| Newer substitution aperiodic | `spectre`, `taylor-socolar`, `sphinx`, `robinson-triangles`, `tuebingen-triangle`, `chair` | PASS | PASS | Mixed | Stronger than render checks, but still mostly based on low-depth counts, metadata, adjacency, signatures, and now contiguity checks rather than full substitution-matrix proofs. Global overlap validation is strict, and the representative render-space overlap fixtures are clean. |
| Newer substitution aperiodic | `hat-monotile` | PASS | PASS | Mixed, stronger | Hat is connected, overlap-clean, and hole-free under the canonical sample checks, while still preserving the reflected-neighbor chirality pattern used by the literature verifier. |
| Newer substitution aperiodic | `shield` | PASS | PASS | Mixed, stronger | Shield is now connected, overlap-clean, and hole-free under the canonical sample checks, while still emitting multiple decoration variants for the decorated kinds. |
| Newer substitution aperiodic | `square-triangle` | PASS | FAIL | Mixed, surface-hole gap exposed | Square-Triangle is connected and overlap-clean, but its canonical sample still forms enclosed empty holes in the merged polygon surface. The hardened literature verifier treats those surrounded gaps as blocking failures. |
| Newer substitution aperiodic | `pinwheel` | PASS | FAIL | Mixed, contiguity gap exposed | The hardened literature verifier blocks Pinwheel because its canonical sample splits into multiple disconnected components in the topology neighbor graph, even though geometric sanity, overlap checks, and hole checks still pass. |
| Periodic mixed / periodic-face | `archimedean-4-8-8`, `archimedean-3-12-12`, `archimedean-3-4-6-4`, `archimedean-4-6-12`, `archimedean-3-3-4-3-4`, `archimedean-3-3-3-4-4`, `archimedean-3-3-3-3-6`, `trihexagonal-3-6-3-6`, `cairo-pentagonal`, `rhombille`, `deltoidal-hexagonal`, `tetrakis-square`, `triakis-triangular`, `deltoidal-trihexagonal`, `prismatic-pentagonal`, `floret-pentagonal`, `snub-square-dual` | PASS | PASS | Sample-level exact + descriptor semantics | Verified on canonical `3x3` samples with exact totals, kind counts, adjacency sets, degree histograms, deterministic signatures, and periodic-face descriptor semantics including slot vocabularies, ID-pattern round-trips, translation behavior, and row offsets. |

## Next Up

- Upgrade periodic mixed verification from `3x3` sample checks to stronger source-backed structural invariants such as vertex configurations and dual-family relationships.
- Replace the remaining generic fallback sources with stronger family-specific references where available.
- Repair `square-triangle` so its canonical sample does not enclose empty holes.
- Repair `pinwheel` so its canonical sample is contiguous in the topology neighbor graph.
- Add richer canonical-patch fixtures for substitution families that currently rely mostly on signatures, contiguity checks, and count invariants.
