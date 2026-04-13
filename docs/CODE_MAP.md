# Code Map

This is a runtime-focused map of the app. It is meant to answer two questions quickly:

1. Where does the app start in server mode and standalone mode?
2. Which files and functions should you follow for a given kind of change?

For the higher-level architecture, see [ARCHITECTURE.md](./ARCHITECTURE.md).
For cleanup priorities and known structural pressure points, see [CODE_QUALITY_ROADMAP.md](./CODE_QUALITY_ROADMAP.md).

## Start Here

### Server runtime

1. [app.py](../app.py)
   Entry script for local Flask development. Calls `create_app()` and starts the dev server.
2. [backend/api.py](../backend/api.py)
   Flask app factory. `create_app(...)` wires config, frontend assets, topology metadata, simulation extensions, and routes.
3. [backend/simulation/bootstrap.py](../backend/simulation/bootstrap.py)
   `register_simulation(app)` creates and stores the simulation coordinator and rule registry.
4. [backend/web/routes.py](../backend/web/routes.py)
   HTTP entrypoints for state fetches and mutations.
5. [backend/web/state_actions.py](../backend/web/state_actions.py)
   Bridges validated request payloads to simulation mutations.
6. [backend/simulation/coordinator.py](../backend/simulation/coordinator.py)
   Coordinates runtime, persistence, restore, and simulation service.
7. [backend/simulation/service.py](../backend/simulation/service.py)
   Main synchronous simulation API used by the host layers.
8. [backend/simulation/engine.py](../backend/simulation/engine.py)
   Pure stepping engine that asks the current rule for each cell's next state.

### Standalone browser runtime

1. [tools/build-standalone.mjs](../tools/build-standalone.mjs)
   Stages the transient standalone build input, runs the standalone Vite build, and finalizes the published static output.
2. [frontend/shell/app-shell-body.html](../frontend/shell/app-shell-body.html)
   Shared shell source used by both Flask and the standalone wrapper.
3. [tools/render_standalone_shell.py](../tools/render_standalone_shell.py)
   Writes the generated standalone wrapper into the build-owned input directory.
4. [frontend/standalone.ts](../frontend/standalone.ts)
   `startStandaloneApp()` loads bootstrap JSON, creates the standalone worker environment, and then calls `initApp(...)`.
5. [frontend/standalone/worker-client.ts](../frontend/standalone/worker-client.ts)
   `createStandaloneEnvironment(...)` creates the Web Worker, talks to Pyodide, and exposes a `SimulationBackend`.
6. [frontend/standalone-worker.ts](../frontend/standalone-worker.ts)
   Worker entrypoint that loads Python and forwards commands into the browser runtime host.
7. [backend/browser_runtime.py](../backend/browser_runtime.py)
   Python runtime host for standalone mode. Exposes `initialize_runtime(...)`, `handle_request(...)`, and `tick_running()`.

### Browser UI startup

1. [frontend/server-entry.ts](../frontend/server-entry.ts)
   Canonical server host entrypoint.
2. [frontend/app-runtime.ts](../frontend/app-runtime.ts)
   `initApp(...)` creates the top-level controller and marks the app ready.
3. [frontend/app-controller.ts](../frontend/app-controller.ts)
   `createAppController(...)` composes state, view, actions, sync, and interactions.
4. [frontend/app-controller-startup.ts](../frontend/app-controller-startup.ts)
   `initializeAppController(...)` orchestrates service construction, interaction wiring, and hydration.
5. [frontend/app-controller-services.ts](../frontend/app-controller-services.ts)
   Builds the session/config-sync/simulation-mutation service layer.
6. [frontend/app-controller-wiring.ts](../frontend/app-controller-wiring.ts)
   Connects interactions, viewport sync, and the action surface.
7. [frontend/app-controller-hydration.ts](../frontend/app-controller-hydration.ts)
   Preserves the async startup order for rules, controls, refresh, and listeners.
8. [frontend/app-actions.ts](../frontend/app-actions.ts)
   Creates the action surface used by controls and interaction handlers.
9. [frontend/app-view.ts](../frontend/app-view.ts)
   Renders the control shell and canvas-facing UI.

## Request Flow

### Server-backed flow

