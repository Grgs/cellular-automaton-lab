# Tiling Known Deviations

This file tracks known mismatches between the current app implementation and the strongest literature-faithful target we eventually want.

## Current Blocking Deviations

None.

## Current Known Deviations

- `chair`, `square-triangle`, `shield`, and `pinwheel` remain available in the codebase and verification suite, but are exposed under the picker's `Experimental` group until browser-visible pattern correctness is re-verified.

## Known Limits That Are Not Currently Treated As Failures

- Periodic mixed families are still verified on finite open-boundary canonical samples rather than larger-sample or quotient-surface proofs. The reference layer now supports per-family periodic sample sizes, but the current audit kept the shipped catalog on `3x3`.
- Reciprocal dual-family invariants currently cover only the periodic pairs whose dual matches are unambiguous in the current catalog.
- The new local-reference layer compares rooted canonical neighborhoods, not full canonical patch diffs.
- Several aperiodic families are verified through deterministic low-depth samples, count invariants, adjacency rules, and metadata presence rather than a full symbolic substitution proof.
- Render-space overlap checks still need a tolerance of `2e-4` because the adapter-space polygon-clipping path for exact-path families like `pinwheel` is noisier than the backend topology-space overlap check.
- Shield decorations now influence dead-state rendering accents, but that does not yet count as full browser-visible re-approval of the family.
- Pinwheel contiguity now uses exact positive-length segment-overlap neighbors on the exact-affine path because the substitution is not edge-to-edge at every subdivision step.

## When To Add An Entry Here

Add a known deviation when:

- the generator is intentionally approximate
- the literature verifier is knowingly weaker than the intended family model
- a family is temporarily kept on a waiver list
- rendering is accepted as a stopgap even though the mathematical generator is not yet canonical

Do not add an entry just because a family uses a finite sample. Finite samples are part of the app’s model and only count as a deviation if they fail to preserve the intended invariants.
