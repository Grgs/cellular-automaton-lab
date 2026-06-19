# Changelog

This is a curated narrative changelog of completed work. Active and upcoming work
lives in [TODO.md](TODO.md). For mechanical commit history, see `git log`.

## Unreleased

- Added an end-to-end periodic tiling workflow: SVG inspection, board-shape diagnostics, transactional catalog installation, preview write/check support, and descriptor/reference auto-discovery.
- Add the 2-uniform #18 tiling `[3^6; 3^2.4.3.4]` with regular triangle and square faces.
- Add the 2-uniform #13 tiling `[3^6; 3^2.4.12]` with regular triangle, square, and dodecagon faces.
- Added a Right-Triangle periodic mixed tiling that splits each square-grid cell into congruent 45-45-90 triangles, with descriptor validation, picker thumbnail data, and reference verification coverage.
- Added the 2-uniform 3-4-6-12 tiling, combining regular triangles, squares, hexagons, and dodecagons in the canonical 3.4.6.4 and 4.6.12 vertex configurations, with reference verification and picker preview coverage. Each face kind gets its own dead-cell tone (dodecagon→hexagon→square→triangle darkening with size), and a new `regular_polygon_kinds` reference invariant independently asserts every face is a regular polygon from its own vertices, catching sheared faces that the count/area/vertex-configuration checks cannot see.
- Completed the compare workspace persistence and live-frame handoff loop: users can save/load/delete named compare runs and custom tiling sets in browser `localStorage`, open a synchronized filmstrip board's current generation back into build mode, and keep using portable `run=v1...` links for cross-device handoff.
- Polished the compare workspace layout and review states: the full-page filmstrip uses wider board tracks, saved-run and saved-tiling controls explain empty states, live side-by-side playback reports loading/error/ready status, and the filmstrip transport/board grid have clearer keyboard and ARIA affordances.
- Made compare mode addressable as a `#/compare` hash route: the panel is deep-linkable and integrated with browser history, so opening it pushes the route, closing clears it, and Back/Forward open and close it. The route coexists with `#share=` board links and works in the standalone build.
- Promoted compare mode to a full-page workspace: on the `#/compare` route it now fills the viewport with a "Back to build" affordance instead of opening as a centred modal over the board. The same panel still supports the modal presentation; the presentation is a parameter of the shared shell.
- Added shareable compare run links: `run=v1.<base64url>` links restore seed/rule/traversal/grid/frame-count/tiling selections in the `#/compare` workspace without auto-running. A run link that is malformed or tagged with a newer, unsupported version now reports the problem in the workspace status line instead of failing silently.
- Added Playwright standalone smoke coverage for the compare workspace so its routing and persistence parity is enforced in the Pyodide build: a `#/compare&run=` deep link restores the setup, and a saved run survives a full reload via `localStorage`.
- Added a synchronized compare filmstrip engine (`POST /api/compare/filmstrip`, mirrored in the standalone runtime): one seed and rule are run across a small, explicit set of tilings, capturing every generation's board state so the tilings can be played back side by side on one shared clock. Bounded for live use (at most 6 tilings, 240 frames, modest grid) with sparse per-frame state and per-tiling geometry sent once. This is the backend foundation for the live side-by-side compare view.
- Wired the filmstrip endpoint into the frontend simulation backend (HTTP and standalone) and added a headless `FilmstripPlayer` synchronized-playback model (one shared frame index across all tilings, play/pause/step/seek/loop), the consumable layer the live side-by-side view will render.
- Added the live side-by-side compare view: a "Play side by side" action in the compare panel runs the selected tilings through the filmstrip engine and plays them in lockstep off one shared clock, with transport controls (play/pause, step, reset, a generation scrubber, and a speed selector) and a per-board live-cell/extinction readout.
- Made rule/topology compatibility explicit and enforced: rules declare `compatible_tiling_families` (universal rules stay `None` so any rule can still be compared across neighborhoods), the kind-specific mixed-tiling rules now restrict themselves to the families whose cell kinds they handle, and reset/config requests reject an incompatible rule with a 400 while restore stays lenient for older snapshots. The per-rule families are surfaced in the rule payload for the picker, and a test enforces that every topology's default rule supports its own family.
- Bounded the simulation session registry with an LRU cap (default 64): a new session past the cap evicts the least-recently-used one, flushing its state to disk so a re-accessed session restores losslessly. This caps the number of live background threads and resident coordinators regardless of how many distinct session ids arrive.
- Centralized session/request/operation error handling in the web routes behind Flask error handlers, removing the per-route `try/except` boilerplate and the action-factory lambdas so each route resolves a coordinator and applies its action directly.
- Promoted `pinwheel-2-1` into the main `Aperiodic` picker group on June 13, 2026 after a visual review against the published Bielefeld patch accepted the rendered field; its exact-`Fraction` `1:4:sqrt(17)` tiles are congruence-verified at every depth, leaving `dodecagonal-square-triangle` as the only experimental aperiodic family.
- Added a `pinwheel-2-1-depth-3` render-review profile so the family's visual review is a repeatable, literature-anchored gate rather than a one-off check.
- Documented a tiling promotion/demotion maintenance checklist and a CI pipefail guardrail in `docs/MAINTENANCE.md`, capturing the coupled edit set and independent-reference review step learned from the `pinwheel` promotion.

