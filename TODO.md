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
- Added advisory profile-owned expectations to render review, managed browser-check manifests, sweep case records, and browser-reviewed workbench summaries so named profiles can carry manual checklists plus expected-warning classification without changing command success semantics.
- Moved browser diagnosis and workbench implementation under `tools/render_review/` and reduced the top-level Python commands to thin CLI entrypoints.
- Surfaced backend-owned aperiodic implementation status and promotion blockers in the topology picker and drawer UI.
- Added incremental lint/format guardrails for the render-review/bootstrap slice plus a repo-owned frontend formatting check.
- Tightened the interaction stack around explicit pointer-down intent resolution and session-owned pointer matching/completion, so the router no longer hardcodes per-session pointer-id policy.
- Split the drawer view model into section-owned builders for shell state, inspector/header state, topology/sizing, rule/palette, and pattern controls.

## Now

- Revisit browser-visible shape and pattern correctness for `dodecagonal-square-triangle` and `pinwheel`; the stronger automated gates are useful, but manual visual review still does not justify promotion out of `Experimental`.
- For a fresh visual-review pass, rebuild `frontend` and `standalone` artifacts on the current HEAD before trusting standalone provenance or comparing newly generated render-review bundles.
- For `pinwheel`, treat the remaining visual mismatch as a display-sampling problem; keep the two-root exact-affine runtime patch, and if we revisit the presentation use a display-only observation window rather than runtime subset selection.
## Next

- Add an optional one-command diff review on top of the existing montage/sweep outputs once there is a concrete consumer for it.
- Continue the code-quality roadmap by splitting the remaining drawer sections into section-owned builders if cell-metadata and editor controls grow again.
- The direct canonical fixture layer now covers shallow and representative depths for `robinson-triangles`, `tuebingen-triangle`, `dodecagonal-square-triangle`, `shield`, and `pinwheel`, plus depth-`3` fixtures for `spectre`, `sphinx`, and `taylor-socolar`; keep `chair` and `hat-monotile` out of scope unless there is a concrete need for more exactness than their current metadata/local-reference coverage provides.
- If we revisit `dodecagonal-square-triangle`, add deeper marked-prototile and substitution-structure checks beyond the current cleaned dense canonical sample, rooted local-reference anchors, exact public canonical patch fixtures, and exact tile-family/orientation/chirality/degree distributions at depths `1` and `3`.
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
