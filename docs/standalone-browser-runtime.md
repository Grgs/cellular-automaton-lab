# Standalone Browser Runtime

Status: current operational reference. Last audited against the implementation
on August 2, 2026.

The app supports two hosts for the same UI and Python simulation model:

- `server`: Flask exposes HTTP endpoints and owns session-scoped runtimes.
- `standalone`: a browser Web Worker runs the Python simulation through a
  packaged Pyodide runtime, and the site is served as static files.

Standalone therefore means **no separately running Python backend**. It does
not mean “no Python”: Python executes locally inside the browser worker.

For the rationale behind this design, read [DESIGN.md](DESIGN.md). For the
broader subsystem map, read [ARCHITECTURE.md](ARCHITECTURE.md).

## Runtime Shape

### Shared application

- [frontend/shell/app-shell-body.html](../frontend/shell/app-shell-body.html) is
  the one authored DOM shell used by both hosts.
- [frontend/app-runtime.ts](../frontend/app-runtime.ts) owns the shared app
  lifecycle and controller stack.
- Frontend controllers depend on the `SimulationBackend` contract instead of
  Flask or Pyodide directly.
- Shared Python request parsing and persisted-snapshot acceptance live below
  the Flask layer so both hosts can reuse them.

### Server host

- Flask renders [templates/index.html](../templates/index.html).
- The frontend uses the HTTP-backed `SimulationBackend` from
  [frontend/api.ts](../frontend/api.ts).
- Flask routes resolve a session-scoped coordinator.
- The backend process owns persistence and the threaded run loop.
- Flask routes select commands from the shared semantic registry and dispatch
  them through a coordinator-backed target.

### Standalone host

- [frontend/standalone.ts](../frontend/standalone.ts) loads
  `standalone-bootstrap.json`, constructs the worker environment, and starts
  the shared app runtime.
- [frontend/standalone/worker-client.ts](../frontend/standalone/worker-client.ts)
  adapts worker messages to `SimulationBackend`.
- [frontend/standalone-worker.ts](../frontend/standalone-worker.ts) runs as a
  module worker, loads `../pyodide/pyodide.mjs`, and installs the packaged
  Python bundle into Pyodide's
  virtual filesystem, and imports
  [backend/browser_runtime.py](../backend/browser_runtime.py).
- The worker serializes operations and owns the run loop through JavaScript
  timers.
- Simulation persistence uses IndexedDB first and falls back to `localStorage`.
- The worker maps API-shaped paths to the same semantic command registry,
  request decoding, domain dispatcher, and public-error contract as Flask.

Both bootstraps provide a discriminated runtime environment. Features inspect
the `liveForks` and `persistence` capabilities they consume instead of testing
a `server` or `standalone` host name. A supported live-fork capability includes
its backend factory; an unavailable capability carries the explicit
`open-in-lab` fallback.

## Build The Static Site

```powershell
npm run build:frontend:standalone
```

The command delegates to `python -m tools build standalone` and writes
`output/standalone/`. The build:

1. stages a transient standalone HTML input from the shared shell
2. runs Vite in standalone mode
3. normalizes the generated entrypoint to `output/standalone/index.html`
4. writes `.nojekyll` for GitHub Pages project-site hosting
5. copies the pinned Pyodide runtime from the installed npm package into
   `output/standalone/pyodide/`
6. exports canonical defaults and topology metadata to
   `standalone-bootstrap.json`
7. bundles backend and configuration Python/JSON sources into
   `standalone-python-bundle.json`
8. records source provenance in `build-manifest.json`

The output has no runtime CDN dependency. Its frontend, Pyodide runtime, Python
standard library archive, and application Python sources are served from the
same artifact.

Do not open `index.html` directly with a `file://` URL. Workers, dynamic module
loading, and fetched JSON require an HTTP origin. To inspect a built artifact
locally, serve `output/standalone/` with any static HTTP server.

## Worker Contract

The canonical TypeScript protocol is
[frontend/standalone/protocol.ts](../frontend/standalone/protocol.ts).

Initialization sends:

- a request ID
- an optional persisted simulation snapshot
- the URL of `standalone-python-bundle.json`

After initialization, the main thread sends `request` messages with API-shaped
paths. The current command family includes state and rule reads, control and
configuration mutations, cell mutations, topology previews, seed comparison,
and comparison filmstrips.

The path vocabulary intentionally resembles the server HTTP API. This keeps
the frontend controller host-neutral; it does not make Flask part of the
standalone runtime.