## `v0.5.0` Preview Release Candidate

- Added compare mode as a first-class workflow: live seed previews, draw-the-seed input, shareable begin/end links, open-in-place result loading, geometric shape seeding, denser cross-topology previews, and clearer compare modal actions.
- Polished the main app chrome, mobile canvas toolbar, drawer sections, tiling picker, rule search, first-action onboarding, and compare modal so repeated topology/rule switching is easier to scan and operate.
- Promoted `pinwheel` into the main `Aperiodic` picker group on June 12, 2026 after a fresh manual review accepted the corrected congruent patch against the Bielefeld reference, with the new per-tile congruence invariant standing behind the automated gates.
- Fixed the `pinwheel` subdivision shear found by the June 11, 2026 literature comparison: three of the five child tuples were declared in non-canonical vertex order, making the base-to-child map an angle-mismatched affine transform that distorted all of their descendants. Every tile is now a congruent `1:2:sqrt(5)` triangle at every depth, the depth-1 chirality split matches the published 3-right + 2-left rule, and the reference verifier gained a per-tile congruence invariant (`expected_triangle_side_ratios`, applied to `pinwheel` and `pinwheel-2-1`) so this defect class can no longer pass automated gates.
- Fixed tiling picker thumbnail fidelity by regenerating stale sampled geometry, aligning Type 7 Pentagonal with its neutral canvas fill, and making palette-backed thumbnails use the same named fill tokens as the canvas renderer.
- Consolidated the duplicate triangle-hexagon Life rule entry so the rule catalog exposes one canonical mixed-tiling rule instead of parallel aliases.
- Consolidated Python tool configuration (`ruff.toml`, `mypy.ini`, `pytest.ini`, `.coveragerc`) into a single `pyproject.toml` with no behavior changes.
- Regenerated the Python lockfiles with `--generate-hashes --allow-unsafe` so pip verifies download integrity for every pinned file and rejects unpinned requirements at install time.
- Broadened the ruff lint gate with bugbear, pyupgrade, and import sorting (`B`, `UP`, `I`) and modernized the Python tree to match: sorted imports, PEP 695 type aliases and generics, `datetime.UTC`, explicit `zip()` strictness, and explicit exception chaining.
- Hardened and streamlined CI automation: all GitHub Actions references are pinned to commit SHAs, a Dependabot auto-merge workflow lands green minor/patch updates automatically (majors stay manual), `merge_group` support prepares CI for a merge queue, a Windows job runs the backend unit suite, and the Playwright jobs skip browser downloads on cache hits.
- Added a tag-triggered Release workflow that validates release prerequisites, rebuilds and smoke-tests the standalone bundle from the tagged commit, and publishes the GitHub Release with the bundle zip attached, replacing the manual `gh release create` step.
- Added Dependabot update automation for pip, npm, and GitHub Actions dependencies, Node/Python toolchain pins (`engines`, `.nvmrc`, `.python-version`), and version-agnostic preview wording in governance docs.
- Added coverage gates that run on every CI event including pull requests: the combined backend unit + API report must stay at or above 75% line coverage (also enforced by `npm run coverage:backend`), and the frontend Vitest run (`npm run coverage:frontend`) enforces ratchet thresholds in `vite.config.ts`.
- Added a repo-owned `release-check` command and maintenance playbook updates so preview releases have explicit pre-publish and post-publish gates for tags, GitHub Releases, and the latest-release pointer.
- Added a repo-owned `generated-check` umbrella command for generated docs, bootstrap data, frontend topology fixtures, and reference fixture freshness checks.

