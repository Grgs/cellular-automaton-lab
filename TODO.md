# TODO

## Now

- Commit the full-catalog literature verification expansion once the current backend/docs/tooling changes are reviewed.
- Decide whether `py -3 tools/verify_reference_tilings.py` should become its own required CI check instead of only being covered indirectly by tests.

## Next

- Strengthen periodic-family literature verification beyond `3x3` sample signatures.
  Use more explicit source-backed invariants such as vertex configurations, dual-family relationships, and descriptor-level face-template expectations so periodic mixed tilings are not only protected by sample drift checks.
- Replace broad fallback sources for periodic tilings with stronger references where possible.
  The newer periodic spec entries are currently good enough for verification, but several still rely on generic uniform-tiling references instead of the strongest family-specific sources.
- Add verification coverage for descriptor semantics, not just generated output.
  Extend the literature verifier to assert stable unit-cell slot vocabularies, translation behavior, and row-offset assumptions for periodic-face tilings.

## Later

- Add `turtle-monotile` on top of the existing Hat-family support.
- Add another verified substitution tiling family such as `socolar-12-fold` or `shield` decoration rendering once decoration metadata is ready to affect visuals.
- Revisit `pinwheel` verification with stronger substitution-matrix and local-patch invariants, not only orientation-diversity and exact-affine adjacency checks.
- Add a richer “reference data” fixture layer so literature-faithfulness checks can compare canonical low-depth patches directly instead of relying mainly on counts/signatures.

## Maybe

- Add literature verification for browser-visible rendering bounds so obviously collapsed but topologically valid patches are caught earlier.
- Expose a lightweight developer-facing report that summarizes which tilings are verified by geometric sanity only, sample-level literature invariants, or stronger substitution-level reference checks.
