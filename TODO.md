# TODO

## Now

- Revisit browser-visible shape and pattern correctness for `square-triangle`, `shield`, and `pinwheel`; the stronger automated gates are useful, but manual visual review still does not justify promotion out of `Experimental`.
- Replace the current literature-derived dense shield field with a defensible full marked fractal substitution if an explicit rule table becomes available or can be reconstructed to a standard the repo can defend.
- Broaden browser-visible rendering-bounds verification beyond the current representative fixture set.
- Tighten the frontend representative polygon-overlap path enough to add `robinson-triangles` and `tuebingen-triangle` cleanly; Robinson still reuses cell ids in its split patch payload, and Tuebingen still produces small adapter-space slivers at the current overlap epsilon.
- Improve the adapter-space overlap helper enough to lower the frontend positive-area overlap epsilon below the current `2e-4` without regressing known-good exact-path families such as `pinwheel`.

## Next

- Add a fixture-regeneration command for canonical and local reference patch fixtures.
- Continue reducing `frontend/interactions/gesture-sessions.ts` by moving individual gesture implementations into per-session files.
- Extend frontend/backend contract drift protection beyond domain payload fields into controller and standalone-worker command payloads.
- Extend the developer-facing verification-strength report with per-family detail or CI artifact output once the current summary format settles.
- Extend direct canonical patch comparisons beyond `square-triangle`, `shield`, and `pinwheel` where they buy materially stronger guarantees.
- If we revisit `square-triangle`, add marked-prototile and substitution-structure checks beyond the current cleaned dense depth-3 canonical sample, rooted local-reference anchors, and exact public canonical patch fixture.

## Later

- Add `turtle-monotile` on top of the existing Hat-family support.
- Add another verified substitution tiling family such as `socolar-12-fold`.
- Revisit `pinwheel` verification with stronger substitution-matrix and direct local-patch invariants, now that its contiguity is derived from exact segment-overlap neighbors on the exact-affine path.
- Explore larger-sample or quotient-surface periodic proofs if the current finite-sample verifier ever stops being discriminating enough for the catalog.
- Extend Shield decoration rendering beyond the current dead-state accenting if decoration metadata becomes authoritative across more visual states.

## Maybe

- Extend browser-visible rendering-bounds verification from geometry-level sanity into richer layout regression checks.
