# Tools Reference

Single index of every script under `tools/`. Each entry is a one-line summary, the canonical invocation, and (when relevant) a pointer to the deeper guide that already covers it.

The CLI tools group into seven purposes:

1. [Build and serve](#build-and-serve)
2. [Lint and format](#lint-and-format)
3. [Pre-commit hooks](#pre-commit-hooks)
4. [Tiling validation and verification](#tiling-validation-and-verification)
5. [Browser diagnosis and render review](#browser-diagnosis-and-render-review)
6. [Fixture and bootstrap regeneration](#fixture-and-bootstrap-regeneration)
7. [Test runners and introspection](#test-runners-and-introspection)
8. [Supply-chain audit](#supply-chain-audit)
9. [Performance benchmarks](#performance-benchmarks)
10. [Process cleanup](#process-cleanup)

For the npm-script surface (which wraps several of these), see the `scripts` block in [package.json](../package.json).

## Build and serve

### `tools/build-standalone.mjs`

Builds the standalone single-file HTML bundle into `output/standalone/` and writes a `build-manifest.json` with the source-tree fingerprint. Wrapped by `npm run build:frontend:standalone`. Source: [build-standalone.mjs](../tools/build-standalone.mjs).

```powershell
node ./tools/build-standalone.mjs
```

### `tools/render_standalone_shell.py`

Prints (or writes) the rendered HTML shell that the standalone build wraps. Used by the standalone build pipeline to produce `output/.standalone-build-input/standalone.html`. Source: [render_standalone_shell.py](../tools/render_standalone_shell.py).

```powershell
py -3 tools/render_standalone_shell.py [output_path]
```

### `tools/run-python.mjs`

Cross-platform Python launcher used by npm scripts. Resolves `$env:PYTHON`, then `py -3` on Windows or `python3`/`python` on POSIX, and forwards remaining args. Source: [run-python.mjs](../tools/run-python.mjs).

```powershell
node ./tools/run-python.mjs path/to/script.py [args...]
```

## Lint and format

### `tools/run_python_style.py`

Runs `ruff check`, `ruff format --check`, or `ruff format` against the curated incremental lint slice (bootstrap, payload contracts, reference verification, render-review tooling, and their tests). The slice is intentionally narrower than the whole repo; widening it is gated on retiring older compatibility-heavy modules. Wired into `pre-commit`. Source: [run_python_style.py](../tools/run_python_style.py).

```powershell
py -3 tools/run_python_style.py check
py -3 tools/run_python_style.py format-check
py -3 tools/run_python_style.py format
```

### `tools/check_frontend_format.mjs`

Repo-owned lightweight frontend formatting check. Asserts every file under `frontend/`, `static/css/`, `templates/`, and `vite.config.ts` ends with a newline, has no trailing whitespace, and has no leading tabs. Wired into `pre-commit` via `npm run format:frontend:check`. Source: [check_frontend_format.mjs](../tools/check_frontend_format.mjs).

```powershell
node ./tools/check_frontend_format.mjs
```

## Pre-commit hooks

These run automatically through [.pre-commit-config.yaml](../.pre-commit-config.yaml) when you commit or push. They are listed here so you can invoke them manually for debugging.

### `tools/privacy_guard.py`

Scans tracked repository files for personal information leaks: Windows/POSIX home-directory paths, consumer webmail addresses, and consumer cloud-share links. Lines tagged with `privacy-guard: allow` are skipped. Used at both `pre-commit` (changed files) and `pre-push` (full repo) stages. Source: [privacy_guard.py](../tools/privacy_guard.py).

```powershell
py -3 tools/privacy_guard.py [paths...]
py -3 tools/privacy_guard.py --all-files
```

### `tools/run_detect_secrets.py`

Wrapper that runs `detect-secrets` against changed files (pre-commit) or all tracked files (pre-push), comparing against [.secrets.baseline](../.secrets.baseline). Source: [run_detect_secrets.py](../tools/run_detect_secrets.py).

```powershell
py -3 tools/run_detect_secrets.py --baseline .secrets.baseline [paths...]
py -3 tools/run_detect_secrets.py --baseline .secrets.baseline --all-files
```

## Tiling validation and verification

The deeper guide for this cluster is [docs/TESTING_TILINGS.md](TESTING_TILINGS.md). Verification status table lives in [docs/TILING_VERIFICATION_STATUS.md](TILING_VERIFICATION_STATUS.md).

### `tools/validate_tilings.py`

Runs the geometry/topology validator across every tiling in the catalog. Catches non-deterministic builders, malformed adjacency, hole formation, and edge-multiplicity issues. This is the cheap geometric sanity check; run it whenever changing topology data. Source: [validate_tilings.py](../tools/validate_tilings.py).

```powershell
py -3 tools/validate_tilings.py
```

### `tools/verify_reference_tilings.py`

Runs the literature-reference verifier across every tiling family. Stricter than `validate_tilings.py`: checks signatures, periodic-face descriptors, exact interior vertex stars, dual-family invariants, polygon-area frequencies, rooted local-reference fixtures, and canonical patch fixtures. Returns non-zero on any blocking surface or connectivity regression. Source: [verify_reference_tilings.py](../tools/verify_reference_tilings.py).

```powershell
py -3 tools/verify_reference_tilings.py
```

### `tools/report_tiling_verification_strength.py`

Aggregates static catalog coverage, aperiodic implementation contracts, fixture presence, and live `verify_all_reference_families()` results into a per-family verification-strength report. Three formats: `summary` (default), `detail`, and `json`. Source: [report_tiling_verification_strength.py](../tools/report_tiling_verification_strength.py).

```powershell
py -3 tools/report_tiling_verification_strength.py
py -3 tools/report_tiling_verification_strength.py --format detail
py -3 tools/report_tiling_verification_strength.py --format json
```

## Browser diagnosis and render review

The deeper guide for this cluster is [docs/TESTING.md](TESTING.md), section "Browser Diagnosis And Failure Investigation". The tools share an implementation package under `tools/render_review/`; the top-level `tools/run_*.py` files are thin CLI entrypoints. Tools listed here in the order they're typically reached for during a diagnosis.

### `tools/render_canvas_review.py`

Renders one tiling family at a chosen depth through the real browser canvas path and saves a PNG plus JSON summary. Supports named profiles (`--list-profiles`), reference-image comparison (`--literature-review` + cached or `--reference` image), settle diagnostics, and visual-quality metrics. Preferred entrypoint when the question is "what does this currently look like?" Source: [render_canvas_review.py](../tools/render_canvas_review.py) → `tools/render_review/review.py`.

```powershell
python tools/render_canvas_review.py --list-profiles
python tools/render_canvas_review.py --profile pinwheel-depth-3
python tools/render_canvas_review.py --profile pinwheel-depth-3 --literature-review
```

### `tools/run_browser_check.py`

Managed runner that owns server/standalone host startup, readiness, logs, and cleanup around either a render review or a delegated unittest. Use when host lifecycle ownership matters or you need a guaranteed artifact bundle on failure. Source: [run_browser_check.py](../tools/run_browser_check.py) → `tools/render_review/browser_check.py`.

```powershell
python tools/run_browser_check.py --host standalone --render-review --profile pinwheel-depth-3
python tools/run_browser_check.py --host server --unittest <dotted-test-id>
python tools/run_browser_check.py --host server --success-artifacts --unittest <dotted-test-id>
```

### `tools/run_render_review_sweep.py`

Runs one render-review profile across a small matrix of hosts, themes, or sizes and emits one sweep manifest plus one comparable artifact tree. Use when the question is comparative rather than single-run. Source: [run_render_review_sweep.py](../tools/run_render_review_sweep.py) → `tools/render_review/sweep.py`.

```powershell
python tools/run_render_review_sweep.py --profile pinwheel-depth-3 --patch-depths 3,4 --hosts standalone,server
```

### `tools/run_render_review_diff.py`

Either runs a new sweep or consumes an existing `sweep-manifest.json`, then emits one HTML sheet plus one PNG contact sheet for side-by-side review. Source: [run_render_review_diff.py](../tools/run_render_review_diff.py) → `tools/render_review/diff_review.py`.

```powershell
python tools/run_render_review_diff.py --profile pinwheel-depth-3 --patch-depths 3,4 --hosts standalone,server
python tools/run_render_review_diff.py --sweep-manifest output/render-review-sweeps/<run>/sweep-manifest.json
```

### `tools/run_family_sample_workbench.py`

Explores candidate representative samples for patch-depth topology families. Compares candidates structurally by count, connectivity, bounds, holes, and diagnostic validation, with optional browser review against injected candidate topology payloads. Source: [run_family_sample_workbench.py](../tools/run_family_sample_workbench.py) → `tools/render_review/family_sample_workbench.py`.

```powershell
python tools/run_family_sample_workbench.py --family shield --patch-depth 3
python tools/run_family_sample_workbench.py --family shield --patch-depth 3 --browser-review --host standalone
```

### `tools/run_geometry_cleanup_workbench.py`

Explores topology cleanup factors for image-derived patch-depth topology families. Compares cleanup candidates by overlap severity, bounds drift, and optional browser-visible gutter risk. Currently meaningful for `shield`. Source: [run_geometry_cleanup_workbench.py](../tools/run_geometry_cleanup_workbench.py) → `tools/render_review/geometry_cleanup_workbench.py`.

```powershell
python tools/run_geometry_cleanup_workbench.py --family shield --patch-depth 3
```

## Fixture and bootstrap regeneration

### `tools/regenerate_reference_fixtures.py`

Regenerates checked-in literature reference fixture JSON (rooted local-reference fixtures, canonical patch fixtures). Use when generator or verifier changes intentionally shift fixture expectations; review the resulting git diff carefully. Source: [regenerate_reference_fixtures.py](../tools/regenerate_reference_fixtures.py).

```powershell
py -3 tools/regenerate_reference_fixtures.py --all --mode both
```

### `tools/regenerate_frontend_topology_fixtures.py`

Regenerates checked-in frontend representative topology fixture JSON used by browser-visible geometry and palette tests. Supports `--check` mode (no writes, exit non-zero on drift) and `--fixture <name>` for a single target. Source: [regenerate_frontend_topology_fixtures.py](../tools/regenerate_frontend_topology_fixtures.py).

```powershell
python tools/regenerate_frontend_topology_fixtures.py --all --check
python tools/regenerate_frontend_topology_fixtures.py --fixture shield-depth-3
```

### `tools/export_bootstrap_data.py`

Exports the backend bootstrap payload (topology catalog, rule metadata, defaults) to a JSON path. Used by the standalone build pipeline to bake the bootstrap data into the bundle. Source: [export_bootstrap_data.py](../tools/export_bootstrap_data.py).

```powershell
py -3 tools/export_bootstrap_data.py <output-path>
```

## Test runners and introspection

### `tools/run-playwright.mjs`

Entrypoint for Playwright suites. Selects a suite by semantic name (`all`, `server`, `standalone`, `subset`, or per-feature), consults [tools/print_standalone_build_status.py](#toolsprint_standalone_build_statuspy) before rebuilding, and on Linux can repair missing browser libraries via `apt`/`dpkg-deb`. Wrapped by `npm run test:e2e:playwright[:server|:standalone|:subset]`. Source: [run-playwright.mjs](../tools/run-playwright.mjs).

```powershell
node ./tools/run-playwright.mjs --list-suites
node ./tools/run-playwright.mjs --suite server
node ./tools/run-playwright.mjs --suite standalone
```

### `tools/run_e2e.py`

Top-level orchestrator that runs frontend Vitest checks, the suite-integrity guard, a frontend build, and chunked Playwright subsets sequentially. Used in CI shard configurations. Source: [run_e2e.py](../tools/run_e2e.py).

```powershell
py -3 tools/run_e2e.py
```

### `tools/print_playwright_suite_manifest.py`

Prints the JSON suite manifest declared by [tests/e2e/playwright_suite_support.py](../tests/e2e/playwright_suite_support.py). Consumed by `run-playwright.mjs` to enumerate suites. Source: [print_playwright_suite_manifest.py](../tools/print_playwright_suite_manifest.py).

```powershell
py -3 tools/print_playwright_suite_manifest.py
```

### `tools/print_standalone_build_status.py`

Prints the JSON standalone build-status report (existence, manifest fingerprint, sources hash). Consumed by `run-playwright.mjs` to decide whether to reuse `output/standalone/` or rebuild. Source: [print_standalone_build_status.py](../tools/print_standalone_build_status.py).

```powershell
py -3 tools/print_standalone_build_status.py
```

### `tools/run_coverage.py`

Runs the backend `unit` suite, the `api` suite, or both under `coverage`, then combines and prints a report. Mirrors the CI workflow so contributors can reproduce the same backend coverage numbers locally. Supports `--fail-under <pct>` for a local threshold gate, `--xml <path>` for Cobertura output, and `--html <dir>` for an interactive report. Wrapped by `npm run coverage:backend`. Source: [run_coverage.py](../tools/run_coverage.py).

```powershell
py -3 tools/run_coverage.py
py -3 tools/run_coverage.py --suite unit
py -3 tools/run_coverage.py --fail-under 80
py -3 tools/run_coverage.py --xml output/coverage/coverage.xml --html output/coverage/html
```

## Supply-chain audit

### `tools/run_supply_chain_audit.py`

Runs `pip-audit` against `requirements.txt` and `requirements-dev.txt` and `npm audit` against `package-lock.json`, and emits a unified findings summary. Exits non-zero when either ecosystem reports a finding at or above the configured severity threshold (default: `high`). Wired into `npm run audit:supply-chain` and a nightly cron in [.github/workflows/supply-chain-audit.yml](../.github/workflows/supply-chain-audit.yml). Source: [run_supply_chain_audit.py](../tools/run_supply_chain_audit.py).

```powershell
py -3 tools/run_supply_chain_audit.py
py -3 tools/run_supply_chain_audit.py --ecosystem python
py -3 tools/run_supply_chain_audit.py --severity moderate --format json
py -3 tools/run_supply_chain_audit.py --ignore-pip-vuln PYSEC-2025-61
```

## Performance benchmarks

### `tools/bench_engine.py`

Microbenchmarks the simulation engine's optimized step path against a helper-driven reference path that approximates the pre-optimization implementation. Reports median ms and speedup per scenario across square Conway, hex Hexlife, triangle Trilife, multi-state Whirlpool/HexWhirlpool, and Archimedean 4.8.8 boards. Source: [bench_engine.py](../tools/bench_engine.py).

```powershell
py -3 tools/bench_engine.py
```

### `tools/profile_tiling_latency.py`

Profiles end-to-end latency for `build_topology` (cached and uncached), backend reset, backend toggle, and the full browser request roundtrip across a few representative topology cases. Spins up an `AppServer` and a real Playwright browser; useful when investigating perceived slowness on a specific tiling. Source: [profile_tiling_latency.py](../tools/profile_tiling_latency.py).

```powershell
py -3 tools/profile_tiling_latency.py
```

## Process cleanup

### `tools/dev_processes.py`

Inspects or kills repo-scoped browser/server helper processes (server-host, standalone-host, leaked Playwright child processes). Narrow cleanup fallback when a previous run left helpers behind. Source: [dev_processes.py](../tools/dev_processes.py).

```powershell
python tools/dev_processes.py list
python tools/dev_processes.py kill --port 5002
python tools/dev_processes.py kill --stale-browser-hosts
```

## See also

- [docs/MAINTENANCE.md](MAINTENANCE.md) — repo hygiene, guardrails, "Tooling Ownership" section for the render-review package layout
- [docs/TESTING.md](TESTING.md) — test strategy and the deep dive on browser diagnosis
- [docs/TESTING_TILINGS.md](TESTING_TILINGS.md) — tiling validation and verification workflow
- [docs/CODE_MAP.md](CODE_MAP.md) — runtime-oriented source guide
- [.pre-commit-config.yaml](../.pre-commit-config.yaml) — which tools run on commit/push
- [package.json](../package.json) — npm scripts that wrap these tools
