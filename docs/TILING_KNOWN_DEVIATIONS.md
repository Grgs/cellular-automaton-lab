# Tiling Known Deviations

This file tracks known mismatches between the current app implementation and the strongest literature-faithful target we eventually want.

## Current Blocking Deviations

None.

## Current Known Deviations

- `dodecagonal-square-triangle` runs a decorated 3.12.12 Archimedean generator (each regular dodecagonal supercell decomposed into six unit squares plus twelve unit equilateral triangles, plus two bridging triangles per supercell). It tiles the plane exactly, has no depth cap, and uses no vendored data, but it is not the canonical Schlottmann quasi-periodic square-triangle tiling: the supercell layout is locally 6-fold symmetric and the global tiling is periodic at the supercell scale.
- `pinwheel` still fails manual visible review even though it now passes stronger backend, canonical-patch, and browser-visible automated checks. It remains in `Experimental` until the rendered pattern looks correct enough to justify promotion.
- `penrose-p2-kite-dart`, `penrose-p3-rhombs`, `penrose-p3-rhombs-vertex`, and `robinson-triangles` use a non-canonical full-tile substitution rule rather than the canonical Conway/de Bruijn deflation cited at [tilings.math.uni-bielefeld.de](https://tilings.math.uni-bielefeld.de/). The output tiles have correct Penrose shapes and the patches are overlap-free, but the depth-to-cell-count growth does not match the canonical phi^2 eigenvalue. P2 grows as `[[2,1],[2,2]]` (eigenvalue `2+sqrt(2)` ≈ 3.414, depth-3 = 240 kites/darts vs canonical 105). Robinson Triangles is derived by splitting P2 cells and inherits the same off-canon growth (depth-3 = 480 vs canonical 210). P3 has its own non-canonical rule (depth-3 = 66). The reason all three diverge in the same direction: the codebase emits only full kites/darts/rhombs (no partial tiles), but the canonical Penrose substitution starting from a sun seed produces unpaired half-acute boundary tiles at every step. The in-house rules sidestep that boundary issue at the cost of the canonical eigenvalue. Tracked for fix in [PENROSE_CANONICAL_SUBSTITUTION_PLAN.md](PENROSE_CANONICAL_SUBSTITUTION_PLAN.md).

## Known Limits That Are Not Currently Treated As Failures

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
