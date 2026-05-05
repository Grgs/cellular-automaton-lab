# Cellular Automaton Lab

Cellular Automaton Lab is a browser-based cellular automata playground built around topology-first boards. It supports classic lattices, periodic mixed tilings, and finite aperiodic patches in one app, with a Flask backend and a Vite-built TypeScript frontend.

Public release status: `v0.1.0` preview. This repo's first public release is a tagged GitHub source release plus the standalone GitHub Pages demo below. It is usable today, but it is not positioned as a long-term API or feature-stability promise yet.

Live standalone demo: [https://grgs.github.io/cellular-automaton-lab/](https://grgs.github.io/cellular-automaton-lab/)

![Current canvas-first workspace on a Kagome mixed-tiling board](docs/images/readme-workspace-kagome.png)

## Project Scope

This project explores cellular automata on rectangular and non-rectangular boards. The rule engine, editor, renderer, and pattern format are organized around topology data so the same app workflow can run on square grids, hex grids, mixed periodic tilings, and finite aperiodic patches.

It is intended for comparing how familiar automata behave on different local neighborhoods, testing topology and rendering ideas, and saving sparse patterns by stable cell IDs rather than lattice-specific grid coordinates.

## Highlights

- 15 tiling families across square, hex, triangle, Archimedean, Cairo, Penrose, and Ammann-Beenker boards
- 16 built-in rules spanning Life-like, mixed-tiling, excitable, and signal systems
- one shared `next_state(ctx)` rule protocol across all shipped topologies
- canvas-first editing with brush, line, rectangle, fill, undo/redo, presets, and pattern import/export
- sparse pattern persistence keyed by stable topology cell IDs
- TypeScript frontend in `frontend/` with Vitest unit tests and Playwright browser coverage

## Screenshots

### Snub Trihexagonal mixed-tiling board with the inspector open

![Snub Trihexagonal mixed Life](docs/images/readme-snub-trihexagonal-overview.png)

### Square board with Conway after several generations

![Square board with evolved Conway patterns](docs/images/readme-workspace-conway.png)

### Penrose P3 Rhombs with patch-depth controls

![Penrose P3 Rhombs overview](docs/images/readme-penrose-p3-overview.png)

## Suggested Demo Flows

- Start with Square + Conway, paint a few cells, use step/run, then export or copy the pattern to see the sparse `cells_by_id` format.
- Switch to Kagome or `4.8.8`, choose the matching mixed-tiling Life rule, and open the inspector while painting to see the same editor workflow on non-square neighborhoods.
- Switch to Penrose P3 Rhombs, Spectre, or Taylor-Socolar, adjust patch depth, and watch how a finite aperiodic patch remains editable and persistent.
- Try Whirlpool or HexWhirlpool from the preset/showcase controls for a quick multi-state animation that exercises more than binary Life-like states.
- Reload the standalone GitHub Pages demo after changing topology or state to check browser persistence without the Flask server.

## Implementation Notes

- The simulation model is topology-first: rules evaluate cells through a neighbor context rather than direct grid indexing.
- The backend owns canonical simulation state; the browser renders snapshots and sends explicit mutations.
- Regular, mixed periodic, and aperiodic boards share the same rule protocol and editing workflow.
- Pattern files use sparse `cells_by_id` payloads instead of dense grid-only formats.
- The topology catalog connects backend builders, frontend render adapters, patch-depth sizing policy, default rules, picker metadata, and standalone bootstrap data.
- Aperiodic families are represented as deterministic finite patches with stable IDs and metadata, using the same snapshot, persistence, and canvas-hit-testing path as regular grids.
- The standalone build runs the Python simulation stack in a browser worker through Pyodide, so server and static-host demos share the same backend model.

Architecture details live in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). A runtime-oriented source guide lives in [docs/CODE_MAP.md](docs/CODE_MAP.md). Maintenance and guardrail ownership lives in [docs/MAINTENANCE.md](docs/MAINTENANCE.md).

## Developer Guides