```text
Browser UI
  -> frontend/api.ts
  -> backend/web/routes.py
  -> backend/web/state_actions.py
  -> backend/simulation/coordinator.py
  -> backend/simulation/service.py
  -> backend/simulation/engine.py + backend/rules/*
  -> snapshot response
  -> frontend/state/snapshot-reducer.ts
  -> canvas + controls rerender
```

### Standalone flow

```text
Browser UI
  -> frontend/standalone/worker-client.ts
  -> frontend/standalone-worker.ts
  -> backend/browser_runtime.py
  -> backend/simulation/service.py
  -> backend/simulation/engine.py + backend/rules/*
  -> worker response
  -> frontend/state/snapshot-reducer.ts
  -> canvas + controls rerender
```

## Frontend Map

### App composition

- [frontend/app-runtime.ts](../frontend/app-runtime.ts)
  `initApp(...)`, `disposeApp()`
- [frontend/server-entry.ts](../frontend/server-entry.ts)
  Server-only host bootstrap.
- [frontend/app-controller.ts](../frontend/app-controller.ts)
  `createAppController(...)`
- [frontend/app-controller-startup.ts](../frontend/app-controller-startup.ts)
  `initializeAppController(...)`
- [frontend/app-controller-services.ts](../frontend/app-controller-services.ts)
  Service-phase startup wiring.
- [frontend/app-controller-wiring.ts](../frontend/app-controller-wiring.ts)
  Interaction, viewport, and action wiring.
- [frontend/app-controller-hydration.ts](../frontend/app-controller-hydration.ts)
  Async hydration and control-binding order.
- [frontend/app-controller-sync.ts](../frontend/app-controller-sync.ts)
  `createAppControllerSync(...)`
- [frontend/app-controller-bootstrap.ts](../frontend/app-controller-bootstrap.ts)
  `createAppControllerBootstrap(...)`, `createViewportControllerDependencies(...)`
- [frontend/config-sync-controller.ts](../frontend/config-sync-controller.ts)
  `createConfigSyncController(...)`
- [frontend/ui-session-controller.ts](../frontend/ui-session-controller.ts)
  `createUiSessionController(...)`
- [frontend/server-environment.ts](../frontend/server-environment.ts)
  `createServerEnvironment()`
- [frontend/bootstrap-data.ts](../frontend/bootstrap-data.ts)
  `installBootstrapData(...)`, `bootstrapDataFromWindow()`, `fetchBootstrapData(...)`

### App state

- [frontend/state/simulation-state.ts](../frontend/state/simulation-state.ts)
  Main app state container and mutation helpers.
  Key functions: `createAppState()`, `setRules(...)`, `setActiveRule(...)`, `setTopology(...)`, `setSpeed(...)`
- [frontend/state/snapshot-reducer.ts](../frontend/state/snapshot-reducer.ts)
  `applySimulationSnapshot(...)`
- [frontend/simulation-reconciler.ts](../frontend/simulation-reconciler.ts)
  `createSimulationReconciler(...)`
- [frontend/state/selectors.ts](../frontend/state/selectors.ts)
  `currentEditorRule(...)`, `currentDimensions(...)`, `topologyRenderPayload(...)`
- [frontend/state/sizing-state.ts](../frontend/state/sizing-state.ts)
  Cell-size and patch-depth rules.
- [frontend/state/overlay-state.ts](../frontend/state/overlay-state.ts)
  Drawer, inspector, hint, blocking, and edit-mode state.
- [frontend/state/polling.ts](../frontend/state/polling.ts)
  `schedulePolling(...)`, `syncPolling(...)`, `stopPolling(...)`

### Actions and control flow

- [frontend/app-actions.ts](../frontend/app-actions.ts)
  `createAppActions(...)`
- [frontend/app-action-groups.ts](../frontend/app-action-groups.ts)
  Groups action composition into simulation/config, pattern/preset/showcase, and editor/UI seams.
- [frontend/actions/simulation/index.ts](../frontend/actions/simulation/index.ts)
  `createSimulationActions(...)`
- [frontend/actions/simulation/topology-selection-plan.ts](../frontend/actions/simulation/topology-selection-plan.ts)
  Pure topology reset and selection planning.
- [frontend/actions/simulation/topology-selection-runtime.ts](../frontend/actions/simulation/topology-selection-runtime.ts)
  Transaction layer for optimistic topology changes, reset dispatch, and rollback.
