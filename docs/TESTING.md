# Testing Strategy

`cellular-automaton-lab` uses a layered test strategy. The goal is to catch the cheapest failures first, then spend browser and full-stack time only on behavior that actually needs it.

In practice, the test stack is:

1. frontend static checks and unit tests
2. backend type checks and Python unit/API tests
3. topology and descriptor validation tools
4. candidate-sample and visual-diagnosis tooling
5. browser end-to-end coverage with Playwright

The repository does not rely on a single “everything is tested in the browser” approach. Most logic is validated before a real browser is involved.

## Local Git Guards

The repo also includes local git guards built on `pre-commit`. They are meant to catch privacy leaks and obvious secret exposure before code is pushed.

The guard stack uses:

- `pre-commit` as the hook runner
- `detect-secrets` for secret scanning
- a repo-local privacy scanner for local filesystem paths, consumer email addresses, and consumer cloud-share links

Install the hooks with:

```powershell
py -3 -m pre_commit install --hook-type pre-commit --hook-type pre-push
```

Run them manually with:

```powershell
py -3 -m pre_commit run --all-files
py -3 -m pre_commit run --hook-stage pre-push --all-files
```

The privacy guard blocks patterns such as:

- Windows or POSIX home-directory paths
- consumer email addresses, including `@gmail.com` and `@outlook.com`
- consumer cloud-share links such as Google Drive, Dropbox, and OneDrive share URLs

If a line is intentionally safe and public, it can be allowlisted inline with:

```text
privacy-guard: allow
```

Use that sparingly. The intended default is to reject personal information, not to normalize it into the repo.

## Testing Goals

The overall strategy is designed to protect these boundaries:

- frontend contracts stay typed, buildable, and free of broad type escapes
- backend request handling and state transitions stay correct without needing a browser
- topology descriptors and tiling metadata stay internally consistent
- the real app shell, controls, editor flows, and persistence still work in a browser

This keeps failures localized:

- TypeScript catches frontend contract drift.
- mypy catches backend and test harness contract drift.
- Python unit/API tests catch state, persistence, request, and serialization regressions.
- Playwright catches real integration issues across the rendered UI.

## Test Layers

### 1. Frontend Static Checks

Frontend validation starts with:

```powershell
npm run typecheck:frontend
npm run build:frontend
```

What these protect:

- TypeScript contract correctness under the repo’s strict compiler settings
- the Vite production build
- import graph and bundling integrity
- architecture rules enforced through type surfaces

The frontend is treated as a fully typed source tree. CI also enforces structural invariants such as:

- no `@ts-nocheck`
- no `as unknown as`
- no open-ended `Record<string, unknown>` or `[key: string]: unknown` on normal contract surfaces
- no broad async/render helper types leaking into public frontend contracts

These checks matter because the repo intentionally pushes normalization and raw-value handling into small parser/validator seams instead of letting loose types spread through the app.

### 2. Frontend Unit Tests

Frontend unit/module tests run in Vitest:

```powershell
npm run test:frontend
```

These tests are aimed at browser-independent frontend behavior such as:

- control/view-model logic
- overlay and disclosure policy
- pattern parsing and export behavior
- preset and snapshot reconciliation behavior

They should validate frontend logic that does not require a real browser or Flask server.

Use frontend unit tests when:

- changing typed frontend state logic
- changing parsers or normalization helpers
- changing preset, overlay, or pattern behavior
- changing action/controller logic that can be exercised without full browser interaction

### 3. Python Type Checking

Backend and shared Python support code are checked with mypy:

```powershell
py -3 -m mypy --config-file mypy.ini
```

This protects:

- backend request and response contracts
- persisted snapshot shapes
- topology and catalog payload types
- typed test harness and support utilities

The Python typing rules are intentionally strict, especially around backend code and shared test helpers. The goal is to catch contract drift before it becomes a runtime issue in routes, restore flows, or test infrastructure.

### 4. Python Unit Tests

Python unit tests live under [tests/unit](../tests/unit).

Run them with:

```powershell
py -3 -m unittest discover -s tests/unit -p "test_*.py"
```

These cover:

- simulation engine behavior
- transition planning
- persistence and restore logic
- topology models and validation
- request parsing and payload validation
- backend support utilities
- startup guards and tool-level validation

Use unit tests for:

- pure backend logic
- service and coordinator behavior
- topology/model math that does not need HTTP
- parser/validation logic

If a change can be proven without a Flask test client or a browser, it usually belongs here.

### 5. API Tests

API tests live under [tests/api](../tests/api).

Run them with:

```powershell
py -3 -m unittest discover -s tests/api -p "test_*.py"
```

These tests verify:

- HTTP request validation
- route behavior
- serialized state, topology, and rule payloads
- reset/config/cell mutation flows
- persistence behavior through the HTTP layer

Use API tests when:

- changing route behavior
- changing payload schemas
- changing request parsing rules
- changing how backend mutations are exposed over HTTP

These tests should prove backend behavior without needing a real browser.

### 6. Topology And Descriptor Validation Tools

Some correctness checks live in dedicated tooling rather than ordinary unit tests:

```powershell
py -3 tools\validate_tilings.py
py -3 tools\regenerate_frontend_topology_fixtures.py --all --check
```

This validates geometry and tiling descriptors directly. It is part of the normal validation path because topology metadata is foundational to both backend behavior and frontend rendering.

Use this tool whenever changing:

- topology catalog definitions
- periodic-face descriptor data
- geometry-related bootstrap payloads
- representative frontend topology fixtures used by browser-visible geometry or palette tests

### 7. Browser End-To-End Tests

Browser tests live under [tests/e2e](../tests/e2e).

The main Playwright-backed suites cover flows such as:

- overlays and editor behavior
- pattern import/export and showcase demos
- rules and topology picker behavior
- topology switching and persistence
- fixture-backed dead/live palette alias regressions for palette-heavy tilings

Non-interaction browser checks should prefer the review/test API over synthetic
canvas clicks. In practice:

- use canvas clicks when hit-testing, brush behavior, or editor interaction is
  the thing being tested
- use injected review topology plus cell-state mutation by `cell.id` when the
  thing being tested is rendered appearance or palette behavior

The palette alias regressions now follow that rule. They no longer click the
canvas to paint representative cells; they inject topology, set states by
`cell.id`, and sample the rendered pixels directly.

Useful entrypoints include:

```powershell
npm run test:e2e:playwright
npm run test:e2e:playwright:server
npm run test:e2e:playwright:standalone
npm run test:e2e:playwright:subset
npm run build:frontend:standalone
npm run build:standalone-and-test
node ./tools/run-playwright.mjs --list-suites
```

These npm scripts are the preferred local entrypoints because they own Playwright suite selection, Linux browser-runtime repair, and standalone-build setup when a suite needs it. The suite list comes from the Python Playwright manifest in `tests/e2e/playwright_suite_support.py`.

The runner now reuses `output/standalone/` when the existing build manifest matches the current checkout fingerprint. It only rebuilds the standalone bundle when required outputs are missing, the manifest is missing, or the build fingerprint no longer matches the current source tree.

Direct Python entrypoints are still useful when debugging CI internals, but they are not the preferred local path:

```powershell
py -3 -m unittest -q tests.e2e.test_playwright_suite_integrity
py -3 -m unittest -q tests.e2e.test_playwright_overlays_and_editor
py -3 -m unittest -q tests.e2e.test_playwright_pattern_and_showcase
py -3 -m unittest -q tests.e2e.test_playwright_rules_and_picker
py -3 -m unittest -q tests.e2e.test_playwright_topology_and_persistence
```

The palette alias coverage is generated inside the shared Playwright case suite,
not maintained as one hand-written test per family. The current browser-backed
dead/live alias checks cover the fixture-backed palette-heavy families:

- `chair`
- `dodecagonal-square-triangle`
- `hat-monotile`
- `pinwheel`
- `robinson-triangles`
- `shield`
- `tuebingen-triangle`

Those browser checks are intentionally narrower than the unit-level palette
invariants. Use the browser path when the question is “does the rendered canvas
still distinguish dead from live?”, not just “does the token resolver return
the expected color?”

For standalone specifically, direct Python entrypoints now expect prebuilt outputs under `output/standalone/`. Use:

```powershell
npm run test:e2e:playwright:standalone
```

or build the artifacts first:

```powershell
npm run build:frontend:standalone
py -3 -m unittest -q tests.e2e.test_playwright_standalone_runtime
```

The repo also supports a chunked subset runner for CI:

```powershell
py -3 -m unittest -q tests.e2e.playwright_chunk_subset
```

Browser tests are the highest-cost layer. They should validate:

- real DOM wiring
- real canvas interaction behavior
- browser storage/session behavior
- full backend/frontend integration

They should not be the first place to test logic that already fits a unit or API test.

### Browser Diagnosis And Failure Investigation

Use the browser-diagnosis tools when you need a focused local answer instead of a full Playwright suite run.

Preferred paths:

- Full suite or feature suite: use the npm Playwright entrypoints.
- Structural-first candidate exploration for a patch-depth family: use `python tools/run_family_sample_workbench.py`.
- Visual inspection of one rendered topology: use `python tools/render_canvas_review.py`.
- Host-owned local debugging with guaranteed startup and cleanup: use `python tools/run_browser_check.py`.
- Small comparison matrix across hosts, themes, or sizes: use `python tools/run_render_review_sweep.py`.

Family sample workbench examples:

```powershell
python tools/run_family_sample_workbench.py --family shield --patch-depth 3
python tools/run_family_sample_workbench.py --family shield --patch-depth 3 --browser-review --host standalone
python tools/run_family_sample_workbench.py --family pinwheel --patch-depth 3
python tools/run_geometry_cleanup_workbench.py --family shield --patch-depth 3
python tools/run_geometry_cleanup_workbench.py --family shield --patch-depth 3 --browser-review --host standalone --theme dark
```

Use the workbench when:

- comparing candidate representative windows or crop rules
- measuring count, connectivity, hole behavior, bounds drift, and overlap diagnostics across candidates
- attaching browser review to an explicit candidate topology instead of only the shipped family/depth patch

Current v1 strategy support:

- `baseline` for any patch-depth family
- `shield` `representative-window` for explicit dodecagonal window-threshold sweeps
- `shield` `trace-cleanup-scale` in the geometry cleanup workbench for fixed-sample cleanup-factor sweeps

Use the geometry cleanup workbench when the representative sample is already fixed and the question is instead:

- how much topology-space cleanup removes overlap
- how much bounds drift that cleanup introduces
- whether the browser-visible gutter risk stays acceptable under the current draw-only seam bridge

Direct render review examples:

```powershell
python tools/render_canvas_review.py --list-profiles
python tools/render_canvas_review.py --profile pinwheel-depth-3
python tools/render_canvas_review.py --profile pinwheel-depth-3 --literature-review
python tools/render_canvas_review.py --profile pinwheel-depth-3 --literature-review --reference C:\path\to\pinwheel-reference.png
```

Managed runner examples:

```powershell
python tools/run_browser_check.py --host standalone --render-review --profile pinwheel-depth-3
python tools/run_browser_check.py --host standalone --render-review --profile pinwheel-depth-3 --literature-review
python tools/run_browser_check.py --host server --unittest tests.e2e.playwright_case_suite.CellularAutomatonUITests.test_pinwheel_topology_switch_renders_aperiodic_patch
python tools/run_browser_check.py --host server --success-artifacts --unittest tests.e2e.playwright_case_suite.CellularAutomatonUITests.test_pinwheel_topology_switch_renders_aperiodic_patch
```

Sweep example:

```powershell
python tools/run_render_review_sweep.py --profile pinwheel-depth-3 --patch-depths 3,4 --hosts standalone,server
python tools/run_render_review_sweep.py --profile pinwheel-depth-3 --patch-depths 3,4 --hosts standalone,server --literature-review
```

Literature-review conventions:

- `--literature-review` requires `--profile`.
- Profiles store citations, source URLs, cache filenames, and review notes; the repo does not store literature images.
- The default local cache is `output/literature-reference-cache/`.
- Explicit `--reference` always overrides the cache.
- If no cached image exists, the render review still succeeds and records a missing-reference warning in the JSON summary and run manifest.

