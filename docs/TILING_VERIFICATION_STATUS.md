# Tiling Verification Status

This file tracks the current verification level for every tiling family in the app.

Implementation-status contracts for aperiodic families live in `backend/simulation/aperiodic_contracts.py`. The developer-facing strength report includes those statuses beside verification coverage, so promotion decisions can distinguish true substitutions, exact-affine paths, canonical patches, and known deviations.

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
| Newer substitution aperiodic | `square-triangle` | PASS | PASS | Mixed, canonical-patch + local-reference + browser-visible render check | Verified on the cleaned dense depth-3 canonical sample with exact counts, metadata diversity, signature, rooted local-reference anchors, an exact canonical patch fixture, representative render-bounds coverage, and a settled-render Playwright gate. It remains in `Experimental` because manual visible review still does not justify promotion. |
| Newer substitution aperiodic | `shield` | PASS | PASS | Mixed, literature-derived dense field + canonical-patch + local-reference + browser-visible render check | Verified against a dense 12-fold canonical field extracted from the literature patch image, with orientation metadata, rooted local-reference anchors, an exact dense depth-3 canonical patch fixture, representative render-bounds coverage, and a settled-render Playwright gate. It remains in `Experimental` pending manual visual review, and it does not currently claim a full marked fractal substitution proof. |
| Newer substitution aperiodic | `pinwheel` | PASS | PASS | Mixed, exact-path + canonical-patch + local-reference + browser-visible render check | Verified on the exact-affine path with orientation diversity, expanding support, rooted local-reference anchors, an exact canonical depth-3 patch fixture including ids, representative render-bounds coverage, and a settled-render Playwright gate. It remains in `Experimental` because manual visible review still does not justify promotion. |
| Periodic mixed / periodic-face | `archimedean-4-8-8`, `archimedean-3-12-12`, `archimedean-3-4-6-4`, `archimedean-4-6-12`, `archimedean-3-3-4-3-4`, `archimedean-3-3-3-4-4`, `archimedean-3-3-3-3-6`, `trihexagonal-3-6-3-6`, `cairo-pentagonal`, `rhombille`, `deltoidal-hexagonal`, `tetrakis-square`, `triakis-triangular`, `deltoidal-trihexagonal`, `prismatic-pentagonal`, `floret-pentagonal`, `snub-square-dual` | PASS | PASS | Sample-level exact + descriptor semantics + interior vertex stars/frequencies + dual checks | Verified on family-specific canonical periodic samples defined in the reference specs. The current audit across `3x3`, `4x4`, and `5x5` kept every shipped periodic family on `3x3`, while still adding explicit sample-size override support, exact interior vertex-configuration sets, exact interior vertex-configuration frequencies, reciprocal dual-structure checks for unambiguous pairs, and candidate-class dual-signature checks where the current catalog is structurally ambiguous. |

## Next Up

- Broaden browser-visible rendering-bounds checks beyond the current representative fixture set.
- Extend direct canonical patch comparisons beyond `square-triangle`, `shield`, and `pinwheel` where the extra exactness buys materially stronger guarantees.
- Tighten the frontend representative polygon-overlap path enough to add `robinson-triangles` and `tuebingen-triangle` cleanly without relaxing the current overlap threshold.
- Revisit manual visible correctness for `square-triangle`, `shield`, and `pinwheel`; automated gates are stronger now, but the current rendered patterns still do not justify promotion out of `Experimental`.
- Replace the current literature-derived dense shield field with a defensible fully marked fractal substitution only if an explicit rule table is available or reconstructed to a standard the repo can defend.
- Add new verified tilings such as `turtle-monotile` and another substitution family like `socolar-12-fold`.
