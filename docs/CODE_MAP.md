# Code Map

This is a runtime-focused map of the app. It is meant to answer two questions quickly:

1. Where does the app start in server mode and standalone mode?
2. Which files and functions should you follow for a given kind of change?

For the higher-level architecture, see [ARCHITECTURE.md](./ARCHITECTURE.md).

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

1. [standalone.html](../standalone.html)
   Static HTML shell for the standalone build.
2. [frontend/standalone.ts](../frontend/standalone.ts)
   `startStandaloneApp()` loads bootstrap JSON, creates the standalone worker environment, and then calls `initApp(...)`.
3. [frontend/standalone/worker-client.ts](../frontend/standalone/worker-client.ts)
   `createStandaloneEnvironment(...)` creates the Web Worker, talks to Pyodide, and exposes a `SimulationBackend`.
4. [frontend/standalone-worker.ts](../frontend/standalone-worker.ts)
   Worker entrypoint that loads Python and forwards commands into the browser runtime host.
5. [backend/browser_runtime.py](../backend/browser_runtime.py)
   Python runtime host for standalone mode. Exposes `initialize_runtime(...)`, `handle_request(...)`, and `tick_running()`.

### Browser UI startup

1. [frontend/main.ts](../frontend/main.ts)
   `initApp(...)` creates the top-level controller and marks the app ready.
2. [frontend/app-controller.ts](../frontend/app-controller.ts)
   `createAppController(...)` composes state, view, actions, sync, and interactions.
3. [frontend/app-controller-startup.ts](../frontend/app-controller-startup.ts)
   `initializeAppController(...)` runs the async startup flow.
4. [frontend/app-actions.ts](../frontend/app-actions.ts)
   Creates the action surface used by controls and interaction handlers.
5. [frontend/app-view.ts](../frontend/app-view.ts)
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

- [frontend/main.ts](../frontend/main.ts)
  `initApp(...)`, `disposeApp()`
- [frontend/app-controller.ts](../frontend/app-controller.ts)
  `createAppController(...)`
- [frontend/app-controller-startup.ts](../frontend/app-controller-startup.ts)
  `initializeAppController(...)`
- [frontend/app-controller-sync.ts](../frontend/app-controller-sync.ts)
  `createAppControllerSync(...)`
- [frontend/app-controller-bootstrap.ts](../frontend/app-controller-bootstrap.ts)
  `createAppControllerBootstrap(...)`, `createViewportControllerDependencies(...)`
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
- [frontend/actions/simulation/index.ts](../frontend/actions/simulation/index.ts)
  `createSimulationActions(...)`
- [frontend/actions/simulation/run-actions.ts](../frontend/actions/simulation/run-actions.ts)
  Start, pause, resume, step actions.
- [frontend/actions/simulation/rule-actions.ts](../frontend/actions/simulation/rule-actions.ts)
  Rule changes.
- [frontend/actions/simulation/topology-actions.ts](../frontend/actions/simulation/topology-actions.ts)
  Topology changes.
- [frontend/actions/preset-actions.ts](../frontend/actions/preset-actions.ts)
  Applies built-in seed presets.
- [frontend/actions/pattern-actions.ts](../frontend/actions/pattern-actions.ts)
  Import/export/copy/paste pattern actions.
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
  `LatticeCell`, `LatticeTopology`, `SimulationBoard`, `build_topology(...)`
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
- [backend/simulation/topology_catalog_build.py](../backend/simulation/topology_catalog_build.py)
  Catalog assembly.
- [backend/simulation/topology_catalog_queries.py](../backend/simulation/topology_catalog_queries.py)
  Serialization helpers.
- [backend/simulation/periodic_face_tilings.py](../backend/simulation/periodic_face_tilings.py)
  Periodic mixed-face tiling descriptors and generated cells.
- [backend/simulation/penrose.py](../backend/simulation/penrose.py)
  Penrose patch builder.
- [backend/simulation/aperiodic_prototiles.py](../backend/simulation/aperiodic_prototiles.py)
  Ammann-Beenker and Penrose prototile patch builders.

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
- [tools/export_bootstrap_data.py](../tools/export_bootstrap_data.py)
  Exports bootstrap metadata for standalone mode.
- [tools/validate_tilings.py](../tools/validate_tilings.py)
  Validates topology descriptors and generated tilings.
- [vite.config.ts](../vite.config.ts)
  Frontend build configuration.

## If You Want To Change...

- HTTP endpoint behavior:
  Start with [backend/web/routes.py](../backend/web/routes.py) and [backend/web/state_actions.py](../backend/web/state_actions.py)
- Simulation transitions or board mutation:
  Start with [backend/simulation/service.py](../backend/simulation/service.py) and [backend/simulation/service_transitions.py](../backend/simulation/service_transitions.py)
- Rule logic:
  Start with [backend/rules/base.py](../backend/rules/base.py) and the concrete rule file under [backend/rules](../backend/rules)
- Topology generation:
  Start with [backend/simulation/topology.py](../backend/simulation/topology.py), [backend/simulation/topology_catalog.py](../backend/simulation/topology_catalog.py), and [backend/simulation/periodic_face_tilings.py](../backend/simulation/periodic_face_tilings.py)
- Canvas rendering:
  Start with [frontend/canvas/render-layers.ts](../frontend/canvas/render-layers.ts), [frontend/canvas/render-style.ts](../frontend/canvas/render-style.ts), and the relevant adapter under [frontend/geometry](../frontend/geometry)
- Control UI:
  Start with [frontend/controls-model.ts](../frontend/controls-model.ts), [frontend/controls-view.ts](../frontend/controls-view.ts), and [frontend/controls-bindings.ts](../frontend/controls-bindings.ts)
- Editor behavior:
  Start with [frontend/interactions/editor-session.ts](../frontend/interactions/editor-session.ts), [frontend/editor-operation-builders.ts](../frontend/editor-operation-builders.ts), and [frontend/editor-history.ts](../frontend/editor-history.ts)
- Standalone browser runtime:
  Start with [frontend/standalone.ts](../frontend/standalone.ts), [frontend/standalone/worker-client.ts](../frontend/standalone/worker-client.ts), and [backend/browser_runtime.py](../backend/browser_runtime.py)
