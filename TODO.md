# TODO

## Now

- Decide whether periodic verification should add larger canonical samples beyond the current open-boundary `3x3` boards.
- Add stronger canonical-patch fixtures for substitution families that still rely mainly on low-depth counts, metadata, adjacency vocabularies, and signatures.

## Next

- Extend periodic dual-family verification beyond the currently unambiguous reciprocal catalog pairs.
- Add larger periodic sample fixtures where the open-boundary `3x3` board is too small to expose structural regressions.
- Promote stronger substitution-level reference fixtures for Hat, Shield, Pinwheel, Square-Triangle, and the multiscale Chair family now that the current canonical samples are green again.
- Strengthen the exact-affine/render-space overlap checks so the frontend helper can use tighter epsilons for exact-path families like `pinwheel`.
- Decide whether graph contiguity should eventually move into `recommended_validation_options(...)` for the currently relaxed aperiodic families once their generators are repaired.
- If we revisit `square-triangle`, add marked-prototile and substitution-structure checks beyond the current cleaned dense depth-3 canonical sample.

## Later

- Add `turtle-monotile` on top of the existing Hat-family support.
- Add another verified substitution tiling family such as `socolar-12-fold`.
- Add Shield decoration rendering once decoration metadata is ready to affect visuals.
- Revisit `pinwheel` verification with stronger substitution-matrix and local-patch invariants, now that its contiguity is derived from exact segment-overlap neighbors on the exact-affine path.
- Add a richer “reference data” fixture layer so literature-faithfulness checks can compare canonical low-depth patches directly instead of relying mainly on counts/signatures.

## Maybe

- Add literature verification for browser-visible rendering bounds so obviously collapsed but topologically valid patches are caught earlier.
- Expose a lightweight developer-facing report that summarizes which tilings are verified by geometric sanity only, sample-level literature invariants, or stronger substitution-level reference checks.
