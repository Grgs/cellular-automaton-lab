# Tiling Known Deviations

This file tracks known mismatches between the current app implementation and the strongest literature-faithful target we eventually want.

## Current Blocking Deviations

None.

## Current Known Deviations

- `dodecagonal-square-triangle` runs a decorated 3.12.12 Archimedean generator (each regular dodecagonal supercell decomposed into six unit squares plus twelve unit equilateral triangles, plus two bridging triangles per supercell). It tiles the plane exactly, has no depth cap, and uses no vendored data, but it is not the canonical Schlottmann quasi-periodic square-triangle tiling: the supercell layout is locally 6-fold symmetric and the global tiling is periodic at the supercell scale.
- `pinwheel` still fails manual visible review even though it now passes stronger backend, canonical-patch, and browser-visible automated checks. It remains in `Experimental` until the rendered pattern looks correct enough to justify promotion.

## Known Limits That Are Not Currently Treated As Failures

- `penrose-p3-rhombs` and `penrose-p3-rhombs-vertex` are built by the de Bruijn pentagrid construction in `backend/simulation/penrose.py` rather than by iterating the canonical Robinson half-tile substitution from a seed. The pentagrid is mathematically equivalent to the canonical Penrose rhomb substitution and produces valid thick / thin rhombs with correct matching at every depth, so the families are flagged as `canonical_patch` rather than `known_deviation`. The trade-off is that the depth-to-cell-count sequence (5/10/24/66 at depths 0..3) is governed by the bounding-box crop at half-extent `0.85 * phi^d` rather than by the substitution eigenvalue; the analogous half-tile rewrite (acutes at short edges into thin rhombs, obtuses at long edges into thick rhombs) was attempted but does not converge to a clean rhomb tiling at depth >= 2 from any rhomb-star or sun seed examined so far. See `docs/PENROSE_CANONICAL_SUBSTITUTION_PLAN.md` for the original investigation.
- Periodic mixed families are still verified on finite open-boundary canonical samples rather than larger-sample or quotient-surface proofs. The reference layer now supports per-family periodic sample sizes, but the current audit kept the shipped catalog on `3x3`.
- Periodic dual-family invariants now cover the unambiguous reciprocal pairs plus candidate-class signature checks for the currently ambiguous catalog groups, but they are still finite-sample descriptor checks rather than full dual-construction proofs.
- The reference layer now mixes rooted local-reference anchors with direct canonical patch diffs for `robinson-triangles`, `tuebingen-triangle`, `dodecagonal-square-triangle`, `shield`, and `pinwheel`; it is not yet full canonical patch coverage for every family.
- Several aperiodic families are verified through deterministic low-depth samples, count invariants, adjacency rules, and metadata presence rather than a full symbolic substitution proof.
- Render-space overlap checks still need a looser tolerance than the backend topology-space overlap check; the current frontend helper uses a `1e-4` positive-area threshold plus multi-precision snapped comparison because exact-path families like `pinwheel` are still noisier in adapter space.
- Pinwheel contiguity now uses exact positive-length segment-overlap neighbors on the exact-affine path because the substitution is not edge-to-edge at every subdivision step.

## When To Add An Entry Here

Add a known deviation when:

- the generator is intentionally approximate
- the literature verifier is knowingly weaker than the intended family model
- a family is temporarily kept on a waiver list
- rendering is accepted as a stopgap even though the mathematical generator is not yet canonical

Do not add an entry just because a family uses a finite sample. Finite samples are part of the app’s model and only count as a deviation if they fail to preserve the intended invariants.
