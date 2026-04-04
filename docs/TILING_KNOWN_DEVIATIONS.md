# Tiling Known Deviations

This file tracks known mismatches between the current app implementation and the strongest literature-faithful target we eventually want.

## Current Blocking Deviations

None. The current deviations below are staged through the literature-verification waiver list so CI stays green while they are still reported loudly.

## Current Known Deviations

- `hat-monotile`
  - The current builder produces both chiralities, but the reflected hats do not participate in the characteristic opposite-chirality local pattern described by the Hat metatiles source.
  - The literature verifier now expects cross-chirality adjacency and at least one three-neighbor opposite-chirality local pattern in a low-depth representative patch; this currently fails and is waived.
- `chair`
  - The current builder produces a simple rep-4 chair hierarchy with one polygon area class.
  - The literature verifier now expects the Ammann Chair family to expose a multiscale chair hierarchy; this currently fails and is waived.
- `shield`
  - The current builder renders plausible shield/square/triangle patches, but the decoration metadata is too flat.
  - The literature verifier now expects multiple decoration-token variants for the decorated shield family; this currently fails and is waived.
- `pinwheel`
  - The current builder uses the exact-affine path and passes orientation/adjacency checks, but it keeps the support rectangle fixed while only subdividing inside it.
  - The literature verifier now expects the representative patch to expand with depth; this currently fails and is waived.

## Known Limits That Are Not Currently Treated As Failures

- Some periodic mixed families are verified through exact `3x3` sample signatures and descriptor checks, but not yet through richer family-specific structural proofs such as vertex-configuration or dual-family invariants.
- Some periodic families still rely on broad fallback sources rather than the strongest family-specific references.
- Several aperiodic families are verified through deterministic low-depth samples, count invariants, adjacency rules, and metadata presence rather than a full symbolic substitution proof.
- Shield decorations are verified as metadata only; they are not rendered.

## When To Add An Entry Here

Add a known deviation when:

- the generator is intentionally approximate
- the literature verifier is knowingly weaker than the intended family model
- a family is temporarily kept on a waiver list
- rendering is accepted as a stopgap even though the mathematical generator is not yet canonical

Do not add an entry just because a family uses a finite sample. Finite samples are part of the app’s model and only count as a deviation if they fail to preserve the intended invariants.
