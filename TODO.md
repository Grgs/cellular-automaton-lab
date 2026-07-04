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

## Comparison wall (wall-first UI) — done

The compare-as-a-first-class-workspace feature shipped and then became the app's
landing experience via the wall-first overhaul (targets `v0.6.0`; see
[CHANGELOG.md](CHANGELOG.md)). Delivered: the synchronized side-by-side engine
and live N-board view; the stage-first workspace with a docked transport on one
shared clock; gallery ↔ speaker view with a deep-linkable `&focus=` slot; the
wall as the bare-URL landing with a first-visit autoplaying demo; the editor as
the routed `#/lab`; a speaker-view seed rail; per-board live forking into an
independent editable pane (reusable `frontend/pane/` primitive); and the
retirement of the two-editable-pane Split View.

Decisions that held throughout:

- **Persistence is client-side** (`localStorage`), namespaced. Server and
  standalone Pyodide builds stay symmetric; cross-device transfer is run links.
- **Run links reconstruct-and-wait**: a run link populates the wall and selects
  tilings but does not auto-run or auto-play, to avoid surprise cold-load compute.
- **Navigation is wall-first**: bare URL → wall, `#share=` → Lab (`#/lab`); the
  legacy `#/compare` stays parsed forever as an alias for the wall.
- **Standalone parity**: hash/`localStorage` only; the live focus pane forks into
  its own persist-free Pyodide environment (no server sessions in standalone).

Possible follow-ups (not scheduled): allow more than one live fork at a time; a
history-gated demo prominence; true code-split of the analytics charts.

## Now

- For `dodecagonal-square-triangle` (catalog label "Schlottmann Square-Triangle"), the runtime is now the genuine Schlottmann quasi-periodic square-triangle pseudo substitution (inflation `2 + sqrt(3)`, five marked prototiles, interlocking supertiles deduplicated in the exact `Z[zeta12]` module). The rule was extracted from the Tilings Encyclopedia figure and verified tile-for-tile against the encyclopedia's 4999-cell literature patch. It scales without depth limit and uses no vendored data. Manual visual review accepted the rendered field on July 2, 2026 and the family was promoted to the main `Aperiodic` group, leaving the Experimental group empty.
- For a fresh visual-review pass, rebuild `frontend` and `standalone` artifacts on the current HEAD before trusting standalone provenance or comparing newly generated render-review bundles.

## Next

- Continue the code-quality roadmap by splitting the remaining drawer sections into section-owned builders if cell-metadata and editor controls grow again.
- The direct canonical fixture layer now covers shallow and representative depths for `robinson-triangles`, `tuebingen-triangle`, `dodecagonal-square-triangle`, `shield`, and `pinwheel`, plus depth-`3` fixtures for `spectre`, `sphinx`, and `taylor-socolar`; keep `chair` and `hat-monotile` out of scope unless there is a concrete need for more exactness than their current metadata/local-reference coverage provides.
- Decide whether the stronger verification-strength JSON report should be published as a CI artifact once consumers for it are clear.

## Later

- `socolar-12-fold` now ships as the dodecagonal rhomb tiling via the de Bruijn multigrid (MLD to `shield`). If the exact Socolar (1989) marked substitution rule becomes available in a portable form, add it as the literal substitution; the current entry is a `canonical_patch` multigrid crop, not the marked-prototile substitution. See [docs/TILING_KNOWN_DEVIATIONS.md](docs/TILING_KNOWN_DEVIATIONS.md).
- Revisit `pinwheel` verification with stronger substitution-matrix and direct local-patch invariants, now that its contiguity is derived from exact segment-overlap neighbors on the exact-affine path.
- Explore larger-sample or quotient-surface periodic proofs if the current finite-sample verifier ever stops being discriminating enough for the catalog.
- Extend Shield decoration rendering beyond the current dead-state accenting if decoration metadata becomes authoritative across more visual states.

## Maybe

- ~~Replace the floating compare toggle with explicit Build/Compare header tabs~~ — superseded by the wall-first overhaul: the wall is the landing view, the Lab is `#/lab`, and the floating toggle is removed.
- Extend browser-visible rendering-bounds verification from geometry-level sanity into richer layout regression checks.
- Revisit polygon/regular geometry sharing only if square, hex, and triangle adapters start duplicating overlay or hit-test policy; keep their local math unless a shared path is clearly simpler.

## Remaining After This Cleanup

- Extend canonical type-surface drift checks beyond the current controller-view/editor/controller-sync-session/actions slice only if more frontend barrels start restating payload shapes instead of reusing canonical request and domain types.
- Revisit Playwright runner/build coordination only if new host types or non-standalone artifact builds need their own freshness checks; keep suite selection and standalone build reuse centralized in the npm runner path.
- Remove or simplify the remaining compatibility-only shield workbench knobs (`representative-window`, `trace-cleanup-scale`) once no one needs artifact continuity with the old image-derived workflow.
- Continue the code-quality roadmap by splitting the remaining drawer sections if editor controls and topology metadata keep growing together.
- Revisit the interaction router only if idle click/context-menu behavior grows new gesture modes; pointer-session start/update/cancel/commit flow should stay in the session modules.
- Revisit drawer composition only if new UI sections appear; section-local field growth should stay in the section builders, not return to one broad `drawer.ts`.