Successful worker responses may carry a canonical snapshot, rules, a revisioned
cell delta, comparison output, filmstrip output, topology-preview geometry, or
a persisted snapshot. Error responses carry a stable error string and optional
limit metadata. Runtime decoders validate these messages before the frontend
uses them.

Background ticks also emit `persist` events so browser storage stays current
when the UI is only polling state snapshots.

## Browser Test Architecture

- The Playwright harness is now host-aware through `tests/e2e/support_runtime_host.py`.
- `ServerRuntimeHost` wraps the existing Flask-backed `AppServer` and still supports restart semantics for persistence tests.
- `StandaloneRuntimeHost` builds `output/standalone/` once per test process, verifies the expected packaged files exist, serves the output from a local static HTTP server, and captures browser-side persistence/debug artifacts on failure.
- Shared UI-flow tests now run against both hosts through the same base browser case.
- Server-only coverage keeps backend restart persistence assertions.
- Standalone-only coverage adds:
    - static-host startup
    - a measured 30-second cold-start budget exposed as `window.__standaloneStartupMs`
    - browser storage restore on reload
    - visible startup error messaging when Pyodide initialization fails
- The shard machinery in `tests/e2e/playwright_suite_support.py` now targets server-host tests only. Standalone tests are intentionally excluded from those shards and run through their dedicated suite entrypoint.
- `tests/e2e/playwright_suite_support.py` is also the canonical suite manifest for the Node Playwright runner. npm entrypoints now select suites by semantic name instead of hardcoding Python module names.

## Lifecycle And Concurrency

- `SimulationBackend.dispose()` is a no-op for HTTP and terminates the worker
  for standalone.
- Lazy standalone live forks own an `AbortController`. Disposing a fork while
  Pyodide is still starting aborts initialization and terminates its worker
  immediately instead of waiting for the runtime to become ready.
- `AppController.dispose()` releases UI-owned resources.
- Both entrypoints install `pagehide` cleanup.
- The worker chains operations so two Python commands cannot mutate its runtime
  concurrently.
- Cell deltas are accepted only when epoch, revision, topology revision, and
  generation match the installed snapshot; otherwise the client requests a
  full state snapshot.

## Persistence Differences

| Behavior                           | Server                               | Standalone                         |
| ---------------------------------- | ------------------------------------ | ---------------------------------- |
| Simulation state                   | Backend session store                | IndexedDB or `localStorage`        |
| Restart behavior                   | Session restore after server restart | Restore after page reload          |
| Multiple independent sessions      | Session registry                     | One runtime per worker environment |
| UI preferences and saved wall runs | Browser storage                      | Browser storage                    |

Saved comparison runs and preferences remain device-local in both hosts.
Portable run links are the cross-device handoff format.

## Runtime Profiling

Build the standalone artifact, then collect the default lower-end desktop
profile:

```powershell
npm run build:frontend:standalone
python -m tools perf standalone-runtime --format json --output output/standalone-runtime-profile.json
```

The command starts a fresh Chromium process for each of three runs, applies a
4× CPU slowdown, measures cold start, and retains two independent Pyodide live
forks in sequence. Each report records the browser version, user agent,
reported hardware concurrency/device memory, host platform, build provenance,
and every raw sample. Use `--cpu-throttle-rate 1` for unthrottled host
measurements, or change `--repeats` while investigating variance.

The expected device class is a lower-end desktop or laptop CPU represented by
4× Chromium throttling at a 1280×720 viewport. Memory is not emulated. The
reported memory is aggregate resident set size across the fresh Chromium
process tree, so it includes browser/renderer overhead and shared pages. Treat
the incremental fork values as conservative resource measurements, not precise
Pyodide heap attribution.

The first three-run reference observation on August 2, 2026 used headless
Chromium 145 under WSL2. Chromium reported 12 hardware threads and 8 GiB device
memory; the 4× slowdown is the relevant CPU expectation:

| Measurement                      |  Median | Maximum |
| -------------------------------- | ------: | ------: |
| Cold start                       |  3.56 s |  3.69 s |
| First live-fork startup          |  2.19 s |  2.47 s |
| Second live-fork startup         |  2.26 s |  2.46 s |
| Main runtime incremental RSS     | 244 MiB |       — |
| First live-fork incremental RSS  | 103 MiB | 105 MiB |
| Second live-fork incremental RSS | 137 MiB | 159 MiB |
| Peak Chromium RSS with two forks | 798 MiB | 821 MiB |