- [frontend/actions/simulation/run-actions.ts](../frontend/actions/simulation/run-actions.ts)
  Start, pause, resume, step actions.
- [frontend/actions/simulation/rule-actions.ts](../frontend/actions/simulation/rule-actions.ts)
  Rule changes.
- [frontend/actions/simulation/topology-actions.ts](../frontend/actions/simulation/topology-actions.ts)
  Topology changes.
- [frontend/actions/pattern-import-plan.ts](../frontend/actions/pattern-import-plan.ts)
  Pure pattern-import confirmation, reset-request, and cell-update helpers.
- [frontend/actions/pattern-import-runtime.ts](../frontend/actions/pattern-import-runtime.ts)
  Pattern import parsing, mutation orchestration, validation, and status handling.
- [frontend/actions/preset-actions.ts](../frontend/actions/preset-actions.ts)
  Applies built-in seed presets.
- [frontend/actions/pattern-actions.ts](../frontend/actions/pattern-actions.ts)
  Thin import/export/copy/paste entrypoints and export serialization.
- [frontend/actions/ui-actions.ts](../frontend/actions/ui-actions.ts)
  Theme, drawer, and disclosure UI actions.

### Controls and view

- [frontend/app-view.ts](../frontend/app-view.ts)
  Top-level UI composition.
- [frontend/controls-view.ts](../frontend/controls-view.ts)
  `renderControls(...)`
- [frontend/controls-model.ts](../frontend/controls-model.ts)
  `collectConfig(...)`, `buildControlsViewModel(...)`
- [frontend/controls-model/shared.ts](../frontend/controls-model/shared.ts)
  Shared view-model builders for run state, blocking state, overlay state, and numeric controls.
- [frontend/controls-bindings.ts](../frontend/controls-bindings.ts)
  `bindControls(...)`
- [frontend/controls](../frontend/controls)
  Shell, simulation, editor/pattern, chrome, and disclosure render/binding modules.

### Canvas, rendering, and geometry

- [frontend/canvas-view.ts](../frontend/canvas-view.ts)
  `createCanvasGridView(...)`, hit testing, and cell-center helpers.
- [frontend/canvas/render-layers.ts](../frontend/canvas/render-layers.ts)
  `drawCommittedLayer(...)`, `drawPreviewLayer(...)`
- [frontend/canvas/render-style.ts](../frontend/canvas/render-style.ts)
  Color and line-style resolution.
  Key functions: `resolveCanvasRenderStyle(...)`, `resolveDeadCellColor(...)`, `resolveRenderedCellColor(...)`
- [frontend/canvas/draw.ts](../frontend/canvas/draw.ts)
  Shared polygon and triangle path/stroke helpers.
- [frontend/canvas/cache.ts](../frontend/canvas/cache.ts)
  `resolveGeometryCache(...)`
- [frontend/geometry/registry.ts](../frontend/geometry/registry.ts)
  `getGeometryAdapter(...)`, `listGeometryAdapters()`
  Bootstraps geometry adapters from topology `render_kind` metadata instead of hand-maintained geometry lists.
- [frontend/geometry/square-adapter.ts](../frontend/geometry/square-adapter.ts)
- [frontend/geometry/hex-adapter.ts](../frontend/geometry/hex-adapter.ts)
- [frontend/geometry/triangle-adapter.ts](../frontend/geometry/triangle-adapter.ts)
- [frontend/geometry/periodic-mixed-adapter.ts](../frontend/geometry/periodic-mixed-adapter.ts)
  Main mixed-tiling adapter.
- [frontend/geometry/penrose-adapter.ts](../frontend/geometry/penrose-adapter.ts)
- [frontend/geometry/aperiodic-prototile-adapter.ts](../frontend/geometry/aperiodic-prototile-adapter.ts)

### Interaction and editor stack

- [frontend/interactions.ts](../frontend/interactions.ts)
  `createInteractionController(...)`
- [frontend/interaction-groups.ts](../frontend/interaction-groups.ts)
  Splits interaction composition into mutation policy, editor runtime, and surface/command wiring.
- [frontend/interactions/editor-session.ts](../frontend/interactions/editor-session.ts)
  Edit-session lifecycle.
