# TODO

## Done

- Added a standalone-first canvas render-review harness that saves a canvas PNG plus JSON metrics from the real browser render path.
- Added a managed browser-host runner that owns standalone/server startup, readiness, logs, and cleanup for local browser checks.
- Extended the render-review tool with reference-image comparison and named review profiles for repeatable visual diagnosis.
- Unified browser/render failure artifacts so local review and browser-test failures emit the same core bundle shape.
- Documented the browser-diagnosis workflow and added CLI profile discovery so the new tools are usable without reading source.
- Added a repo-scoped process inspection/kill helper for the known browser/server helper processes started from this repo.
- Added a render-review consistency report that cross-checks backend topology facts, browser-state topology facts, and frontend grid-summary output in one JSON report.

## Now

- Revisit browser-visible shape and pattern correctness for `dodecagonal-square-triangle`, `shield`, and `pinwheel`; the stronger automated gates are useful, but manual visual review still does not justify promotion out of `Experimental`.
- For `pinwheel`, treat the remaining visual mismatch as a display-sampling problem; keep the two-root exact-affine runtime patch, and if we revisit the presentation use a display-only observation window rather than runtime subset selection.
- Replace the current literature-derived dense shield field with a defensible full marked fractal substitution if an explicit rule table becomes available or can be reconstructed to a standard the repo can defend.
## Next

- Add an optional success-artifact bundle for managed browser checks, especially targeted `--unittest` runs, so passing diagnosis sessions can still preserve `canvas.png`, `page.png`, and `render-summary.json`.
- Add a review-sweep helper that runs one render-review profile across a small matrix of depths, themes, or host kinds and emits one comparable artifact set.
- Continue the code-quality roadmap by splitting the remaining drawer sections into section-owned builders if cell-metadata and editor controls grow again.
- The current exact-depth canonical set now also covers `spectre`, `sphinx`, and `taylor-socolar`; keep `chair` and `hat-monotile` out of scope unless there is a concrete need for more exactness than their current metadata/local-reference coverage provides.
- If we revisit `dodecagonal-square-triangle`, add marked-prototile and substitution-structure checks beyond the current cleaned dense depth-3 canonical sample, rooted local-reference anchors, and exact public canonical patch fixture.
- Decide whether the stronger verification-strength JSON report should be published as a CI artifact once consumers for it are clear.

## Later

- Add `turtle-monotile` on top of the existing Hat-family support.
- Add another verified substitution tiling family such as `socolar-12-fold`.
- Revisit `pinwheel` verification with stronger substitution-matrix and direct local-patch invariants, now that its contiguity is derived from exact segment-overlap neighbors on the exact-affine path.
- Explore larger-sample or quotient-surface periodic proofs if the current finite-sample verifier ever stops being discriminating enough for the catalog.
- Extend Shield decoration rendering beyond the current dead-state accenting if decoration metadata becomes authoritative across more visual states.

## Maybe

- Extend browser-visible rendering-bounds verification from geometry-level sanity into richer layout regression checks.
