# Code Quality Roadmap

This document is a current-state cleanup assessment. It is not a feature roadmap. It identifies the code areas that most need structural change for the app to stay maintainable as tilings, interaction modes, standalone runtime, and verification coverage keep growing.

## Current State

The app is in a workable state. The major runtime boundaries are visible:

- backend simulation state is authoritative
- frontend mutations are explicit
- topology catalog data is bootstrapped into the frontend
- server and standalone hosts share the same UI shell
- validation and literature verification are separate concepts
- interaction behavior is covered by unit tests and browser tests

The main problem is not missing abstraction everywhere. The main problem is that a few high-change subsystems have accumulated too many responsibilities in single files or tightly coupled call chains. Those areas now need stronger ownership boundaries before more features are added.

## Assessment Basis

This assessment is based on the current code shape, recent feature work, and the files that now carry the broadest responsibility:

- `frontend/canvas-view.ts` has become the owner for committed canvas caching plus multiple transient visual layers.
- `frontend/interactions/surface-bindings.ts`, `legacy-drag.ts`, and `editor-session.ts` coordinate several pointer gestures with overlapping lifecycle rules.
- `frontend/controls-model/drawer.ts` is now both the drawer aggregator and the right-click cell metadata model.
- `backend/simulation/literature_reference_specs.py` and `backend/simulation/literature_reference_verification.py` are now compatibility facades, but the newly split verifier/spec modules should stay small as more verification modes are added.
- Aperiodic tiling builders vary in implementation strength, so implementation status, picker status, and verification language need explicit per-family contracts.
- Browser E2E tooling has grown into a real runtime subsystem and should be treated as such instead of as loose Python commands.

## Cleanup Principles

- Keep state ownership explicit. Backend simulation state, frontend app state, and view-local canvas state should not blur together.
- Preserve plan/runtime splits. Pure planning code should remain testable without DOM, canvas, Flask, workers, or timers.
- Prefer small subsystem-owned constants and helpers over global configuration dumps.
- Do not hide mathematically weak tiling implementations behind stronger UI or verification wording.
- Browser tests should validate browser behavior only. Logic that can be proven in unit/API tests should stay out of Playwright.
- Every new interaction mode should flow through one coherent gesture model, not another special-case pointer branch.

## Priority Areas

### 1. Frontend Gesture And Selection Model

Primary files:

- [surface-bindings.ts](../frontend/interactions/surface-bindings.ts)
- [legacy-drag.ts](../frontend/interactions/legacy-drag.ts)
- [editor-session.ts](../frontend/interactions/editor-session.ts)
- [command-dispatch.ts](../frontend/interactions/command-dispatch.ts)
- [interactions.ts](../frontend/interactions.ts)
- [interaction-groups.ts](../frontend/interaction-groups.ts)

Current issue:

The interaction stack supports hover, right-drag selection, direct left-button paint/erase, armed brush/fill/line/rectangle tools, gesture afterglow, undo/redo, and drawer updates. Those behaviors are tested, but they are coordinated through multiple mutable flags and branches in `surface-bindings.ts`.

Needed change:

Replace the ad hoc pointer branching with an explicit gesture state machine. The state machine should classify each pointer interaction into one of a small set of gesture sessions:

- idle hover
- left direct paint/erase
- right selection add/remove
- armed brush
- armed shape preview
- armed fill click

Each gesture session should own:

- start conditions
- update behavior
- cancel behavior
- commit behavior
- transient overlay requests
- history behavior
- control-panel refresh behavior

Target outcome:

Adding a new gesture should require adding one session implementation, not editing many unrelated branches. Undo/history and metadata refresh should become session outcomes instead of side effects hidden in surface bindings.

Implementation status:

The first extraction is in place. `surface-bindings.ts` now delegates pointer lifecycle behavior to `frontend/interactions/gesture-sessions.ts`, the gesture router resolves explicit pointer-down intents before starting a session, and the per-session modules now own pointer-id matching plus up/cancel completion semantics for legacy drag, armed editor pointer sessions, and right-button selection gestures. The router still owns idle click/context-menu policy, which is acceptable unless that path grows new modes.

### 2. Canvas Transient Overlay Rendering

Primary files:

- [canvas-view.ts](../frontend/canvas-view.ts)
- [render-layers.ts](../frontend/canvas/render-layers.ts)
- [render-style.ts](../frontend/canvas/render-style.ts)
- [draw.ts](../frontend/canvas/draw.ts)
- [square-adapter.ts](../frontend/geometry/square-adapter.ts)
- [periodic-mixed-adapter.ts](../frontend/geometry/periodic-mixed-adapter.ts)
- [aperiodic-prototile-adapter.ts](../frontend/geometry/aperiodic-prototile-adapter.ts)