Repo-scoped process inspection and cleanup:

```powershell
python tools/dev_processes.py list
python tools/dev_processes.py kill --stale-browser-hosts
python tools/dev_processes.py kill --port 5002
```

Artifact locations:

- Successful direct render-review outputs default to `output/render-review/`.
- Direct render-review failure artifacts default to `output/render-review-artifacts/`.
- Literature reference cache defaults to `output/literature-reference-cache/`.
- Standalone builds now emit `output/standalone/build-manifest.json`.
- Managed runner `--render-review` runs default the PNG, JSON summary, and optional montage into `output/browser-check/<timestamp-mode-host>/`.
- Managed runner outputs default to `output/browser-check/<timestamp-mode-host>/`.
- Managed runner `--unittest` runs place delegated browser-test failure bundles under `output/browser-check/<timestamp-mode-host>/test-artifacts/`.
- Managed runner `--unittest --success-artifacts` runs also preserve a per-test success bundle under `output/browser-check/<timestamp-mode-host>/test-artifacts/`.
- Sweep runs default to `output/render-review-sweeps/<timestamp-profile>/`.
- Family sample workbench runs default to `output/family-sample-workbench/<timestamp-family-depth>/`, with one `workbench-manifest.json` plus one subdirectory per candidate.
- Geometry cleanup workbench runs default to `output/geometry-cleanup-workbench/<timestamp-family-depth>/`, with one `workbench-manifest.json` plus one subdirectory per cleanup candidate.

Shared failure artifact bundle:

- `canvas.png`
- `page.png`
- `page.html`
- `console.txt`
- `render-summary.json`
- host logs such as standalone or server stdout and stderr
- `run-manifest.json`

Managed runner manifests for successful render reviews also record:

- `renderPng`
- `renderSummary`
- `renderMontage` when present
- `runtimeProvenance`
- `provenanceWarnings`
- `transformSummary`
- `literatureReferenceStatus` when literature review was requested or an explicit reference was used
- `literatureWarnings` when the review ran without a cache hit
- `consistencyWarnings` when the review summary surfaced any

Render-review JSON summaries now also record:

- `transformReport`
- `runtimeProvenance`
- `provenanceWarnings`
- `settleDiagnostics`
- `visualMetrics`

Render-review capture now waits for a stable readiness tuple before saving PNGs
or JSON summaries. A hidden loading overlay is no longer sufficient on its own.
The settle gate now requires:

- `window.__appReady === true`
- no active blocking activity message or kind
- non-placeholder `gridSizeText`
- non-empty `generationText`
- stable topology/render summary state across three polls

This change was motivated by a dark-mode standalone `shield` run that captured a
transient `Building tiling...` frame even though the command itself succeeded.

The standard render-review payload now also includes advisory visual metrics
such as:

- visible occupied-field aspect ratio
- edge density
- boundary dominance
- gutter score
- orientation diversity when orientation tokens are present
- 12-sector occupancy and derived radial-symmetry score when render diagnostics
  expose the needed aggregate inputs

Named render-review profiles also now carry advisory `profileExpectations`:

- short manual-review checklist items owned by the profile
- exact expected-warning matching for known host- or family-specific warnings
- missing vs unexpected warning classification in the JSON summary

These expectations are advisory only. They do not change exit status or fail a
review command on their own.

Managed runner manifests for successful `--unittest --success-artifacts` runs also record:

- `successArtifactsRequested`
- `testArtifactsDir`

Defaults:

- `tools/render_canvas_review.py` is the preferred visual-inspection entrypoint.
- `tools/run_browser_check.py` is the preferred direct-debug entrypoint when host lifecycle, logs, and cleanup must be owned by one command.
- `tools/run_render_review_sweep.py` is the preferred entrypoint when a diagnosis loop needs a small matrix comparison rather than one run.
- npm Playwright entrypoints remain the preferred full-suite path.
- `tools/dev_processes.py` is the narrow cleanup fallback when you need to inspect or terminate repo-owned browser/server helper processes directly.

If a visual-review run depends on standalone provenance being current, rebuild
the frontend outputs on the current HEAD first:

```powershell
npm run build:frontend
npm run build:frontend:standalone
```