- [frontend/interactions/simulation-mutations.ts](../frontend/interactions/simulation-mutations.ts)
  Commits UI edit intents to the simulation backend.
- [frontend/interactions/command-dispatch.ts](../frontend/interactions/command-dispatch.ts)
  Serialized command dispatch.
- [frontend/editor-operation-builders.ts](../frontend/editor-operation-builders.ts)
  Brush, line, rectangle, and fill cell builders.
- [frontend/editor-history.ts](../frontend/editor-history.ts)
  Undo/redo stack and edit diff handling.

### Patterns, presets, and topology metadata

- [frontend/pattern-io.ts](../frontend/pattern-io.ts)
  `buildPatternPayload(...)`, `serializePatternPayload(...)`, `readPatternFile(...)`, clipboard helpers.
- [frontend/presets.ts](../frontend/presets.ts)
  `listAvailablePresets(...)`, `buildPresetSeed(...)`
- [frontend/presets/registry.ts](../frontend/presets/registry.ts)
  Rule-to-preset registry.
- [frontend/topology-catalog.ts](../frontend/topology-catalog.ts)
  Frontend topology definition lookup and picker metadata.
- [frontend/topology.ts](../frontend/topology.ts)
  Topology helpers like `indexTopology(...)`, `findTopologyCellById(...)`

## Backend Map

### Flask host and request layer

- [backend/api.py](../backend/api.py)
  `create_app(...)`
- [backend/app_shell.py](../backend/app_shell.py)
  Shared shell rendering for the Flask wrapper and standalone shell generation.
- [backend/web/routes.py](../backend/web/routes.py)
  Thin Flask routes and JSON response helpers.
  Main endpoints: `get_state()`, `get_rules()`, `get_bootstrap()`, `start()`, `pause()`, `resume()`, `step()`, `reset()`, `update_config()`, `toggle_cell()`, `set_cell()`, `set_cells()`
- [backend/web/state_actions.py](../backend/web/state_actions.py)
  `StateActionService`
- [backend/web/requests.py](../backend/web/requests.py)
  `get_payload(request)`
- [backend/contract_validation.py](../backend/contract_validation.py)
  Shared payload validation for both Flask and standalone browser runtime.

### Simulation façade and runtime

- [backend/simulation/bootstrap.py](../backend/simulation/bootstrap.py)
  `register_simulation(app)`
- [backend/simulation/coordinator.py](../backend/simulation/coordinator.py)
  `SimulationCoordinator`
- [backend/simulation/coordinator_persistence.py](../backend/simulation/coordinator_persistence.py)
  Persistence scheduling and save/load orchestration.
- [backend/simulation/coordinator_restore.py](../backend/simulation/coordinator_restore.py)
  Persisted-state restore flow.
- [backend/simulation/coordinator_mutations.py](../backend/simulation/coordinator_mutations.py)
  Immediate vs deferred mutation dispatch.
- [backend/simulation/service.py](../backend/simulation/service.py)
  `SimulationService`
  Key methods: `get_state()`, `step()`, `reset(...)`, `update_config(...)`, `toggle_cell_by_id(...)`, `set_cell_state_by_id(...)`, `set_cells_by_id(...)`
- [backend/simulation/runtime.py](../backend/simulation/runtime.py)
  `SimulationRuntime`
- [backend/simulation/engine.py](../backend/simulation/engine.py)
  `SimulationEngine.step_board(...)`
- [backend/simulation/service_transitions.py](../backend/simulation/service_transitions.py)
  `apply_reset_transition(...)`, `apply_config_transition(...)`
- [backend/simulation/service_boards.py](../backend/simulation/service_boards.py)
  Board creation, coercion, and transfer helpers.
- [backend/simulation/service_cells.py](../backend/simulation/service_cells.py)
  Cell mutation helpers.
- [backend/simulation/service_snapshots.py](../backend/simulation/service_snapshots.py)
  `snapshot_state(...)`

### Models, topology, persistence

- [backend/simulation/models.py](../backend/simulation/models.py)
  `TopologySpec`, `SimulationConfig`, `RuleSnapshot`, `SimulationSnapshot`, `SimulationStateData`
- [backend/simulation/topology.py](../backend/simulation/topology.py)
  Public compatibility façade for topology types and board builders.