Current issue:

The canvas view now owns committed rendering, hover state, persistent selected cells, paint previews, gesture outlines, timeout cleanup, topology-revision cleanup, and render-order rules. The behavior is good, but the ownership is too concentrated.

Needed change:

Introduce a small `TransientOverlayState` and an overlay renderer that owns:

- hover cell
- selected cells
- preview cells
- gesture outline cells
- overlay render order
- timeout lifecycle for gesture flashes
- topology-revision cleanup

Canvas view should remain responsible for canvas surface lifecycle, committed-layer caching, hit testing, and invoking the overlay renderer.

Target outcome:

Canvas view becomes smaller and easier to reason about. Overlay behavior can be tested without constructing the full canvas view.

Implementation status:

The next extraction is now in place. `frontend/canvas/transient-overlays.ts` owns hover, selection, preview, gesture outline, flash timing, and topology cleanup state; `frontend/canvas/overlay-renderer.ts` owns transient overlay draw order; `frontend/canvas/committed-renderer.ts` owns committed-layer lifecycle, viewport alignment, geometry cache invalidation, and pointer hit testing; and `frontend/canvas/render-diagnostics.ts` owns diagnostics sampling plus rendered-cell lookup. `canvas-view.ts` is now a thin facade that composes those subsystems. Render-style ownership is also split: `theme-colors.ts` owns CSS token/color utilities, `state-colors.ts` owns cell-state and dead-state palette resolution, and `overlay-style.ts` owns transient overlay color policy.

### 3. Drawer And Inspector View Models

Primary files:

- [app-view.ts](../frontend/app-view.ts)
- [drawer.ts](../frontend/controls-model/drawer.ts)
- [view-sections.ts](../frontend/controls/view-sections.ts)
- [types/ui.d.ts](../frontend/types/ui.d.ts)
- [types/dom.d.ts](../frontend/types/dom.d.ts)

Current issue:

The drawer now includes rule/palette information, sizing settings, unsafe controls, and right-click cell metadata. The selection-inspector feature is useful, but it makes the drawer model a growing aggregation point.

Needed change:

Split drawer model construction into section-owned builders:

- cell metadata inspector
- rule and palette
- sizing and topology
- editor/pattern controls
- advanced settings

The right-click metadata inspector should be built from a typed selector over `gridView.getSelectedCells()`, `topologyIndex`, and `cellStates`, not inline in the broad drawer model.

Target outcome:

Adding a drawer section should not increase coupling between unrelated controls. Section tests should be able to exercise their model builders independently.

Implementation status:

The right-click metadata builder now lives in `frontend/controls-model/selection-inspector.ts`, and the broader drawer model is now split into section-owned builders for shell state, inspector/header state, topology/sizing, rule/palette, and pattern controls. `drawer.ts` is now just the composition layer for those sections.

### 4. Aperiodic Tiling Implementations

Primary files:

- [aperiodic_registry.py](../backend/simulation/aperiodic_registry.py)
- [aperiodic_substitution.py](../backend/simulation/aperiodic_substitution.py)
- [aperiodic_support.py](../backend/simulation/aperiodic_support.py)
- [aperiodic_dodecagonal_square_triangle.py](../backend/simulation/aperiodic_dodecagonal_square_triangle.py)
- [aperiodic_shield.py](../backend/simulation/aperiodic_shield.py)
- [aperiodic_pinwheel.py](../backend/simulation/aperiodic_pinwheel.py)
- [topology_validation.py](../backend/simulation/topology_validation.py)

Current issue:

Most aperiodic families are now in better shape than the original generated patches, but the implementation quality is uneven. `dodecagonal-square-triangle` and `pinwheel` remain experimental because manual visual review still does not justify promotion. `shield` is now on the exact marked substitution path, passed a fresh manual visible-review pass on April 19, 2026, and has been promoted into the main `Aperiodic` group. The remaining shield work is cleanup of compatibility-only legacy diagnostics, not replacement of the generator itself.

Needed change:

Create per-family implementation contracts that state whether the family is:

- true substitution implementation
- exact-affine implementation
- literature-derived canonical patch
- known deviation

Each contract should identify:

- source references
- public cell kinds
- internal metadata semantics
- expected depth behavior
- validation mode
- promotion blocker, if any

Shield should stay documented as experimental until the new exact marked substitution path has an intentional visible-review decision and the remaining compatibility-only diagnostic tooling is either removed or simplified.

