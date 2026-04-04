# TODO

## Now

- Extend periodic dual-family verification beyond the currently unambiguous reciprocal catalog pairs.
- Expand the local reference-data layer from rooted neighborhood fixtures into direct canonical patch comparisons where that buys materially stronger guarantees.
- Re-verify browser-visible pattern correctness for the experimental `square-triangle`, `shield`, and `pinwheel` families before moving them out of the picker's `Experimental` group.

## Next

- Broaden browser-visible rendering-bounds verification beyond the current representative fixture set.
- Tighten the frontend representative polygon-overlap path enough to add `robinson-triangles` and `tuebingen-triangle` cleanly; Robinson still reuses cell ids in its split patch payload, and Tuebingen still produces small adapter-space slivers at the current overlap epsilon.
- Improve the adapter-space overlap helper enough to lower the frontend positive-area overlap epsilon below the current `2e-4` without regressing known-good exact-path families such as `pinwheel`.
- Extend the developer-facing verification-strength report with per-family detail or CI artifact output once the current summary format settles.
- If we revisit `square-triangle`, add marked-prototile and substitution-structure checks beyond the current cleaned dense depth-3 canonical sample and rooted local-reference anchors.

## Later

- Add `turtle-monotile` on top of the existing Hat-family support.
- Add another verified substitution tiling family such as `socolar-12-fold`.
- Revisit `pinwheel` verification with stronger substitution-matrix and direct local-patch invariants, now that its contiguity is derived from exact segment-overlap neighbors on the exact-affine path.
- Explore larger-sample or quotient-surface periodic proofs if the current finite-sample verifier ever stops being discriminating enough for the catalog.
- Extend Shield decoration rendering beyond the current dead-state accenting if decoration metadata becomes authoritative across more visual states.

## Maybe

- Add full canonical patch-diff workflows on top of the current local-reference fixture layer.
- Extend browser-visible rendering-bounds verification from geometry-level sanity into richer layout regression checks.
