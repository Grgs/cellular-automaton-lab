# TODO

Active work. Completed work lives in [CHANGELOG.md](CHANGELOG.md).

## Public Release Triage

### Release blockers

- Do not cut the `v0.1.0` public preview from the current dirty `main` checkout. Resolve or explicitly exclude in-flight changes first, then cut a dedicated release branch from the intended release commit.
- Keep `pinwheel` in `Experimental` for the public preview until manual visible review justifies promotion.

### Acceptable known limitations for `v0.1.0`

- `dodecagonal-square-triangle` is acceptable for the first public preview as a documented decorated `3.12.12` Archimedean generator, not a canonical Schlottmann quasi-periodic marked-prototile implementation.
- The standalone public demo may continue loading Pyodide from a CDN for `v0.1.0`; full offline bundling is post-preview work.
- Current finite-sample verifier boundaries and exact-path render tolerances are acceptable for `v0.1.0` as long as the existing known-deviation docs stay explicit.

### Post-release follow-up

- Add a manual post-deploy GitHub Pages smoke check routine to the release workflow if the preview release cadence becomes regular.
- Revisit whether the verification-strength JSON report should become a CI artifact once there is a concrete consumer for it.

## Now

- Revisit browser-visible shape and pattern correctness for `pinwheel`; the stronger automated gates are useful, but manual visual review still does not justify promotion out of `Experimental`.
- For `dodecagonal-square-triangle`, the runtime is now a decorated 3.12.12 Archimedean generator: hexagonal lattice of regular dodecagonal supercells decomposed into six unit squares plus twelve unit equilateral triangles, with two bridging triangles per supercell. It tiles the plane exactly, scales without depth limit, and uses no vendored data. It is not the canonical Schlottmann quasi-periodic tiling (which would require marked prototiles); the supercell layout is locally 6-fold symmetric and the global tiling is periodic at the supercell scale.
- For a fresh visual-review pass, rebuild `frontend` and `standalone` artifacts on the current HEAD before trusting standalone provenance or comparing newly generated render-review bundles.
- For `pinwheel`, treat the remaining visual mismatch as a display-sampling problem; keep the two-root exact-affine runtime patch, and if we revisit the presentation use a display-only observation window rather than runtime subset selection.

## Next

- Continue the code-quality roadmap by splitting the remaining drawer sections into section-owned builders if cell-metadata and editor controls grow again.
- The direct canonical fixture layer now covers shallow and representative depths for `robinson-triangles`, `tuebingen-triangle`, `dodecagonal-square-triangle`, `shield`, and `pinwheel`, plus depth-`3` fixtures for `spectre`, `sphinx`, and `taylor-socolar`; keep `chair` and `hat-monotile` out of scope unless there is a concrete need for more exactness than their current metadata/local-reference coverage provides.
- If a faithful canonical Schlottmann marked-prototile substitution becomes available (e.g. via Hermisson, Richard, Baake 1997 or an open-source reference implementation), swap the decorated-3.12.12 runtime for it. The current generator is structurally correct as a square-triangle tiling but is periodic, not quasi-periodic.
- Decide whether the stronger verification-strength JSON report should be published as a CI artifact once consumers for it are clear.

## Later

- Add `turtle-monotile` on top of the existing Hat-family support.
- Add another verified substitution tiling family such as `socolar-12-fold`.
- Revisit `pinwheel` verification with stronger substitution-matrix and direct local-patch invariants, now that its contiguity is derived from exact segment-overlap neighbors on the exact-affine path.
- Explore larger-sample or quotient-surface periodic proofs if the current finite-sample verifier ever stops being discriminating enough for the catalog.
- Extend Shield decoration rendering beyond the current dead-state accenting if decoration metadata becomes authoritative across more visual states.

## Maybe

- Extend browser-visible rendering-bounds verification from geometry-level sanity into richer layout regression checks.
- Revisit polygon/regular geometry sharing only if square, hex, and triangle adapters start duplicating overlay or hit-test policy; keep their local math unless a shared path is clearly simpler.

## Remaining After This Cleanup

- Expand Python lint/format guardrails beyond the current tooling + verification slice once the older compatibility-heavy simulation and legacy test modules stop depending on import-for-export and `sys.path` bootstrap patterns.
- Decide whether the lightweight frontend formatting check should grow into a full linter/formatter after a deliberate repo-wide mechanical style pass.
- Extend canonical type-surface drift checks beyond the current controller-view/editor/controller-sync-session/actions slice only if more frontend barrels start restating payload shapes instead of reusing canonical request and domain types.
- Revisit Playwright runner/build coordination only if new host types or non-standalone artifact builds need their own freshness checks; keep suite selection and standalone build reuse centralized in the npm runner path.
- Remove or simplify the remaining compatibility-only shield workbench knobs (`representative-window`, `trace-cleanup-scale`) once no one needs artifact continuity with the old image-derived workflow.
- Continue the code-quality roadmap by splitting the remaining drawer sections if editor controls and topology metadata keep growing together.
- Revisit the interaction router only if idle click/context-menu behavior grows new gesture modes; pointer-session start/update/cancel/commit flow should stay in the session modules.
- Revisit drawer composition only if new UI sections appear; section-local field growth should stay in the section builders, not return to one broad `drawer.ts`.