- [backend/simulation/topology_types.py](../backend/simulation/topology_types.py)
  `LatticeCell`, `LatticeTopology`, `SimulationBoard`, regular cell ids, revision hashing.
- [backend/simulation/topology_regular.py](../backend/simulation/topology_regular.py)
  Square, hex, and triangle lattice builders.
- [backend/simulation/topology_specialized.py](../backend/simulation/topology_specialized.py)
  Periodic-face and aperiodic patch conversion helpers.
- [backend/simulation/topology_builders.py](../backend/simulation/topology_builders.py)
  Shared topology assembly and cached `build_topology(...)`.
  Delegates geometry dispatch through the topology implementation registry.
- [backend/simulation/topology_implementation_registry.py](../backend/simulation/topology_implementation_registry.py)
  Internal builder and render dispatch registry.
  Maps each geometry key to a `builder_kind`, `render_kind`, and backend builder entrypoint.
- [backend/simulation/topology_boards.py](../backend/simulation/topology_boards.py)
  `empty_board(...)`, `board_from_states(...)`, `board_from_cells_by_id(...)`
- [backend/simulation/rule_context.py](../backend/simulation/rule_context.py)
  Public compatibility façade for rule-context frames and queries.
- [backend/simulation/rule_context_frames.py](../backend/simulation/rule_context_frames.py)
  `TopologyFrame`, frame cache, and `topology_frame_for(...)`.
- [backend/simulation/rule_context_queries.py](../backend/simulation/rule_context_queries.py)
  `RuleContext`, `NeighborSelection`, `build_rule_contexts_for_board(...)`.
- [backend/simulation/persistence.py](../backend/simulation/persistence.py)
  `SimulationStateStore`
- [backend/simulation/state_restore.py](../backend/simulation/state_restore.py)
  `SimulationStateRestorer`
- [backend/simulation/persistence_coordinator.py](../backend/simulation/persistence_coordinator.py)
  Debounced save scheduling.
- [backend/simulation/transition_planner.py](../backend/simulation/transition_planner.py)
  Pure transition planning for reset, config, and restore.

### Topology catalog and generated tilings

- [backend/simulation/topology_catalog.py](../backend/simulation/topology_catalog.py)
  Public topology catalog façade.
- [backend/simulation/topology_catalog_data.py](../backend/simulation/topology_catalog_data.py)
  Static topology definitions.
- [backend/simulation/topology_catalog_types.py](../backend/simulation/topology_catalog_types.py)
  Catalog dataclasses and definition types.
- [backend/simulation/topology_catalog_build.py](../backend/simulation/topology_catalog_build.py)
  Catalog assembly.
- [backend/simulation/topology_catalog_queries.py](../backend/simulation/topology_catalog_queries.py)
  Serialization helpers.
- [backend/simulation/periodic_face_tilings.py](../backend/simulation/periodic_face_tilings.py)
  Periodic mixed-face tiling descriptors and generated cells.
- [backend/simulation/penrose.py](../backend/simulation/penrose.py)
  Penrose patch builder.
- [backend/simulation/aperiodic_prototiles.py](../backend/simulation/aperiodic_prototiles.py)
  Public aperiodic patch facade and Penrose P3 conversion path.
- [backend/simulation/aperiodic_support.py](../backend/simulation/aperiodic_support.py)
  Shared aperiodic patch dataclasses, affine math, polygon helpers, and neighbor reconstruction.
- [backend/simulation/aperiodic_substitution.py](../backend/simulation/aperiodic_substitution.py)
  Reusable substitution-recipe helper for recursive affine expansion, structured substitution nodes, metadata propagation, and deterministic leaf flattening.
- [backend/simulation/aperiodic_registry.py](../backend/simulation/aperiodic_registry.py)
  Registry-backed dispatch for family-specific aperiodic builders and recipe styles.
- [backend/simulation/literature_reference_specs.py](../backend/simulation/literature_reference_specs.py)
  Source-backed reference specs for literature-faithfulness verification of the full topology catalog.
- [backend/simulation/literature_reference_verification.py](../backend/simulation/literature_reference_verification.py)
  Verifier that compares canonical regular, periodic, and aperiodic topology samples against source-backed invariants, and checks the exact-affine Pinwheel path.