`tools/standalone_runtime_budget.json` turns that observation into the supported
lower-end proxy policy. The 3.69-second observed maximum plus a 4.31-second
regression and runner-variance margin produces an 8-second limit. This replaces
the former 30-second ceiling with a threshold that is 73% lower while retaining
117% headroom over the observed maximum. The standalone browser suite applies
the same conservative limit to its unthrottled smoke journey.

CI runs the three-repeat, 4×-throttled profile with budget enforcement and
uploads the complete `standalone-runtime-profile` JSON artifact. Run the same
gate locally with:

```powershell
python -m tools perf standalone-runtime --check-budget --format json --output output/standalone-runtime-profile.json
```

The throttled profile is the repeatable merge gate. Periodic physical-device
measurements remain a calibration check: record them with the same command and
metadata, and revise the observed baseline, explicit margin, and limit together
when sustained results show that the proxy no longer represents the supported
lower-end desktop or laptop class.

The August 3, 2026 reference build also ratcheted the two recently raised gzip
ceilings without treating them as available feature headroom:

| Bundle category | Observed gzip | Regression margin | Ceiling |
| --------------- | ------------: | ----------------: | ------: |
| `js-runtime`    |  83,757 bytes |         143 bytes |  83,900 |
| `js-standalone` |   8,680 bytes |          10 bytes |   8,690 |

Gzip output is deterministic. Any increase beyond those small margins requires
an intentional optimization or a freshly measured, documented budget change;
raw-byte categories retain the broader maintenance headroom described in the
bundle budget policy.

## Testing

The preferred standalone checks are:

```powershell
npm run build:frontend:standalone
npm run smoke:standalone
npm run test:e2e:playwright:standalone
```

Cold start is guarded by `tools/standalone_runtime_budget.json` in both the standalone Playwright suite and the throttled CI profile. Artifact size is guarded separately by `tools/standalone_bundle_budget.json` through `npm run check:bundle-size:fresh`; a Pyodide replacement should be considered only when measured startup or bundle budgets fail persistently.

The host-aware Playwright support:

- builds or reuses `output/standalone/` only when its provenance is fresh
- serves the artifact through a local static HTTP server
- checks packaged-file presence and startup readiness
- captures console errors, page errors, screenshots, HTML, browser storage,
  and static-host logs on failure
- runs shared UI journeys against both hosts where behavior should match

Standalone-specific coverage includes startup, run/pause/step, configuration,
cell editing, pattern flows, comparison flows, reload persistence, and visible
worker-initialization failure handling. Server-only coverage retains backend
restart and session semantics.

Direct Python `unittest` module execution still exists for runner debugging,
but the npm and `python -m tools test e2e` entrypoints own build freshness and
suite selection and should be preferred.

## CI And Deployment

The CI workflow treats standalone as an independent signal:

- the primary build job creates the server frontend and standalone artifact
- a dedicated standalone Playwright job consumes that artifact
- that job records and enforces the throttled runtime profile before browser journeys
- `pages-build` uploads `output/standalone/` only after required quality gates
- `pages-deploy` publishes the artifact to GitHub Pages

The expected project-site URL is
[https://grgs.github.io/cellular-automaton-lab/](https://grgs.github.io/cellular-automaton-lab/).
The repository's Pages source must be configured as **GitHub Actions**.

Tagged releases independently rebuild and smoke-test the artifact before
attaching a standalone archive to the GitHub Release. See
[MAINTENANCE.md](MAINTENANCE.md#public-release-process).

## Constraints

- Pyodide adds artifact size and cold-start latency compared with a
  JavaScript-only runtime.
- Static hosting still requires an HTTP origin even when all assets are local.
- The worker bypasses Flask-specific request objects, response wrappers, and
  server session management; only framework-neutral payload and simulation
  contracts are shared.
- Browser storage is local to the browser profile and is not cloud sync.
- Any new Python dependency used by the browser runtime must either already be
  available in the packaged Pyodide environment or be deliberately added to
  the standalone packaging design.

## Change Checklist

When changing the standalone host or its artifact:

1. update both adapters if a shared `SimulationBackend` operation changes
2. update protocol types and runtime decoders together
3. update or regenerate decoder-contract fixtures for payload changes
4. rebuild the artifact before trusting browser results
5. run the standalone smoke, bundle-size, and Playwright checks
6. update [DESIGN.md](DESIGN.md) only if the host boundary or a durable tradeoff
   changes; update this document for operational or implementation changes
