# Tiling Known Deviations

This file tracks known mismatches between the current app implementation and the strongest literature-faithful target we eventually want.

## Current Blocking Deviations

- `square-triangle`
  Canonical literature verification now blocks because the depth-3 sample is connected but still leaves enclosed empty gaps rather than a hole-free surface.

## Current Known Deviations

None.

## Known Limits That Are Not Currently Treated As Failures

- Some periodic mixed families are verified through exact `3x3` sample signatures and descriptor checks, but not yet through richer family-specific structural proofs such as vertex-configuration or dual-family invariants.
- Some periodic families still rely on broad fallback sources rather than the strongest family-specific references.
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