## Recommended Local Workflow

For most frontend-only changes:

```powershell
npm run typecheck:frontend
npm run build:frontend
npm run test:frontend
```

For backend-only changes:

```powershell
py -3 -m mypy --config-file mypy.ini
py -3 -m unittest discover -s tests/unit -p "test_*.py"
py -3 -m unittest discover -s tests/api -p "test_*.py"
py -3 tools\validate_tilings.py
py -3 tools\report_tiling_verification_strength.py
py -3 tools\report_tiling_verification_strength.py --format detail
py -3 tools\report_tiling_verification_strength.py --format json
```

For changes that affect real UI flows, controls, persistence, or topology switching, add the relevant Playwright suite:

```powershell
npm run test:e2e:playwright:server
npm run test:e2e:playwright:standalone
```

Quick failure-class mapping:

- server-host browser failures: `npm run test:e2e:playwright:server`
- standalone browser failures: `npm run test:e2e:playwright:standalone`
- full browser sweep: `npm run test:e2e:playwright`
- shard debugging with `PLAYWRIGHT_SUBSET_*`: `npm run test:e2e:playwright:subset`

Playwright troubleshooting:

- missing server-host browser behavior:
  run `npm run test:e2e:playwright:server`
- missing standalone-only browser behavior:
  run `npm run test:e2e:playwright:standalone`
- stale or missing standalone bundle:
  run `npm run build:frontend:standalone`
- full browser regression sweep:
  run `npm run test:e2e:playwright`
- shard-specific server regression:
  run `npm run test:e2e:playwright:subset`
- Linux browser library failures:
  `node ./tools/run-playwright.mjs` can repair missing Playwright browser libraries only on Debian/Ubuntu-style environments with `apt`, `apt-cache`, and `dpkg-deb`
- when those packaging tools are unavailable:
  install the listed shared libraries manually, then rerun the npm Playwright command you actually need

For broad refactors or release confidence, run the full local sweep:

```powershell
npm run typecheck:frontend
npm run build:frontend
npm run test:frontend
py -3 -m mypy --config-file mypy.ini
py -3 -m unittest discover -s tests -p "test_*.py"
py -3 tools\validate_tilings.py
```

## CI Strategy

CI runs in two stages:

### Frontend, Backend, And Tooling Job

This job runs first and blocks the browser matrix. It covers:

- typed frontend source invariants
- frontend typecheck
- frontend build
- frontend Vitest suites
- mypy
- tiling validation
- Python unit and API tests with coverage
- Playwright suite integrity guard

The point of this job is to reject obvious or structural failures before spending time on browser subsets.

### Playwright Subset Matrix

The Playwright workload is then split across multiple subsets. This keeps end-to-end coverage broad without making a single browser job overly slow or brittle.

The browser subset stage is intentionally downstream from the cheaper checks. If unit, API, typing, or topology validation fails, the matrix does not run.

## Where New Tests Should Go

Choose the cheapest layer that proves the behavior:

- frontend parser, selector, overlay, preset, or reconciliation logic: Vitest
- backend planner, service, model, request, or persistence logic: Python unit tests
- route or payload behavior: API tests
- real DOM, canvas, storage, or multi-layer browser flow: Playwright

Good rule of thumb:

- if no DOM is needed, do not use Playwright
- if no HTTP boundary is needed, do not use API tests
- if the behavior is pure or nearly pure, prefer unit tests

## What Not To Rely On

The test strategy intentionally avoids a few things:

- no dependency on committed generated frontend runtime files
- no JavaScript unit-test harness that imports built artifacts from `static/`
- no broad “browser tests will catch it later” philosophy

The repo expects correctness to be established first through typed contracts and lower-cost tests, then confirmed in the browser.

## Test Maintenance Principles

When adding or refactoring tests:

- keep helpers typed and exact
- prefer endpoint-specific or feature-specific helpers over generic “do anything” test utilities
- add browser coverage only for behavior that truly needs a browser
- update CI guards when architectural invariants change
- keep topology and descriptor validation close to the data they protect

The best outcome is a test suite that is fast to debug, layered by cost, and aligned with the actual architecture of the app.
