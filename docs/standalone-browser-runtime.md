# Standalone Browser Runtime

This repository now supports two runtime hosts for the same UI:

- `server` mode keeps the existing Flask + HTTP architecture.
- `standalone` mode runs the Python simulation inside a Web Worker using Pyodide and serves the frontend as static assets from `output/standalone/`.

The current standalone target is normal static hosting with network access. Pyodide is still loaded from a CDN, so this is browser-local execution rather than a fully offline bundle.

The public evaluator demo is published to GitHub Pages at [https://grgs.github.io/cellular-automaton-lab/](https://grgs.github.io/cellular-automaton-lab/).

The first public release line is a `v0.1.x` preview series: tagged GitHub source release plus this GitHub Pages demo, without npm or PyPI packaging.

## Architecture Overview

### Server mode

- Flask still renders `templates/index.html`.
- `templates/index.html` now wraps the shared shell source from `frontend/shell/app-shell-body.html` instead of duplicating the full app body.
- The frontend uses the HTTP-backed `SimulationBackend` from `frontend/api.ts`.
- Server bootstrap data is available through both template globals and `GET /api/bootstrap`.
- The backend remains authoritative for state, persistence, and the threaded run loop.
- HTTP request extraction stays in Flask, but payload normalization and persisted snapshot validation now live in the shared backend contract layer in `backend/contract_validation.py`.

### Standalone mode

- The standalone build stages a transient `standalone.html` input from the same shared shell source that the server wrapper uses, so the large DOM shell is defined in one place without a checked-in wrapper file.
- `frontend/standalone.ts` fetches `standalone-bootstrap.json`, installs the bootstrap globals first, then dynamically imports the shared app runtime so standalone startup no longer races bootstrapped window data.
- `frontend/standalone.ts` creates the worker-backed `SimulationBackend` and then starts the shared frontend controller stack.
- `frontend/standalone-worker.ts` loads Pyodide, installs a bundled Python payload into Pyodide's virtual filesystem, imports `backend.browser_runtime`, and proxies frontend commands into the Python simulation runtime.
- The worker owns the standalone run loop with JS timers. The frontend continues to use the existing polling/reconciliation flow while the worker advances the simulation in the background.
- Browser-local persistence uses IndexedDB first and falls back to `localStorage` if IndexedDB is unavailable.
- The standalone worker now uses the same shared command parsing and persisted snapshot acceptance helpers as the Flask route layer.

## Lifecycle Cleanup

- `SimulationBackend` now includes `dispose()`.
- The HTTP backend implements disposal as a no-op.
- The standalone backend terminates the worker, removes its listeners, and rejects pending requests during disposal.
- `AppController` now exposes `dispose()`, and `initApp()` returns the created controller.
- Both server and standalone entrypoints install `pagehide` cleanup so browser teardown and Playwright tests can release the active controller explicitly.

## Build Commands

### Flask-hosted frontend build

```powershell
npm run build:frontend
```

This outputs the Vite manifest and hashed assets to `static/dist/`, which the Flask app consumes on startup.

### Standalone static build

```powershell
npm run build:frontend:standalone
```

This performs five steps:

1. stages a transient standalone build-input directory under `output/`
2. writes a generated `standalone.html` wrapper plus staged `styles.css` and `favicon.svg` into that build-input directory
3. builds the standalone Vite entry into `output/standalone/`
4. exports `standalone-bootstrap.json` from the Python topology/defaults metadata
5. writes `standalone-python-bundle.json`, which contains the standalone Python source/config payload as one bundled JSON file

The standalone output includes both `standalone.html` and `index.html` for easier static hosting.
The packager also writes `.nojekyll` so the published artifact is safe for GitHub Pages project-site hosting.

## Worker Message Contract

The standalone worker uses the protocol defined in `frontend/standalone/protocol.ts`.

### Main thread -> worker

- `init`
  - `requestId`
  - `persistedSnapshot`
  - `pythonBundleUrl`
  - `pyodideBaseUrl`
- `request`
  - `requestId`
  - `path`
  - optional `payload`

The `path` values intentionally match the existing HTTP command surface:

- `/api/state`
- `/api/rules`
- `/api/control/start`
- `/api/control/pause`
- `/api/control/resume`
- `/api/control/step`
- `/api/control/reset`
- `/api/config`
- `/api/cells/toggle`
- `/api/cells/set`
- `/api/cells/set-many`

### Worker -> main thread

- `ready`
  - success shape: `snapshot` and optional `persistedSnapshot`
  - failure shape: `error`
- `response`
  - success shape: `ok: true` plus `snapshot`, `rules`, and/or `persistedSnapshot`
  - failure shape: `ok: false` and `error`
- `persist`
  - emitted from background ticks so the main thread can keep browser-local persistence fresh even while the UI is only polling state snapshots

The worker command paths intentionally stay aligned with the existing `/api/...` HTTP surface so the frontend controller does not branch on host after environment creation.

## Browser Test Architecture

- The Playwright harness is now host-aware through `tests/e2e/support_runtime_host.py`.
- `ServerRuntimeHost` wraps the existing Flask-backed `AppServer` and still supports restart semantics for persistence tests.
- `StandaloneRuntimeHost` builds `output/standalone/` once per test process, verifies the expected packaged files exist, serves the output from a local static HTTP server, and captures browser-side persistence/debug artifacts on failure.
- Shared UI-flow tests now run against both hosts through the same base browser case.
- Server-only coverage keeps backend restart persistence assertions.
- Standalone-only coverage adds:
  - static-host startup
  - browser storage restore on reload
  - visible startup error messaging when Pyodide initialization fails
- The shard machinery in `tests/e2e/playwright_suite_support.py` now targets server-host tests only. Standalone tests are intentionally excluded from those shards and run through their dedicated suite entrypoint.
- `tests/e2e/playwright_suite_support.py` is also the canonical suite manifest for the Node Playwright runner. npm entrypoints now select suites by semantic name instead of hardcoding Python module names.

The preferred local standalone suite entrypoint is:

```powershell
npm run test:e2e:playwright:standalone
```

Direct Python debugging is still supported, but it now expects prebuilt `output/standalone/` artifacts:

```powershell
npm run build:frontend:standalone
py -3 -m unittest -q tests.e2e.test_playwright_standalone_runtime
```

Server shard entrypoints still use `tests/e2e.playwright_chunk_subset`, but now partition only the Flask-backed browser cases.

## CI Topology

GitHub Actions now exposes standalone browser coverage as a separate signal:

- `frontend-backend`
  - runs `npm run build:frontend`
  - runs `npm run build:frontend:standalone`
  - runs frontend, mypy, descriptor, unit, API, and Playwright integrity checks
- `e2e-playwright`
  - a 4-way matrix of server-only Playwright shards
- `e2e-playwright-standalone`
  - the dedicated standalone browser job that runs `tests.e2e.test_playwright_standalone_runtime`
- `pages-build`
  - runs only on `push` to `main` or `workflow_dispatch`
  - rebuilds `output/standalone/`, configures Pages, and uploads the Pages artifact
- `pages-deploy`
  - runs only on `push` to `main` or `workflow_dispatch`
  - deploys the uploaded artifact to the `github-pages` environment

This keeps standalone failures explicit in the CI UI, avoids duplicate execution inside the server shard matrix, and only publishes the public demo after the existing quality gates pass.

## GitHub Pages Deployment

- Deployment is handled by the existing CI workflow in `.github/workflows/ci.yml`.
- Publish conditions:
  - push to `main`
  - manual `workflow_dispatch`
- Published artifact:
  - `output/standalone/`
- Expected project-site URL:
  - `https://grgs.github.io/cellular-automaton-lab/`
- GitHub repository settings still need `Settings -> Pages -> Source = GitHub Actions` enabled for the workflow to publish.

## Failure Artifacts

- Browser tests now honor `E2E_ARTIFACTS_DIR` when it is set.
- Local runs still fall back to temp directories.
- CI jobs set deterministic workspace-local artifact roots:
  - `e2e-artifacts/server-subset-<index>/...`
  - `e2e-artifacts/standalone-browser/...`
- On failure, uploaded artifacts can include:
  - page screenshot and HTML
  - captured browser console/page errors
  - backend state/topology snapshots for server-host tests
  - browser localStorage/IndexedDB snapshots plus static-host logs for standalone tests

## Verification Status

The current implementation was verified with:

```powershell
npm run typecheck:frontend
npm run test:frontend
npm run build:frontend
node .\tools\run-playwright.mjs --list-suites
npm run test:e2e:playwright:server
npm run test:e2e:playwright:standalone
Test-Path .\output\standalone\.nojekyll
py -3 -m unittest -q tests.e2e.test_playwright_suite_integrity
npm run build:frontend:standalone
py -3 -m unittest -q tests.e2e.test_playwright_standalone_runtime
```

That browser coverage now exercises:

- startup to ready state
- run, pause, and single-step generation changes
- rule and topology switching, including Penrose patch depth controls
- canvas editing flows
- pattern import, export, copy, and paste
- server restart persistence
- standalone reload persistence from browser storage
- standalone worker-init failure messaging

## Known Limitations

- Pyodide is loaded from the CDN configured in `frontend/standalone/worker-client.ts`; the standalone build does not yet vend Pyodide assets locally for fully offline use.
- The standalone Python runtime still bypasses Flask-specific HTTP concerns such as request objects and response wrappers; only payload validation and simulation contracts are shared.
- The standalone build is aimed at static hosting with network access. If offline hosting becomes a requirement, Pyodide must be vendored into the output and loaded locally.
- The Node Playwright runner can self-repair missing Chromium shared libraries only on Debian/Ubuntu-style Linux environments with `apt`, `apt-cache`, and `dpkg-deb`.

## Remaining Work Checklist

- Decide whether Pyodide must be bundled into the standalone output instead of loaded from a CDN. If full offline hosting is required, replace the CDN loader with vendored Pyodide assets and update the packager accordingly.
- If the public demo needs stronger polish later, add a post-deploy smoke check and optionally a custom domain without changing the standalone runtime contract.
