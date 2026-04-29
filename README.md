# Cellular Automaton Lab

Cellular Automaton Lab is a browser-based cellular automata playground built around topology-first boards. It supports classic lattices, periodic mixed tilings, and finite aperiodic patches in one app, with a Flask backend and a Vite-built TypeScript frontend.

Live standalone demo: [https://grgs.github.io/cellular-automaton-lab/](https://grgs.github.io/cellular-automaton-lab/)

![Current canvas-first workspace on a Kagome mixed-tiling board](docs/images/readme-workspace-kagome.png)

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

## What Makes It Different

- The simulation model is topology-first, not grid-first.
- The backend is authoritative; the browser renders snapshots and sends explicit mutations.
- Regular, mixed periodic, and aperiodic boards share one rule protocol and one editing workflow.
- Pattern files use sparse `cells_by_id` payloads instead of dense grid-only formats.

Architecture details live in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). A runtime-oriented source guide lives in [docs/CODE_MAP.md](docs/CODE_MAP.md). Maintenance and guardrail ownership lives in [docs/MAINTENANCE.md](docs/MAINTENANCE.md).

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
py -3 -m unittest discover -s tests -p "test_*.py"
```

Explicit Playwright runs:

```powershell
py -3 -m unittest -v tests.e2e.test_playwright_all
py -3 -m unittest -v tests.e2e.test_playwright_suite_integrity
```

### Browser diagnosis

Use the render-review tool when the question is what the current canvas output actually looks like:

```powershell
python tools/render_canvas_review.py --profile pinwheel-depth-3
python tools/render_canvas_review.py --profile pinwheel-depth-3 --literature-review
```

Use the managed runner when you need owned startup, cleanup, logs, and artifacts around a focused browser check:

```powershell
python tools/run_browser_check.py --host standalone --render-review --profile pinwheel-depth-3
python tools/run_browser_check.py --host standalone --render-review --profile pinwheel-depth-3 --literature-review
python tools/run_browser_check.py --host server --success-artifacts --unittest tests.e2e.playwright_case_suite.CellularAutomatonUITests.test_pinwheel_topology_switch_renders_aperiodic_patch
```

Use the sweep tool when the question is comparative rather than single-run:

```powershell
python tools/run_render_review_sweep.py --profile pinwheel-depth-3 --patch-depths 3,4 --hosts standalone,server
python tools/run_render_review_sweep.py --profile pinwheel-depth-3 --patch-depths 3,4 --hosts standalone,server --literature-review
```

Use the diff-review tool when you want one artifact that compares a sweep:

```powershell
python tools/run_render_review_diff.py --profile pinwheel-depth-3 --patch-depths 3,4 --hosts standalone,server
python tools/run_render_review_diff.py --sweep-manifest output/render-review-sweeps/<run>/sweep-manifest.json
```

The shared implementation for those commands lives in `tools/render_review/`. The top-level scripts remain the stable CLI entrypoints.

If you need to inspect or clear repo-owned browser/server helper processes directly:

```powershell
python tools/dev_processes.py list
python tools/dev_processes.py kill --stale-browser-hosts
```

The render-review tool is the preferred visual-inspection path. The managed runner is the preferred direct-debug path when host lifecycle ownership matters. The sweep tool is the preferred small-matrix comparison path. The diff-review tool is the preferred way to turn a sweep into one HTML/PNG comparison sheet. The process helper is the narrow cleanup fallback. Full browser suites should still go through the npm Playwright entrypoints.

Literature review is metadata-first: the repo stores citations and review notes in profiles, not literature images. If you want a literature montage, place an operator-provided image in `output/literature-reference-cache/` or pass `--reference /abs/path/to/image`.

## Repository Layout

- `app.py`: local app entrypoint
- `backend/`: Flask app, simulation engine, rules, topology catalog, persistence, and API routes
- `frontend/`: authored TypeScript frontend source
- `static/css/`: authored styles
- `static/dist/`: generated frontend build output
- `templates/`: HTML shell
- `tests/`: backend, API, integration, and browser coverage
- `tools/`: validation and profiling helpers
