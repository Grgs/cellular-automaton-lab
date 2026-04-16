# Tiling Known Deviations

This file tracks known mismatches between the current app implementation and the strongest literature-faithful target we eventually want.

## Current Blocking Deviations

None.

## Current Known Deviations

- `dodecagonal-square-triangle`, `shield`, and `pinwheel` still fail manual visible review even though they now pass stronger backend, canonical-patch, and browser-visible automated checks. They remain in `Experimental` until the rendered patterns look correct enough to justify promotion.
- `shield` now uses a dense literature-derived central field selected through a backend-owned dodecagonal window rather than the old translated-cluster motif, but it is still not a full marked fractal substitution with explicit bond rules. The repo treats that as an approximation gap, not as a blocker for the current canonical-patch verifier.

## Known Limits That Are Not Currently Treated As Failures

- Periodic mixed families are still verified on finite open-boundary canonical samples rather than larger-sample or quotient-surface proofs. The reference layer now supports per-family periodic sample sizes, but the current audit kept the shipped catalog on `3x3`.
- Periodic dual-family invariants now cover the unambiguous reciprocal pairs plus candidate-class signature checks for the currently ambiguous catalog groups, but they are still finite-sample descriptor checks rather than full dual-construction proofs.
- The reference layer now mixes rooted local-reference anchors with direct canonical patch diffs for `dodecagonal-square-triangle`, `shield`, and `pinwheel`; it is not yet full canonical patch coverage for every family.
- `shield` uses relaxed topology validation (`surface` + `graph connectivity`, without strict overlap or edge-multiplicity checks) because the dense image-derived polygons are not exact edge-sharing substitution polygons.
- `shield` also remains outside the strict frontend render-space no-overlap contract because the dense image-derived polygons require backend-owned gap compensation to remove visible gutters, and that compensation is not an exact edge-sharing model.
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