Target outcome:

The code stops treating all aperiodic builders as equally authoritative. Product status, verification status, and implementation quality stay aligned.

Implementation status:

The first contract layer is in place in `backend/simulation/aperiodic_contracts.py`. It records implementation status, source links, public kinds, metadata fields, depth semantics, verification modes, and promotion blockers for every aperiodic catalog family. The verification-strength report now includes the implementation-status column, with `shield` promoted from `known_deviation` to `true_substitution`, while `dodecagonal-square-triangle` and `pinwheel` still remain explicitly blocked pending visual review. Backend-owned `aperiodic_families` bootstrap metadata now also carries those status fields into the frontend, and the picker/drawer surface experimental status directly instead of hiding it in backend/test-only layers.

### 5. Literature Verification And Fixtures

Primary files:

- [literature_reference_specs.py](../backend/simulation/literature_reference_specs.py)
- [literature_reference_verification.py](../backend/simulation/literature_reference_verification.py)
- [reference_patch_local_fixtures.json](../backend/simulation/data/reference_patch_local_fixtures.json)
- [reference_patch_canonical_fixtures.json](../backend/simulation/data/reference_patch_canonical_fixtures.json)
- [report_tiling_verification_strength.py](../tools/report_tiling_verification_strength.py)

Current issue:

The verifier is valuable, but the two core Python files are large and mix family specs, observation logic, canonical serialization, mismatch reporting, dual checks, and fixture comparison.

Needed change:

Split verification into narrower modules:

- spec data by family group
- periodic descriptor verification
- aperiodic depth verification
- canonical patch serialization
- fixture loading/comparison
- report formatting

Also add a fixture-regeneration workflow that makes intentional fixture updates explicit.

Target outcome:

The verifier remains strict without becoming a single-file policy engine. Adding a family should not require understanding every verification mode.

Implementation status:

The first split is in place. `backend/simulation/literature_reference_specs.py` now merges grouped spec modules from `backend/simulation/reference_specs/`, and `backend/simulation/literature_reference_verification.py` is a compatibility facade over `backend/simulation/reference_verification/` modules for observation, fixtures, depth checks, periodic checks, shared types, and runner orchestration. `tools/regenerate_reference_fixtures.py` now makes local and canonical fixture regeneration explicit, deterministic, and checkable.
The verification-strength report is now a real aggregator instead of a thin tag dump: `tools/report_tiling_verification_strength.py` combines static coverage, aperiodic implementation contracts, fixture presence, and live `verify_all_reference_families()` results into summary, detail, and deterministic JSON outputs.
Direct canonical patch comparison now covers both shallow and representative depths for the highest-risk aperiodic families: `robinson-triangles`, `tuebingen-triangle`, `dodecagonal-square-triangle`, `shield`, and `pinwheel` all have checked-in direct patch fixtures at depth `1`, while their strongest representative fixtures remain checked in at depth `3`. Canonical fixture policy such as whether ids must be part of the comparison is now owned by the backend reference spec instead of by the JSON fixture file.

### 6. Frontend Geometry Adapter Common Path

Primary files:

- [geometry/shared.ts](../frontend/geometry/shared.ts)
- [geometry/periodic-mixed-adapter.ts](../frontend/geometry/periodic-mixed-adapter.ts)
- [geometry/aperiodic-prototile-adapter.ts](../frontend/geometry/aperiodic-prototile-adapter.ts)
- [geometry/triangle-adapter.ts](../frontend/geometry/triangle-adapter.ts)
- [geometry/hex-adapter.ts](../frontend/geometry/hex-adapter.ts)
- [geometry/square-adapter.ts](../frontend/geometry/square-adapter.ts)

Current issue:

Adapters have converged on similar responsibilities: metrics, hit testing, committed rendering, preview rendering, hover rendering, selection rendering, gesture outline rendering, and overlap/render-bounds expectations. Some shared behavior still has adapter-local copies.

Needed change:

Extract common polygon adapter operations:

- path construction
- overlay rendering
- stroke-width choice
- bounds/metrics helpers
- per-cell display transforms
- hit-test helpers where possible

Do not over-abstract regular square/hex/triangle math if local formulas remain clearer.

Target outcome:

Visual behavior stays consistent across tilings, and changing overlay or selection rendering no longer requires editing every adapter.

Implementation status:

The polygon adapter path is now shared more coherently. `frontend/geometry/polygon-adapter-shared.ts` owns polygon bounds measurement, transformed-cell construction, cache-backed cell resolution, rendered-center lookup, overlay/grid drawing, and polygon hit-test routing for the mixed periodic, Penrose, and generic aperiodic adapters. This also fixed the old mixed-adapter fallback-center bug where transformed bounds could be fed back through raw-coordinate center math. Regular square, hex, and triangle adapters remain local because their grid math is still clearer outside a polygon abstraction.

### 7. Frontend Type Surfaces

Primary files:

- [types/domain.d.ts](../frontend/types/domain.d.ts)
- [types/controller-api.d.ts](../frontend/types/controller-api.d.ts)
- [types/controller-view.d.ts](../frontend/types/controller-view.d.ts)
- [types/editor.d.ts](../frontend/types/editor.d.ts)
- [payload_types.py](../backend/payload_types.py)
- [contract_validation.py](../backend/contract_validation.py)

Current issue:

Frontend and backend payload contracts are manually kept in sync. That has worked because tests are strong, but the surface keeps growing: topology metadata, editor commands, standalone worker protocol, reset/config payloads, and pattern import/export all duplicate shape knowledge.

Needed change:

Choose one of these approaches:

- generate frontend API/domain types from backend schema definitions
- generate backend payload stubs from a shared schema source
- add a contract snapshot test that compares serialized backend schema metadata to frontend expectations

Target outcome:

Payload drift becomes mechanically visible before it reaches runtime or E2E tests.

Implementation status:

The drift guard now covers substantially more of the shared schema surface. `backend/payload_contracts.py` derives frontend field contracts directly from backend `TypedDict` payload definitions in `payload_types.py`, including bootstrap metadata, rule/snapshot payloads, pattern export payloads, request bodies, and the rendering-side periodic face tiling descriptor. The same test module now also checks drift-prone canonical type references and aliases across `frontend/types/controller-view.d.ts`, `frontend/types/controller-sync-session.d.ts`, `frontend/types/editor.d.ts`, and `frontend/types/actions.d.ts`, while still asserting the standalone worker request payload union in `frontend/standalone/protocol.ts`.

### 8. E2E Tooling And Browser Runtime

Primary files:

- [run-playwright.mjs](../tools/run-playwright.mjs)
- [run-python.mjs](../tools/run-python.mjs)
- [support_runtime_host.py](../tests/e2e/support_runtime_host.py)
- [playwright_case_suite.py](../tests/e2e/playwright_case_suite.py)
- [playwright_suite_support.py](../tests/e2e/playwright_suite_support.py)

Current issue:

The Playwright harness is effective but expensive. It now covers both server and standalone hosts, handles local browser runtime libraries, and captures failure artifacts. That power also makes the test harness a real subsystem.

Needed change:

Keep the npm scripts as the public entrypoints and document that direct Python commands are mostly for CI internals. Next cleanup should:

- make browser-lib repair messages explicit when `apt download` is unavailable
- avoid duplicate standalone rebuilds across local commands
- keep suite grouping in one place
- add a short troubleshooting section for local Linux browser dependencies

Target outcome:

Developers run the same entrypoints locally and in CI, reducing stale assumptions like waiting for server HTTP responses in standalone mode.

Implementation status:

The consolidation is now stronger. `tests/e2e/playwright_suite_support.py` remains the single public suite manifest, `tools/run-playwright.mjs` still selects suites by semantic name, and the runner now consults a backend-owned standalone build-status report before rebuilding. That means local npm Playwright commands reuse `output/standalone/` when the build fingerprint still matches the current checkout instead of rebuilding blindly. `docs/TESTING.md` now also maps common Playwright failure classes to the right npm command and Linux browser-library repair path. The browser diagnosis and workbench commands continue to share one real package under `tools/render_review/`, with the top-level `tools/run_*.py` and `tools/render_canvas_review.py` files reduced to CLI entrypoints.

## Quick Wins

These are low-risk cleanup tasks worth doing before larger refactors:

- Add a `docs` note for which npm script to run for each E2E failure class.

## Do Not Do Yet

- Do not promote `dodecagonal-square-triangle` or `pinwheel` until manual visual review and implementation status justify it.
- Do not centralize all constants into one global config file.
- Do not rewrite the app controller stack without first extracting gesture and overlay state; those are the higher-churn seams.
- Do not replace Playwright coverage with unit tests for flows that genuinely require DOM, canvas, browser storage, or standalone worker execution.

## Suggested Order

1. Split remaining drawer sections into section-owned builders once metadata and editor controls grow again.
2. Expand Python lint/format guardrails beyond the current render-review/bootstrap slice once the older compatibility facades stop depending on import-for-export and `sys.path` bootstrap patterns.