- [Adding rules](docs/ADDING_RULES.md)
- [Adding topologies](docs/ADDING_TOPOLOGIES.md)
- [Adding presets and patterns](docs/ADDING_PRESETS_AND_PATTERNS.md)
- [Choosing tests for changes](docs/TESTING_CHANGES.md)

## Useful Files To Inspect

- [backend/simulation/engine.py](backend/simulation/engine.py): pure stepping loop that applies the active rule to each topology cell.
- [backend/simulation/models.py](backend/simulation/models.py): core board, topology, snapshot, and rule-context data shapes.
- [backend/simulation/topology_catalog.py](backend/simulation/topology_catalog.py) and [backend/simulation/topology_implementation_registry.py](backend/simulation/topology_implementation_registry.py): catalog metadata and builder/render dispatch.
- [backend/simulation/aperiodic_registry.py](backend/simulation/aperiodic_registry.py): aperiodic patch family dispatch.
- [backend/rules/base.py](backend/rules/base.py) and [backend/rules](backend/rules): the shared rule protocol and built-in rules.
- [backend/web/routes.py](backend/web/routes.py) and [backend/web/state_actions.py](backend/web/state_actions.py): HTTP mutation boundary.
- [frontend/app-controller.ts](frontend/app-controller.ts), [frontend/app-actions.ts](frontend/app-actions.ts), and [frontend/simulation-reconciler.ts](frontend/simulation-reconciler.ts): frontend orchestration around canonical snapshots.
- [frontend/canvas-view.ts](frontend/canvas-view.ts), [frontend/geometry/registry.ts](frontend/geometry/registry.ts), and [frontend/canvas/render-layers.ts](frontend/canvas/render-layers.ts): canvas rendering and topology-specific geometry adapters.
- [frontend/pattern-io.ts](frontend/pattern-io.ts): sparse pattern import/export format.

## Release Surface

The public `v0.1.0` preview ships through three surfaces:

- tagged GitHub source releases
- the GitHub Pages standalone demo
- local source checkout for development and self-hosted use

This release does not publish an npm package or a PyPI package. The repository is the install and integration surface for now.

## Preview Status And Known Limitations

The current preview is available for public evaluation, local experimentation, and contribution, but some families and verification targets are still documented as provisional.

- `pinwheel` remains labeled `Experimental` because manual visible review still does not justify promotion, even though automated checks now pass.
- `dodecagonal-square-triangle` is currently implemented as a decorated `3.12.12` Archimedean generator rather than the canonical Schlottmann quasi-periodic square-triangle tiling.
- The standalone GitHub Pages demo targets static hosting with network access and still loads Pyodide from a CDN rather than bundling it for offline use.

The canonical list of known mathematical and rendering deviations lives in [docs/TILING_KNOWN_DEVIATIONS.md](docs/TILING_KNOWN_DEVIATIONS.md). Active follow-up work lives in [TODO.md](TODO.md).

## Intentional Non-Goals For This Preview

- No npm or PyPI package is published; the source repo and standalone demo are the release surface.
- No public plugin or extension API is promised yet.
- No separate JavaScript simulation engine is maintained for the standalone demo; the browser runtime reuses the Python backend through Pyodide.
- No full offline standalone bundle is shipped yet because Pyodide still loads from a CDN.
- No claim is made that every aperiodic family is a complete symbolic or literature-canonical construction; weaker or provisional cases are documented in the tiling deviation notes.

## Included Rules

- Life-like: `conway`, `highlife`, `life-b2-s23`, `hexlife`, `trilife`
- Mixed-tiling Life: `archlife488`, `archlife-3-12-12`, `archlife-3-4-6-4`, `archlife-4-6-12`, `archlife-3-3-4-3-4`, `archlife-3-3-3-4-4`, `archlife-3-3-3-3-6`, `kagome-life`
- Excitable: `penrose-greenberg-hastings`, `whirlpool`
- Signal/circuit: `wireworld`

## Running Locally

1. Install Python dependencies:

```powershell
py -3 -m pip install -r requirements.txt
```

2. Install frontend dependencies:

```powershell
npm install
```

3. Build the frontend bundle:

```powershell
npm run build:frontend
```

4. Start the app:

```powershell
py -3 .\app.py
```

5. Open [http://127.0.0.1:5000](http://127.0.0.1:5000)

The server respects `HOST`, `PORT`, and `APP_INSTANCE_PATH`. If `static/dist/manifest.json` is missing, startup fails with a message telling you to run `npm run build:frontend`.

## Frontend Workflow

The authored frontend source lives in `frontend/`. Vite builds hashed runtime assets and `manifest.json` into `static/dist/`, and Flask resolves those assets when it renders the page.

Common frontend commands:

```powershell
npm run lint:frontend
npm run format:frontend:check
npm run typecheck:frontend
npm run test:frontend
npm run build:frontend
```

During active frontend work:

```powershell
npm run dev:frontend
```

## Tests

Install dev dependencies and browser support:

```powershell
py -3 -m pip install -r requirements-dev.txt
py -3 -m playwright install chromium
```

Frontend checks:

```powershell
npm run lint:frontend
npm run format:frontend:check
npm run typecheck:frontend
npm run test:frontend
npm run build:frontend
```

Backend and integration checks:

```powershell
npm run check:python
py -3 -m mypy --config-file mypy.ini
py -3 .\tools\validate_tilings.py
py -3 .\tools\verify_reference_tilings.py
py -3 -m unittest discover -s tests -p "test_*.py"
```

Explicit Playwright runs:

```powershell
py -3 -m unittest -v tests.e2e.test_playwright_all
py -3 -m unittest -v tests.e2e.test_playwright_suite_integrity
```

For release confidence, also run:

```powershell
npm run build:frontend:standalone
npm run smoke:standalone
npm run check:doc-links
npm run audit:supply-chain
py -3 -m pre_commit run --hook-stage pre-push --all-files
```

### Browser diagnosis

For focused visual inspection, sweep matrices, diff sheets, and managed browser-host runs, see the "Browser Diagnosis And Failure Investigation" section of [docs/TESTING.md](docs/TESTING.md). Full browser suites still go through the npm Playwright entrypoints above.

### Correctness-Oriented Tests To Inspect

- [tests/unit/test_simulation_engine.py](tests/unit/test_simulation_engine.py): compares optimized stepping against reference rule-context evaluation across regular and mixed tilings.
- [tests/unit/test_simulation_topology.py](tests/unit/test_simulation_topology.py), [tests/unit/test_simulation_topology_aperiodic.py](tests/unit/test_simulation_topology_aperiodic.py), and [tests/unit/test_topology_validation.py](tests/unit/test_topology_validation.py): cover topology construction and validation invariants.
- [tests/unit/test_literature_reference_verification.py](tests/unit/test_literature_reference_verification.py): checks source-backed reference specs, connectivity, hole counts, deterministic signatures, and pass/fail behavior for the tiling verifier.
- [tests/unit/test_payload_contracts.py](tests/unit/test_payload_contracts.py), [tests/api](tests/api), and [frontend/review-api.test.ts](frontend/review-api.test.ts): guard backend/frontend payload and HTTP mutation contracts.
- [frontend/pattern-io.test.ts](frontend/pattern-io.test.ts), [frontend/presets.test.ts](frontend/presets.test.ts), and [frontend/actions/simulation/topology-selection-plan.test.ts](frontend/actions/simulation/topology-selection-plan.test.ts): exercise frontend parsing, preset, and topology-transition planning logic.
- [tests/e2e/playwright_case_suite.py](tests/e2e/playwright_case_suite.py): drives browser-visible flows for rule selection, topology switching, patch-depth controls, painting, pattern import/export, persistence, and standalone runtime coverage.

## Repository Layout

- `app.py`: local app entrypoint
- `backend/`: Flask app, simulation engine, rules, topology catalog, persistence, and API routes
- `frontend/`: authored TypeScript frontend source
- `static/css/`: authored styles
- `static/dist/`: generated frontend build output
- `templates/`: HTML shell
- `tests/`: backend, API, integration, and browser coverage
- `tools/`: validation and profiling helpers
