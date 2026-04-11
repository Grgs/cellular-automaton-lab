# TODO

## Now

- Revisit browser-visible shape and pattern correctness for `square-triangle`, `shield`, and `pinwheel`; the stronger automated gates are useful, but manual visual review still does not justify promotion out of `Experimental`.
- Replace the current literature-derived dense shield field with a defensible full marked fractal substitution if an explicit rule table becomes available or can be reconstructed to a standard the repo can defend.
- Broaden browser-visible rendering-bounds verification beyond the current representative fixture set.

## Next

- Continue the code-quality roadmap by splitting the remaining drawer sections into section-owned builders if cell-metadata and editor controls grow again.
- Broaden direct canonical patch comparisons beyond the current exact-depth set (`square-triangle`, `shield`, `pinwheel`, `robinson-triangles`, and `tuebingen-triangle`) where they buy materially stronger guarantees.
- If we revisit `square-triangle`, add marked-prototile and substitution-structure checks beyond the current cleaned dense depth-3 canonical sample, rooted local-reference anchors, and exact public canonical patch fixture.
- Decide whether the stronger verification-strength JSON report should be published as a CI artifact once consumers for it are clear.

## Later

- Add `turtle-monotile` on top of the existing Hat-family support.
- Add another verified substitution tiling family such as `socolar-12-fold`.
- Revisit `pinwheel` verification with stronger substitution-matrix and direct local-patch invariants, now that its contiguity is derived from exact segment-overlap neighbors on the exact-affine path.
- Explore larger-sample or quotient-surface periodic proofs if the current finite-sample verifier ever stops being discriminating enough for the catalog.
- Extend Shield decoration rendering beyond the current dead-state accenting if decoration metadata becomes authoritative across more visual states.

## Maybe

- Extend browser-visible rendering-bounds verification from geometry-level sanity into richer layout regression checks.
