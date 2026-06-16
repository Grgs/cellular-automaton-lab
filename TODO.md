# TODO

Active work. Completed work lives in [CHANGELOG.md](CHANGELOG.md).

## Public Release Follow-up

The `v0.4.0` public preview has been released (after `v0.1.0`, `v0.2.0`, and `v0.3.0`). Keep this section for follow-up work that affects future preview releases or the published standalone demo.

### Current preview limitations

- Keep `dodecagonal-square-triangle` documented as a decorated `3.12.12` Archimedean generator, not a canonical Schlottmann quasi-periodic marked-prototile implementation.
- Keep the standalone public demo's Pyodide CDN dependency documented until full offline bundling is implemented.
- Keep finite-sample verifier boundaries and exact-path render tolerances documented in the known-deviation notes until stronger verification replaces them.

### Future release follow-up

- Add an automated post-deploy GitHub Pages smoke check if the preview release cadence becomes regular; the manual smoke routine and pre/post release publication guard now live in [docs/MAINTENANCE.md](docs/MAINTENANCE.md#public-release-process).
- Revisit whether the verification-strength JSON report should become a CI artifact once there is a concrete consumer for it.

## Compare workspace & synchronized side-by-side

Roadmap to "complete" for the compare-as-a-first-class-workspace feature. The
synchronized side-by-side engine, the live N-board view, the panel/modal
decoupling, the `#/compare` hash route, and the full-page workspace presentation
are done (see [CHANGELOG.md](CHANGELOG.md); routing + full-page land via the
open compare PRs). What remains, sequenced, one reviewable PR per step.

Decisions already taken (so the steps are unambiguous):

- **Persistence is client-side** (`localStorage`), namespaced. Keeps the server
  and standalone Pyodide builds symmetric; cross-device transfer is handled by
  run links, not a server store.
- **Run links reconstruct-and-wait**: opening a run link populates the workspace
  and selects the tilings but does not auto-run or auto-play, to avoid surprise
  compute on cold load.
- **Navigation stays the floating toggle + in-workspace "Back to build"**; header
  Build/Compare tabs are deferred (see Maybe) to avoid an app-shell rewrite.
- **Standalone parity is mandatory** for every step: hash/`localStorage` only, no
  server-only state.

### Phase C — persistent & shareable runs

- **C2 — Result → build from the live view.** The static results table already
  opens begin/end in place; the live filmstrip view does not. Add a per-board
  "Open this generation in build" action that turns a tiling's current
  `frames[index]` into a `PatternPayload` and loads it via the existing
  `onOpenPattern` path, returning to `#/build`. Threads an `onOpenPattern`
  callback through `createFilmstripView`.
- **C3 — Persisted named runs (+ custom tiling sets).** Save the current run
  configuration under a name; list / load / rename / delete from the workspace,
  backed by a small `localStorage` store module. Fold custom/pinned tiling sets
  into the same store (a saved named tiling selection that applies alongside the
  built-in Representative/Regular/Mixed/Aperiodic presets). Done when a saved run
  and a saved tiling set both restore losslessly after a full reload.
- **C5 — Workspace nav & layout polish.** Tune the filmstrip board grid to use
  the full-page width (larger boards when there is room); add empty/loading/error
  states for saved runs and the live view; pass a keyboard-focus and `aria`
  review for the full-page workspace.

### Closeout — definition of done

- Docs: a "Compare workspace" section in the user-facing docs/README; document
  the `run=` link format next to the share-link format; CHANGELOG narrative.
- Standalone smoke coverage: exercise C1–C3 in the Pyodide build via the
  Playwright standalone suite so parity is enforced, not assumed.
- The feature is complete when, in **both** the server and standalone builds, you
  can: open `#/compare`, build a side-by-side run, play it synchronized, open a
  frame into build, save the run, reload and restore it, and open a copied run
  link in a fresh tab — with green CI and updated docs.

## Now

- For `dodecagonal-square-triangle`, the runtime is now a decorated 3.12.12 Archimedean generator: hexagonal lattice of regular dodecagonal supercells decomposed into six unit squares plus twelve unit equilateral triangles, with two bridging triangles per supercell. It tiles the plane exactly, scales without depth limit, and uses no vendored data. It is not the canonical Schlottmann quasi-periodic tiling (which would require marked prototiles); the supercell layout is locally 6-fold symmetric and the global tiling is periodic at the supercell scale.
- For a fresh visual-review pass, rebuild `frontend` and `standalone` artifacts on the current HEAD before trusting standalone provenance or comparing newly generated render-review bundles.

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

- Replace the floating compare toggle with explicit Build/Compare header tabs once the compare workspace is established, if the floating entry point feels secondary to its first-class status; deferred from the compare-workspace roadmap to avoid an app-shell rewrite.
- Extend browser-visible rendering-bounds verification from geometry-level sanity into richer layout regression checks.
- Revisit polygon/regular geometry sharing only if square, hex, and triangle adapters start duplicating overlay or hit-test policy; keep their local math unless a shared path is clearly simpler.

## Remaining After This Cleanup

- Extend canonical type-surface drift checks beyond the current controller-view/editor/controller-sync-session/actions slice only if more frontend barrels start restating payload shapes instead of reusing canonical request and domain types.
- Revisit Playwright runner/build coordination only if new host types or non-standalone artifact builds need their own freshness checks; keep suite selection and standalone build reuse centralized in the npm runner path.
- Remove or simplify the remaining compatibility-only shield workbench knobs (`representative-window`, `trace-cleanup-scale`) once no one needs artifact continuity with the old image-derived workflow.
- Continue the code-quality roadmap by splitting the remaining drawer sections if editor controls and topology metadata keep growing together.
- Revisit the interaction router only if idle click/context-menu behavior grows new gesture modes; pointer-session start/update/cancel/commit flow should stay in the session modules.
- Revisit drawer composition only if new UI sections appear; section-local field growth should stay in the section builders, not return to one broad `drawer.ts`.