- [backend/simulation/aperiodic_golden_triangles.py](../backend/simulation/aperiodic_golden_triangles.py)
  Shared golden-triangle geometry and metadata helpers for Robinson and Tuebingen families.
- [backend/simulation/aperiodic_penrose_p2.py](../backend/simulation/aperiodic_penrose_p2.py)
- [backend/simulation/aperiodic_ammann_beenker.py](../backend/simulation/aperiodic_ammann_beenker.py)
- [backend/simulation/aperiodic_spectre.py](../backend/simulation/aperiodic_spectre.py)
- [backend/simulation/aperiodic_taylor_socolar.py](../backend/simulation/aperiodic_taylor_socolar.py)
- [backend/simulation/aperiodic_sphinx.py](../backend/simulation/aperiodic_sphinx.py)
- [backend/simulation/aperiodic_hat.py](../backend/simulation/aperiodic_hat.py)
- [backend/simulation/aperiodic_tuebingen_triangle.py](../backend/simulation/aperiodic_tuebingen_triangle.py)
- [backend/simulation/aperiodic_dodecagonal_square_triangle.py](../backend/simulation/aperiodic_dodecagonal_square_triangle.py)
- [backend/simulation/aperiodic_shield.py](../backend/simulation/aperiodic_shield.py)
- [backend/simulation/aperiodic_pinwheel.py](../backend/simulation/aperiodic_pinwheel.py)
  Family-specific aperiodic patch builders, including Spectre, the Taylor-Socolar half-hex factor, Sphinx, Hat, Tuebingen Triangle, Dodecagonal Square-Triangle, Shield, and Pinwheel. Pinwheel uses the exact-record helper path in `aperiodic_support.py`; the other rebuilt families still emit the standard polygon patch format.

### Rules

- [backend/rules/__init__.py](../backend/rules/__init__.py)
  `RuleRegistry`
- [backend/rules/base.py](../backend/rules/base.py)
  `AutomatonRule`, `CellStateDefinition`
- [backend/rules/life_like.py](../backend/rules/life_like.py)
  Shared binary and kind-aware Life helpers.
- Concrete rules:
  - [backend/rules/conway.py](../backend/rules/conway.py)
  - [backend/rules/highlife.py](../backend/rules/highlife.py)
  - [backend/rules/hexlife.py](../backend/rules/hexlife.py)
  - [backend/rules/trilife.py](../backend/rules/trilife.py)
  - [backend/rules/kagome_life.py](../backend/rules/kagome_life.py)
  - [backend/rules/archlife488.py](../backend/rules/archlife488.py)
  - [backend/rules/archlife_extended.py](../backend/rules/archlife_extended.py)
  - [backend/rules/wireworld.py](../backend/rules/wireworld.py)
  - [backend/rules/whirlpool.py](../backend/rules/whirlpool.py)
  - [backend/rules/penrose_greenberg_hastings.py](../backend/rules/penrose_greenberg_hastings.py)

## Tests And Tooling

### Tests

- [tests/api](../tests/api)
  API contract and route coverage.
- [tests/unit](../tests/unit)
  Backend service, topology, persistence, validation, and frontend-support unit tests.
- [tests/e2e](../tests/e2e)
  Playwright-backed browser coverage for both server and standalone runtimes.

### Tooling

- [tools/build-standalone.mjs](../tools/build-standalone.mjs)
  Builds the static standalone site.
- [tools/run-playwright.mjs](../tools/run-playwright.mjs)
  Local Playwright runner used by npm scripts. It prepares Linux browser runtime libraries when needed, builds standalone output for standalone suites, and dispatches Python `unittest` modules.
- [tools/run-python.mjs](../tools/run-python.mjs)
  Cross-platform Python command wrapper used by npm scripts for repo tools.
- [tools/validate_tilings.py](../tools/validate_tilings.py)
  Manifest-wide geometric sanity checker for catalog tilings. Prints a reminder to run the literature verifier for the full catalog companion checks.
- [tools/verify_reference_tilings.py](../tools/verify_reference_tilings.py)
  Literature-faithfulness verifier for the full topology catalog. Reports `PASS`, `KNOWN_DEVIATION`, or `FAIL` without changing the public app surface.
- [tools/render_standalone_shell.py](../tools/render_standalone_shell.py)
  Writes the standalone wrapper into the transient build-input directory.
