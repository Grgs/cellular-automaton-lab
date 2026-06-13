# Cellular Automaton Lab

[![CI](https://github.com/Grgs/cellular-automaton-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/Grgs/cellular-automaton-lab/actions/workflows/ci.yml)
[![Supply Chain Audit](https://github.com/Grgs/cellular-automaton-lab/actions/workflows/supply-chain-audit.yml/badge.svg)](https://github.com/Grgs/cellular-automaton-lab/actions/workflows/supply-chain-audit.yml)
[![Latest release](https://img.shields.io/github/v/release/Grgs/cellular-automaton-lab?label=release)](https://github.com/Grgs/cellular-automaton-lab/releases/latest)
[![License: MIT](https://img.shields.io/github/license/Grgs/cellular-automaton-lab)](LICENSE)
[![Live demo](https://img.shields.io/badge/demo-GitHub%20Pages-0969da)](https://grgs.github.io/cellular-automaton-lab/)

Cellular Automaton Lab is a browser-based cellular automata playground built around topology-first boards. It supports classic lattices, periodic mixed tilings, and finite aperiodic patches in one app, with a Flask backend and a Vite-built TypeScript frontend.

Public release status: `v0.5.0` preview. The preview is usable for public evaluation, local experimentation, and contribution, but it is not a long-term API or feature-stability promise.

Live standalone demo: [https://grgs.github.io/cellular-automaton-lab/](https://grgs.github.io/cellular-automaton-lab/)

**First time here?** [`docs/ONBOARDING.md`](docs/ONBOARDING.md) is a one-page decision tree -- find the row that matches what you want to do (run the app, add a tiling, use the topology library, etc.) and follow the link. The [`examples/`](examples/README.md) directory has short, runnable Python scripts for each major subsystem.

![Compare results showing one acorn seed evaluated across representative tilings](docs/images/readme-compare-results-hero.png)

## Project Scope

This project explores cellular automata on rectangular and non-rectangular boards. The rule engine, editor, renderer, and pattern format are organized around topology data so the same app workflow can run on square grids, hex grids, mixed periodic tilings, and finite aperiodic patches.

It is intended for comparing how familiar automata behave on different local neighborhoods, testing topology and rendering ideas, and saving sparse patterns by stable cell IDs rather than lattice-specific grid coordinates.

## Highlights

- 46 shipped tiling families (3 regular grids, 27 periodic mixed tilings, 16 aperiodic patches including Penrose variants and monotiles)
- 16 built-in rules spanning Life-like, mixed-tiling, excitable, and signal systems
- one shared `next_state(ctx)` rule protocol across all shipped topologies
- canvas-first editing with brush, line, rectangle, fill, undo/redo, presets, and pattern import/export
- compare-mode overlay that runs one seed across many tilings, charts how topology shapes the outcome, and opens begin/end states as shareable board links (also scriptable via `python -m tools tilings compare`)
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
- Compare `Penrose P1 Pentagon-Diamond (Distributed)` with `Penrose P1 Pentagon-Boat-Star` to see the difference between the distributed vertex-merge manifestation and the centered singular pentagrid patch.
- Try the convex pentagonal periodic catalog with Cairo, Prismatic, Floret, Type 7, Stein 14, and Pentagon Crosses to compare how the same rule family behaves on distinct pentagon adjacencies.
- Try Whirlpool or HexWhirlpool from the preset/showcase controls for a quick multi-state animation that exercises more than binary Life-like states.
- Reload the standalone GitHub Pages demo after changing topology or state to check browser persistence without the Flask server.

## How It Works

- The simulation model is topology-first: rules evaluate cells through a neighbor context rather than direct grid indexing.
- The backend owns canonical simulation state; the browser renders snapshots and sends explicit mutations.
- Regular, mixed periodic, and aperiodic boards share the same rule protocol and editing workflow.
- Pattern files use sparse `cells_by_id` payloads instead of dense grid-only formats.
- The standalone build runs the Python simulation stack in a browser worker through Pyodide, so server and static-host demos share the same backend model.

For deeper orientation, start with:

- [Architecture](docs/ARCHITECTURE.md) for runtime boundaries and subsystem ownership
- [Code map](docs/CODE_MAP.md) for file-level navigation and call paths
- [Contributing](CONTRIBUTING.md) for setup, common commands, and contribution expectations
- [Maintenance](docs/MAINTENANCE.md) for guardrails, release process, and doc ownership

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

## Common Checks

The canonical "what to run" list lives in [`docs/ONBOARDING.md`](docs/ONBOARDING.md#run-tests). At a glance:

```powershell
npm run check:frontend     # frontend lint + build + vitest
npm run check:python       # ruff lint + ruff format check + mypy
npm run check:ci-local     # the broad local-CI sweep
```

For choosing narrower checks by change type, see [Testing changes](docs/TESTING_CHANGES.md). For the full strategy, browser diagnostics, and the release-confidence sweep, see [Testing strategy](docs/TESTING.md) and [Maintenance](docs/MAINTENANCE.md#public-release-process).

## Developer Guides

- [Adding rules](docs/ADDING_RULES.md)
- [Adding topologies](docs/ADDING_TOPOLOGIES.md)
- [Adding presets and patterns](docs/ADDING_PRESETS_AND_PATTERNS.md)
- [Choosing tests for changes](docs/TESTING_CHANGES.md)
- [Tools reference](docs/TOOLS.md)

## Release Surface

The public `v0.5.0` preview ships through three surfaces:

- tagged GitHub source releases
- the GitHub Pages standalone demo
- local source checkout for development and self-hosted use

This release does not publish an npm package or a PyPI package. The repository is the install and integration surface for now.

## Preview Status And Known Limitations

- `pinwheel-2-1` remains labeled `Experimental` until manual visual review accepts its exact-affine implementation; the single-prototile `pinwheel` was promoted to the main `Aperiodic` group on June 12, 2026 after a review of the corrected congruent patch.
- `dodecagonal-square-triangle` is currently implemented as a decorated `3.12.12` Archimedean generator rather than the canonical Schlottmann quasi-periodic square-triangle tiling.
- The standalone GitHub Pages demo targets static hosting with network access and still loads Pyodide from a CDN rather than bundling it for offline use.

The canonical list of known mathematical and rendering deviations lives in [docs/TILING_KNOWN_DEVIATIONS.md](docs/TILING_KNOWN_DEVIATIONS.md). Active follow-up work lives in [TODO.md](TODO.md).

## Intentional Non-Goals For This Preview

- No npm or PyPI package is published; the source repo and standalone demo are the release surface.
- No public plugin or extension API is promised yet.
- No separate JavaScript simulation engine is maintained for the standalone demo; the browser runtime reuses the Python backend through Pyodide.
- No full offline standalone bundle is shipped yet because Pyodide still loads from a CDN.
- No claim is made that every aperiodic family is a complete symbolic or literature-canonical construction; weaker or provisional cases are documented in the tiling deviation notes.

## Repository Layout

- `app.py`: local app entrypoint
- `backend/`: Flask app, simulation engine, rules, topology catalog, persistence, and API routes
- `frontend/`: authored TypeScript frontend source
- `static/css/`: authored styles
- `static/dist/`: generated frontend build output
- `templates/`: HTML shell
- `tests/`: backend, API, integration, and browser coverage
- `tools/`: validation, build, diagnosis, and profiling helpers
