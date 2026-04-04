# Tiling Known Deviations

This file tracks known mismatches between the current app implementation and the strongest literature-faithful target we eventually want.

## Current Blocking Deviations

None.

## Current Known Deviations

- `chair`, `square-triangle`, `shield`, and `pinwheel` remain available in the codebase and verification suite, but are exposed under the picker's `Experimental` group until browser-visible pattern correctness is re-verified.

## Known Limits That Are Not Currently Treated As Failures

- Periodic mixed families are still verified on finite open-boundary canonical samples rather than larger-sample or quotient-surface proofs.
- Reciprocal dual-family invariants currently cover only the periodic pairs whose dual matches are unambiguous in the current catalog.
- Several aperiodic families are verified through deterministic low-depth samples, count invariants, adjacency rules, and metadata presence rather than a full symbolic substitution proof.
- Shield decorations are verified as metadata only; they are not rendered.
- Pinwheel contiguity now uses exact positive-length segment-overlap neighbors on the exact-affine path because the substitution is not edge-to-edge at every subdivision step.

## When To Add An Entry Here

Add a known deviation when:

- the generator is intentionally approximate
- the literature verifier is knowingly weaker than the intended family model
- a family is temporarily kept on a waiver list
- rendering is accepted as a stopgap even though the mathematical generator is not yet canonical

Do not add an entry just because a family uses a finite sample. Finite samples are part of the app’s model and only count as a deviation if they fail to preserve the intended invariants.