## `v0.4.0` Preview Release Candidate

- Added several periodic mixed tilings after `v0.3.0`, including Pythagorean, Herringbone, Basketweave, two 2-uniform triangle/hex/square variants, Stein 14 Pentagonal, Pentagon Crosses, and supporting sketch/validation tooling for descriptor-driven topology work.
- Added the two-prototile `pinwheel-2-1` aperiodic family and repaired the Conway-Radin `pinwheel` second-root vertex ordering so exact-affine substitution patches render as the intended pinwheel field.
- Replaced the `dodecagonal-square-triangle` finite-oracle runtime with a decorated periodic `3.12.12` square-triangle generator that scales without vendored literature data, while keeping its non-canonical status documented.
- Improved perceived simulation speed control by presenting target speed separately from measured actual cadence and by adapting polling cadence to the selected target.
- Reduced expensive neighbor construction paths for both periodic-face and segment-overlap aperiodic tilings, including large speedups for `pinwheel-2-1`, `chair`, `penrose-p2-kite-dart`, `robinson-triangles`, and `tuebingen-triangle` at their deeper preview patch depths.
- Consolidated repo tooling under the Python `tools` CLI, added onboarding/examples, strengthened pre-commit/CI parity, and refreshed source-reference/verification fixtures for the expanded catalog.

## `v0.3.0` Preview Release Candidate

- Added `type-7-pentagonal` as a new periodic convex pentagonal family through the existing `periodic_face` descriptor architecture, with backend catalog wiring, picker preview data, and periodic reference validation.
- Added `penrose-p1-pentagon-boat-star` as a separate centered singular-pentagrid Penrose P1 family that emits the full `pentagon` / `diamond` / `boat` / `star` vocabulary instead of overloading the older distributed P1 manifestation.
- Clarified the older non-singular P1 family as `Penrose P1 Pentagon-Diamond (Distributed)`, trimmed its public metadata to the prototiles it actually emits, and aligned docs, fixtures, and release-facing labels with that split.
- Added a startup-time frontend freshness guard so `python app.py` fails fast when `static/dist/` is stale relative to the authored frontend source.
- Refreshed the release-facing documentation set for the current catalog, including README overview text, tiling source references, verification-status summaries, and the `v0.3.0` release-notes draft.

## Public Release Prep

- Framed the first public release line as a `v0.1.x` preview series: tagged GitHub source release plus GitHub Pages standalone demo, without npm or PyPI publishing.
- Added public preview status, release-surface guidance, and explicit known-limitations framing to the README.
- Added a release-process checklist to the maintenance guide, including freeze, validation, CI, tagging, and post-deploy Pages verification.
- Added a draft `v0.1.0` release-notes document and explicit TODO triage for release blockers, acceptable limitations, and post-release follow-up.

## Browser Diagnosis And Render Review

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
- Added advisory visual-quality metrics to render-review output, managed browser-check manifests, and sweep case records, including visible aspect ratio, edge density, boundary dominance, gutter score, orientation diversity, 12-sector occupancy, and radial-symmetry scoring when the live render diagnostics expose the needed inputs.
- Added advisory profile-owned expectations to render review, managed browser-check manifests, sweep case records, and browser-reviewed workbench summaries so named profiles can carry manual checklists plus expected-warning classification without changing command success semantics.
- Moved browser diagnosis and workbench implementation under `tools/render_review/` and reduced the top-level Python commands to thin CLI entrypoints.
- Added a one-command render-review diff tool that either runs a new sweep or consumes an existing `sweep-manifest.json`, then emits one HTML sheet plus one PNG contact sheet for side-by-side review.

## Tilings, Geometry, And Verification

- Restored shield's representative render-space no-overlap fixture by separating topology cleanup from draw-only seam hiding: the shipped topology now uses minimal inward trace cleanup, while the canvas path handles seam bridging without mutating geometry cache vertices.
- Added a family sample workbench for patch-depth families so candidate representative samples can be compared structurally by count, connectivity, bounds, holes, and diagnostic validation, with optional browser review against injected candidate topology payloads.
- Added a geometry cleanup workbench for image-derived families so shield cleanup scales can be compared by overlap severity, bounds drift, and optional browser-visible gutter risk without ad hoc Shapely sweeps.
- Added a frontend representative fixture manifest plus regeneration tool so browser-facing topology fixtures can be checked and refreshed deterministically instead of relying on ad hoc manual export steps.
- Surfaced backend-owned aperiodic implementation status and promotion blockers in the topology picker and drawer UI.
- Replaced the `dodecagonal-square-triangle` finite-oracle runtime with a decorated 3.12.12 Archimedean generator that tiles the plane exactly, scales without a depth cap, and depends on no vendored data; deleted the literature oracle JSON, the substitution spec JSON, the regeneration tools (`regenerate_dodecagonal_literature_source.py`, `regenerate_dodecagonal_substitution_spec.py`), the structure miner (`mine_dodecagonal_square_triangle_structure.py`, `dodecagonal_structure_report.py`, `tiling_template_analysis.py`), their unit tests, and the contracts-bundle source assets (Bielefeld patch PDF and rule image).