- [tools/export_bootstrap_data.py](../tools/export_bootstrap_data.py)
  Exports bootstrap metadata for standalone mode.
- [tools/validate_tilings.py](../tools/validate_tilings.py)
  Validates topology descriptors and generated tilings.
- [vite.config.ts](../vite.config.ts)
  Frontend build configuration.

## Current Refactor Targets

Use this list to decide where cleanup work should start. These are the files with the most structural pressure today, not necessarily the files with the most defects.

- Frontend gesture orchestration:
  [surface-bindings.ts](../frontend/interactions/surface-bindings.ts),
  [legacy-drag.ts](../frontend/interactions/legacy-drag.ts),
  [editor-session.ts](../frontend/interactions/editor-session.ts),
  [command-dispatch.ts](../frontend/interactions/command-dispatch.ts)
- Canvas transient overlays:
  [canvas-view.ts](../frontend/canvas-view.ts),
  [render-layers.ts](../frontend/canvas/render-layers.ts),
  [render-style.ts](../frontend/canvas/render-style.ts)
- Drawer metadata and inspector modeling:
  [drawer.ts](../frontend/controls-model/drawer.ts),
  [view-sections.ts](../frontend/controls/view-sections.ts),
  [app-view.ts](../frontend/app-view.ts)
- Aperiodic implementation quality:
  [aperiodic_registry.py](../backend/simulation/aperiodic_registry.py),
  [aperiodic_substitution.py](../backend/simulation/aperiodic_substitution.py),
  [aperiodic_support.py](../backend/simulation/aperiodic_support.py),
  [aperiodic_shield.py](../backend/simulation/aperiodic_shield.py)
- Literature verification size and ownership:
  [literature_reference_specs.py](../backend/simulation/literature_reference_specs.py),
  [literature_reference_verification.py](../backend/simulation/literature_reference_verification.py)
- Frontend/backend contract drift:
  [types/domain.d.ts](../frontend/types/domain.d.ts),
  [types/controller-api.d.ts](../frontend/types/controller-api.d.ts),
  [payload_types.py](../backend/payload_types.py),
  [contract_validation.py](../backend/contract_validation.py)

## If You Want To Change...

- HTTP endpoint behavior:
  Start with [backend/web/routes.py](../backend/web/routes.py) and [backend/web/state_actions.py](../backend/web/state_actions.py)
- Simulation transitions or board mutation:
  Start with [backend/simulation/service.py](../backend/simulation/service.py) and [backend/simulation/service_transitions.py](../backend/simulation/service_transitions.py)
- Rule logic:
  Start with [backend/rules/base.py](../backend/rules/base.py) and the concrete rule file under [backend/rules](../backend/rules)
- Topology generation:
  Start with [backend/simulation/topology.py](../backend/simulation/topology.py), [backend/simulation/topology_builders.py](../backend/simulation/topology_builders.py), and [backend/simulation/topology_catalog.py](../backend/simulation/topology_catalog.py)
- Canvas rendering:
  Start with [frontend/canvas/render-layers.ts](../frontend/canvas/render-layers.ts), [frontend/canvas/render-style.ts](../frontend/canvas/render-style.ts), and the relevant adapter under [frontend/geometry](../frontend/geometry)
- Control UI:
  Start with [frontend/controls-model.ts](../frontend/controls-model.ts), [frontend/controls-view.ts](../frontend/controls-view.ts), and [frontend/controls-bindings.ts](../frontend/controls-bindings.ts)
- Editor behavior:
  Start with [frontend/interactions/editor-session.ts](../frontend/interactions/editor-session.ts), [frontend/editor-operation-builders.ts](../frontend/editor-operation-builders.ts), and [frontend/editor-history.ts](../frontend/editor-history.ts)
- Standalone browser runtime:
  Start with [frontend/standalone.ts](../frontend/standalone.ts), [frontend/standalone/worker-client.ts](../frontend/standalone/worker-client.ts), and [backend/browser_runtime.py](../backend/browser_runtime.py)
- Shared shell or startup wrappers:
  Start with [frontend/shell/app-shell-body.html](../frontend/shell/app-shell-body.html), [backend/app_shell.py](../backend/app_shell.py), and [tools/render_standalone_shell.py](../tools/render_standalone_shell.py)
