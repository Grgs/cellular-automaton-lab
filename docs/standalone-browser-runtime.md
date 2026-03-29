# Standalone Browser Runtime

This repository now supports two runtime hosts for the same UI:

- `server` mode keeps the existing Flask + HTTP architecture.
- `standalone` mode runs the Python simulation inside a Web Worker using Pyodide and serves the frontend as static assets from `output/standalone/`.

## Architecture Overview

### Server mode

- Flask still renders `templates/index.html`.
- The frontend uses the HTTP-backed `SimulationBackend` from `frontend/api.ts`.
- Server bootstrap data is available through both template globals and `GET /api/bootstrap`.
- The backend remains authoritative for state, persistence, and the threaded run loop.

### Standalone mode

- `standalone.html` bootstraps the same DOM shell the server-rendered app uses.
- `frontend/standalone.ts` fetches `standalone-bootstrap.json`, installs the bootstrap globals, creates the worker-backed `SimulationBackend`, and then starts the shared frontend controller stack.
- `frontend/standalone-worker.ts` loads Pyodide, copies the packaged Python sources into Pyodide's virtual filesystem, imports `backend.browser_runtime`, and proxies frontend commands into the Python simulation runtime.
- The worker owns the standalone run loop with JS timers. The frontend continues to use the existing polling/reconciliation flow while the worker advances the simulation in the background.
- Browser-local persistence uses IndexedDB first and falls back to `localStorage` if IndexedDB is unavailable.

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

This performs four steps:

1. builds the standalone Vite entry into `output/standalone/`
2. copies the shared authored stylesheet and favicon into the standalone output
3. exports `standalone-bootstrap.json` from the Python topology/defaults metadata
4. copies the Python source/config tree into `output/standalone/py-src/` and writes `standalone-python-manifest.json`

The standalone output includes both `standalone.html` and `index.html` for easier static hosting.

## Worker Message Contract

The standalone worker uses the protocol defined in `frontend/standalone/protocol.ts`.

### Main thread -> worker

- `init`
  - `requestId`
  - `persistedSnapshot`
  - `pythonManifestUrl`
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

## Known Limitations

- Pyodide is loaded from the CDN configured in `frontend/standalone/worker-client.ts`; the standalone build does not yet vend Pyodide assets locally for fully offline use.
- The standalone shell currently duplicates the server template structure in `standalone.html`, so future shell/layout changes must be mirrored in both places.
- The standalone Python runtime intentionally bypasses Flask and the Pydantic request layer. It enforces the core command contract and rule/state validation, but it does not yet share every validation helper byte-for-byte with the HTTP layer.
- Standalone browser smoke coverage was verified manually, but there is not yet a committed Playwright suite that exercises `output/standalone/` end-to-end in CI.

## Remaining Work Checklist

- Add dedicated standalone Playwright coverage that serves `output/standalone/` from a static test server and verifies startup, stepping, run/pause, topology changes, painting, import/export, and persistence restore.
- Deduplicate `standalone.html` and `templates/index.html` so both hosts render from one shared shell source.
- Move more of the standalone request validation into shared backend helpers so the server and worker hosts use the same parsing/validation code paths.
- Decide whether Pyodide must be bundled into the standalone output instead of loaded from a CDN. If full offline hosting is required, replace the CDN loader with vendored Pyodide assets and update the packager accordingly.
- If the standalone runtime needs stronger lifecycle guarantees, add explicit backend/worker disposal from the frontend controller so the worker can be terminated cleanly on teardown.
