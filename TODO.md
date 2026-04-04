# TODO

## Now

- Repair `square-triangle` so its canonical depth-3 sample is hole-free.
- Replace generic fallback periodic sources with stronger family-specific references where possible.
- Decide whether periodic verification should add larger canonical samples beyond the current open-boundary `3x3` boards.
- Add stronger canonical-patch fixtures for substitution families that still rely mainly on low-depth counts, metadata, adjacency vocabularies, and signatures.

## Next

- Strengthen periodic-family literature verification beyond `3x3` sample signatures.
  Use more explicit source-backed invariants such as vertex configurations and dual-family relationships so periodic mixed tilings are not only protected by sample drift checks.
- Add larger periodic sample fixtures where the open-boundary `3x3` board is too small to expose structural regressions.
- Promote stronger substitution-level reference fixtures for Hat, Shield, Pinwheel, and the multiscale Chair family now that Hat, Shield, and Chair pass the staged verifier.
- Strengthen the exact-affine/render-space overlap checks so the frontend helper can use tighter epsilons for exact-path families like `pinwheel`.
- Decide whether graph contiguity should eventually move into `recommended_validation_options(...)` for the currently relaxed aperiodic families once their generators are repaired.

## Later

- Add `turtle-monotile` on top of the existing Hat-family support.
- Add another verified substitution tiling family such as `socolar-12-fold` or `shield` decoration rendering once decoration metadata is ready to affect visuals.
- Revisit `pinwheel` verification with stronger substitution-matrix and local-patch invariants, now that its contiguity is derived from exact segment-overlap neighbors on the exact-affine path.
- Add a richer “reference data” fixture layer so literature-faithfulness checks can compare canonical low-depth patches directly instead of relying mainly on counts/signatures.

## Maybe

- Add literature verification for browser-visible rendering bounds so obviously collapsed but topologically valid patches are caught earlier.
- Expose a lightweight developer-facing report that summarizes which tilings are verified by geometric sanity only, sample-level literature invariants, or stronger substitution-level reference checks.
