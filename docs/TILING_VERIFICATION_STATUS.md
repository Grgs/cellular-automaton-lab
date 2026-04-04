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
| Newer substitution aperiodic | `spectre`, `taylor-socolar`, `sphinx` | PASS | PASS | Mixed | Stronger than render checks, but still mostly based on low-depth counts, metadata, adjacency, signatures, and contiguity checks rather than full substitution-matrix proofs. Global overlap validation is strict, and the representative render-space overlap fixtures are clean. |
| Newer substitution aperiodic | `robinson-triangles`, `tuebingen-triangle` | PASS | PASS | Mixed, metadata + browser-visible render check | Verified by low-depth counts, metadata, adjacency, deterministic signatures, contiguity checks, representative render-bounds fixtures, and browser-visible Playwright gates that wait for the final settled patch and require strong canvas occupancy plus multiple dead-state fill colors. |
| Newer substitution aperiodic | `chair` | PASS | PASS | Mixed, metadata + local-reference + browser-visible render check | Verified as a true chair substitution through exact depth totals, orientation-token metadata, rooted local-reference fixtures, strict validation, render-bounds coverage, and a browser-visible Playwright check that the patch fills the viewport sensibly and exposes the four orientation-based dead-state colors. |
| Newer substitution aperiodic | `hat-monotile` | PASS | PASS | Mixed, local-reference + browser-visible render check | Hat is connected, overlap-clean, and hole-free under the canonical sample checks, preserves the reflected-neighbor chirality pattern used by the literature verifier, matches a checked-in rooted local-reference fixture, and now also has a browser-visible Playwright gate for settled multi-fill occupancy. |
| Experimental aperiodic | `shield` | PASS | PASS | Mixed, decoration-aware local-reference | Kept in the `Experimental` picker group while browser-visible pattern correctness is re-verified; automated checks now cover connectivity, hole freedom, decoration-token diversity, and rooted decorated local-reference fixtures. |
| Experimental aperiodic | `square-triangle` | PASS | PASS | Mixed, depth-3 canonical + local-reference | Kept in the `Experimental` picker group while browser-visible pattern correctness is re-verified; automated checks now cover the cleaned dense depth-3 canonical sample, kind counts, metadata diversity, signature, and rooted local-reference fixtures. |
| Experimental aperiodic | `pinwheel` | PASS | PASS | Mixed, exact-path + local-reference | Kept in the `Experimental` picker group while browser-visible pattern correctness is re-verified; automated checks now cover the exact-affine neighbor path, orientation diversity, expanding support, and a rooted exact-path local-reference fixture. |
| Periodic mixed / periodic-face | `archimedean-4-8-8`, `archimedean-3-12-12`, `archimedean-3-4-6-4`, `archimedean-4-6-12`, `archimedean-3-3-4-3-4`, `archimedean-3-3-3-4-4`, `archimedean-3-3-3-3-6`, `trihexagonal-3-6-3-6`, `cairo-pentagonal`, `rhombille`, `deltoidal-hexagonal`, `tetrakis-square`, `triakis-triangular`, `deltoidal-trihexagonal`, `prismatic-pentagonal`, `floret-pentagonal`, `snub-square-dual` | PASS | PASS | Sample-level exact + descriptor semantics + interior vertex stars/frequencies + selected dual checks | Verified on family-specific canonical periodic samples defined in the reference specs. The current audit across `3x3`, `4x4`, and `5x5` kept every shipped periodic family on `3x3`, while still adding explicit sample-size override support, exact interior vertex-configuration sets, exact interior vertex-configuration frequencies, and reciprocal dual-structure checks for the unambiguous periodic pairs already present in the catalog. |

## Next Up

- Extend reciprocal dual-family verification beyond the currently unambiguous periodic pairs.
- Grow the new rooted local-reference layer into broader direct canonical patch comparisons where that adds real discrimination.
- Broaden browser-visible rendering-bounds checks and re-verify the remaining experimental families visually before promoting them out of the picker's `Experimental` group.
- Add new verified tilings such as `turtle-monotile` and another substitution family like `socolar-12-fold`.