## Dodecagonal Square-Triangle Investigation (Pre-Replacement)

This was a multi-pass effort to recover marked-prototile substitution rules from
the literature-derived source patch. The work was ultimately superseded by the
decorated 3.12.12 Archimedean generator listed above, but the pipeline is
documented here for context.

- Added a first-pass dodecagonal structure miner that reports repeated local shell signatures and bounded square/triangle macro-candidate unions from the literature-derived source patch.
- Added a second-pass dodecagonal supertile miner that grows repeated macro seeds through symmetry-normalized neighbor-slot support, surfacing a stable five-cell square-seeded candidate pattern from the literature-derived source patch.
- Added a third-pass dodecagonal inflation probe that extracts boundary line families from the five-cell seed, searches stable second-ring slot combinations, and surfaces a repeatable ten-cell polygonal closure with an approximate scale-up factor.
- Added a boundary-template inference pass for dodecagonal inflation candidates that canonicalizes repeated larger closures under seed symmetry and reports explicit normalized line-family offsets for the dominant repeated templates.
- Added a line-equation and supertile-decomposition pass for dodecagonal boundary templates that emits explicit normalized line equations and groups repeated interval-signature decomposition components inside the dominant larger templates.
- Added a dodecagonal macro-composition pass that unions repeated decomposition-region signatures and surfaces recurring square macro-cells inside the dominant 8-cell and 10-cell literature-derived templates.
- Added a first recovered-rule pass for dodecagonal templates that promotes repeated macro-composition patterns into explicit substitution-style child rules and checks whether those child rules recur on a slightly deeper shell window of the literature-derived source patch.
- Extracted a reusable planar template-analysis module for polygon context building, subset scoring, boundary canonicalization, line-family inference, slot normalization, and template-component recovery so later tiling miners do not need to duplicate the dodecagonal geometry/template machinery.
- Added a recovered parent-decomposition pass for dodecagonal templates that mixes verified multi-region child rules with recurring singleton square/triangle components, yielding fully covered child inventories for several parent templates and deeper-shell verification counts for each recovered piece.
- Added a canonical parent-rule pass for dodecagonal templates that solves a compact exact cover over recovered composition pieces plus primitive square/triangle components, yielding smaller fully covered child inventories for the strongest parent templates.
- Extended the canonical parent-rule pass with template-local composition mining at a lower support threshold, which reduced the strongest verified 7-cell square-seeded parent to a 7-piece exact cover with three square-valued multi-region children and twelve deeper-shell template matches.
- Folded deeper-window template-local compositions back into the canonical rule candidate pool and gave canonical recovery its own wider template-local decomposition state, which strengthened the strongest verified 7-cell square-seeded parent into a full 7-piece exact cover with four square-valued multi-region children and twelve deeper-shell template matches.
- Added an evidence-ranked parent-rule pass for dodecagonal templates that kept exact-cover recovery from over-optimizing for compactness alone, surfacing fully verified zero-weak-piece covers for the strongest 7-cell square-seeded parent across the deeper verification window.

## Frontend Architecture

- Replaced click-driven palette alias browser tests with a review/test API that injects topology and mutates cell state by `cell.id`, then samples rendered pixels directly from the canvas.
- Moved custom dead-palette ownership and fixture-backed browser alias coverage onto a shared manifest/registry contract so TypeScript and Python no longer maintain separate family allowlists for this test surface.
- Tightened the interaction stack around explicit pointer-down intent resolution and session-owned pointer matching/completion, so the router no longer hardcodes per-session pointer-id policy.
- Split the drawer view model into section-owned builders for shell state, inspector/header state, topology/sizing, rule/palette, and pattern controls.

## Tooling Hygiene

- Added incremental lint/format guardrails for the render-review/bootstrap slice plus a repo-owned frontend formatting check.
