# TODO

## Done

- Added a standalone-first canvas render-review harness that saves a canvas PNG plus JSON metrics from the real browser render path.
- Added a managed browser-host runner that owns standalone/server startup, readiness, logs, and cleanup for local browser checks.
- Extended the render-review tool with reference-image comparison and named review profiles for repeatable visual diagnosis.
- Unified browser/render failure artifacts so local review and browser-test failures emit the same core bundle shape.
- Documented the browser-diagnosis workflow and added CLI profile discovery so the new tools are usable without reading source.
- Added a repo-scoped process inspection/kill helper for the known browser/server helper processes started from this repo.
- Added a render-review consistency report that cross-checks backend topology facts, browser-state topology facts, and frontend grid-summary output in one JSON report.
- Made managed `run_browser_check.py --render-review` runs default their PNG/JSON outputs into the run artifact directory so repeated reviews do not overwrite the shared `output/render-review/` paths.
- Added an optional `--success-artifacts` bundle for managed `run_browser_check.py --unittest` runs so passing browser checks can preserve `page.png`, `canvas.png`, and `render-summary.json`.
- Added a render-review sweep tool that runs one profile across a small matrix of hosts, themes, or sizes and emits one sweep manifest plus one comparable artifact tree.
- Added profile-owned literature review metadata plus a gitignored local reference-cache workflow so render reviews and sweeps can produce normalized literature montages without storing literature images in git.
- Added render-transform diagnostics to browser-backed render review so summaries and manifests can show topology-space bounds, render-space bounds, and stable sample-cell transforms from the live frontend adapter path.
- Added standalone build provenance and stale-bundle comparison so render-review summaries and manifests can warn when a standalone bundle no longer matches the current checkout.
- Hardened browser render-review settle detection so captures now wait for a stable readiness tuple and record `settleDiagnostics` instead of trusting a momentarily hidden loading overlay.
- Added overlap-hotspot diagnostics plus family-aware overlap policy metadata to render review, managed browser checks, and sweeps so image-derived families like `shield` can report overlap severity instead of only failing a binary fixture test.
- Restored shield's representative render-space no-overlap fixture by separating topology cleanup from draw-only seam hiding: the shipped topology now uses minimal inward trace cleanup, while the canvas path handles seam bridging without mutating geometry cache vertices.
- Added advisory visual-quality metrics to render-review output, managed browser-check manifests, and sweep case records, including visible aspect ratio, edge density, boundary dominance, gutter score, orientation diversity, 12-sector occupancy, and radial-symmetry scoring when the live render diagnostics expose the needed inputs.
- Added a family sample workbench for patch-depth families so candidate representative samples can be compared structurally by count, connectivity, bounds, holes, and diagnostic validation, with optional browser review against injected candidate topology payloads.
- Added a geometry cleanup workbench for image-derived families so shield cleanup scales can be compared by overlap severity, bounds drift, and optional browser-visible gutter risk without ad hoc Shapely sweeps.
- Replaced click-driven palette alias browser tests with a review/test API that injects topology and mutates cell state by `cell.id`, then samples rendered pixels directly from the canvas.
- Moved custom dead-palette ownership and fixture-backed browser alias coverage onto a shared manifest/registry contract so TypeScript and Python no longer maintain separate family allowlists for this test surface.
- Added a frontend representative fixture manifest plus regeneration tool so browser-facing topology fixtures can be checked and refreshed deterministically instead of relying on ad hoc manual export steps.

## Now

- Revisit browser-visible shape and pattern correctness for `dodecagonal-square-triangle` and `pinwheel`; the stronger automated gates are useful, but manual visual review still does not justify promotion out of `Experimental`.
- Run an explicit manual visible-review decision for `shield` against the cached literature reference; the current dense-field approximation is now visually close enough to revisit review, but it remains `Experimental` until that decision is recorded.
- For `pinwheel`, treat the remaining visual mismatch as a display-sampling problem; keep the two-root exact-affine runtime patch, and if we revisit the presentation use a display-only observation window rather than runtime subset selection.
- Replace the current literature-derived dense shield field with a defensible full marked fractal substitution if an explicit rule table becomes available or can be reconstructed to a standard the repo can defend.
## Next

- Add an optional one-command diff review on top of the existing montage/sweep outputs once there is a concrete consumer for it.
- Add profile-attached expectations beyond simple review notes, such as family-specific visual checkpoints, expected warning suppressions, and short literature-review acceptance checklists where those expectations can be stated clearly.
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
