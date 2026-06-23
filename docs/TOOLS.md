# Tools Reference

Generated from the `python -m tools ...` command registry. Edit the CLI metadata, not this file by hand.

Before hand-rolling a script for repo maintenance, prefer the commands below (run `python -m tools --help` to discover the full surface). They carry guardrails a bespoke script would bypass: transactional installs, the `generated-check` freshness gate, deterministic regeneration, and bundle-budget accounting. Regenerate generated artifacts (catalog aggregate, palette manifest, preview data, bootstrap fixture, this file) rather than editing them by hand.

For npm convenience aliases, see the `scripts` block in [package.json](../package.json).

## Build

Build and inspect standalone frontend artifacts.

### `python -m tools build standalone`

Build the standalone bundle into `output/standalone/` and write a build manifest.

Python-first replacement for the old standalone build script. It stages the standalone shell, runs Vite, writes bootstrap data, bundles backend/config Python sources, and records source provenance in `build-manifest.json`.

```powershell
python -m tools build standalone
```

### `python -m tools build standalone-shell`

Render the standalone HTML shell to stdout or a file.

Useful when inspecting the shared standalone wrapper independently from a full build.

```powershell
python -m tools build standalone-shell
python -m tools build standalone-shell output/.standalone-build-input/standalone.html
```

### `python -m tools build bundle-size`

Check standalone bundle budgets and emit optional JSON or text reports.

Runs the standalone bundle budget gate against `output/standalone/` and supports baseline comparisons for CI/history tracking.

```powershell
python -m tools build bundle-size
python -m tools build bundle-size --format json
```

## Rules

Render and inspect automaton rule evolution.

### `python -m tools rules review`

Render selected generations for one rule, topology, and seed.

Backend-only rule troubleshooting helper that writes per-generation PNG frames, a montage, and a JSON summary with state counts, changed-cell counts, and live-cell bounds. Supports binary seeds, named geometric patterns, cells-by-id JSON, and square Whirlpool presets.

```powershell
python -m tools rules review --rule whirlpool --preset anchored-source-vortex --generations 0,5,15,30
python -m tools rules review --rule conway --pattern glider --width 40 --height 30
```

## Tilings

Validate, verify, preview, sketch, and scaffold tilings.

### `python -m tools tilings validate`

Run geometry/topology validation across catalog tilings.

Traverses every registered mixed and aperiodic catalog geometry and performs cheap sanity validation for topology structure, adjacency, holes, and edge multiplicity.

```powershell
python -m tools tilings validate
```

### `python -m tools tilings verify`

Run literature-backed reference verification across tiling families.

Traverses the full registered catalog and applies stricter verification than `tilings validate`, including required reference specs, signatures, fixtures, and connectivity invariants.

```powershell
python -m tools tilings verify
```

### `python -m tools tilings report`

Report per-family verification strength in summary, detail, or JSON format.

Aggregates implementation contracts, fixture coverage, and live verification results.

```powershell
python -m tools tilings report
python -m tools tilings report --format detail
```

### `python -m tools tilings preview`

Generate preview polygon data for the tiling picker.

Supports periodic and aperiodic preview generation and discovery via `--list`. Aperiodic families require the `--aperiodic` flag (the default mode reads periodic-face descriptors).

```powershell
python -m tools tilings preview --list
python -m tools tilings preview --geometry kisrhombille
python -m tools tilings preview --aperiodic --geometry hat-monotile --write
```

### `python -m tools tilings sketch`

Sketch and validate a candidate periodic tiling without wiring it into the catalog.

Builds a patch from a sketch file, reports topology/geometry issues, and can emit SVG/JSON/reference-spec outputs.

```powershell
python -m tools tilings sketch tools/sketch_examples/triangular_square_2uniform.py
python -m tools tilings sketch path/to/sketch.py --svg out.svg --json out.json
```

### `python -m tools tilings inspect-svg`

Inspect polygon geometry and translation candidates in a reference SVG.

Classifies straight-sided polygons, reports repeated center translations, and can emit a normalized editable sketch starter.

```powershell
python -m tools tilings inspect-svg reference.svg
python -m tools tilings inspect-svg reference.svg --sketch-output output/starter.py
```

### `python -m tools tilings add-periodic`

Install a validated periodic sketch across catalog and generated surfaces.

Writes the descriptor, reference spec, permanent sketch, and authoritative per-tiling metadata, then regenerates the server aggregate, palette, preview, bootstrap fixture, and budget headroom as one rollback-safe operation. Supports --dry-run, --check, and --reconcile.

```powershell
python -m tools tilings add-periodic sketch.py --source-url https://example.org/reference.svg --picker-order 250 --dry-run
python -m tools tilings add-periodic sketch.py --source-url https://example.org/reference.svg --picker-order 250 --reconcile
python -m tools tilings add-periodic tools/sketch_examples/example.py --check
```

### `python -m tools tilings regenerate-catalog`

Rebuild every periodic catalog surface after rebases.

Validates one-to-one descriptor, metadata, and reference-spec discovery, then deterministically rebuilds the server aggregate, palettes, previews, standalone bootstrap metadata, and bootstrap bundle-budget headroom while preserving handwritten reference specs.

```powershell
python -m tools tilings regenerate-catalog --dry-run
python -m tools tilings regenerate-catalog
python -m tools tilings regenerate-catalog --check
```

### `python -m tools tilings scaffold-aperiodic`

Scaffold the boilerplate for a new aperiodic tiling family.

Creates the generator skeleton, reference spec, tests, and registry/manifest inserts before real geometry is implemented.

```powershell
python -m tools tilings scaffold-aperiodic --family-id widget-monotile --label "Widget Monotile" --kind widget --source-url https://example.org/widget
```

### `python -m tools tilings compare`

Compare one seed under one rule across many tilings.

Maps a seed onto each topology through a canonical traversal (`bfs` rings by default), runs the same rule, and reports population, end-state classification, and a degenerate-seed guard. Supports `--rule`, `--traversal`, `--steps`, `--grid-size`, `--geometries`, and JSON output.

```powershell
python -m tools tilings compare
python -m tools tilings compare "01100 11000 01000" --rule conway --steps 80
python -m tools tilings compare --geometries square,hex,kagome --format json
```

## Fixtures

Regenerate or check checked-in fixture files.

### `python -m tools fixtures reference`

Regenerate or check literature reference fixtures.

Supports `--check`, `--all`, targeted geometry/depth regeneration, and discovery with `--list-targets`.

```powershell
python -m tools fixtures reference --all --mode both --check
python -m tools fixtures reference --mode canonical --geometry pinwheel --depth 3
```

### `python -m tools fixtures frontend`

Regenerate or check frontend representative topology fixtures.

Supports `--check`, `--all`, targeted fixture names, and discovery with `--list-fixtures`.

```powershell
python -m tools fixtures frontend --all --check
python -m tools fixtures frontend --fixture shield-depth-3
```

## Bootstrap

Export bootstrapped backend metadata for standalone mode.

### `python -m tools bootstrap export`

Export the backend bootstrap payload to JSON.

Writes topology catalog, rule metadata, and canonical defaults to a file for standalone/runtime consumers.

```powershell
python -m tools bootstrap export frontend/test-fixtures/bootstrap-data.json
```

## Browser

Run browser-backed reviews, sweeps, workbenches, and smoke checks.

### `python -m tools browser review`

Render one topology through the real browser canvas path and emit PNG/JSON artifacts.

Supports named profiles, literature review, cached references, and visual metrics. Use `--list-profiles` for discovery.

```powershell
python -m tools browser review --list-profiles
python -m tools browser review --profile pinwheel-depth-3
```

### `python -m tools browser check`

Own browser host startup/cleanup around one render review or targeted unittest.

Managed runner for server or standalone browser checks with artifact manifests and failure bundling.

```powershell
python -m tools browser check --host standalone --render-review --profile pinwheel-depth-3
python -m tools browser check --host server --unittest tests.e2e.playwright_case_suite.CellularAutomatonUITests.test_chair_topology_switch_renders_aperiodic_patch
```

### `python -m tools browser sweep`

Run a small matrix of comparable render-review cases.

Expands a render-review profile across hosts, themes, or sizes and writes one sweep manifest plus case artifacts.

```powershell
python -m tools browser sweep --profile shield-depth-3 --hosts standalone,server
```

### `python -m tools browser diff`

Build an HTML/PNG comparison sheet from a sweep or by running a new sweep.

Useful when reviewing host/theme/depth differences side by side.

```powershell
python -m tools browser diff --profile pinwheel-depth-3 --patch-depths 3,4 --hosts standalone,server
python -m tools browser diff --sweep-manifest output/render-review-sweeps/<run>/sweep-manifest.json
```

### `python -m tools browser workbench-samples`

Explore candidate representative samples for patch-depth families.

Compares structural candidates and can optionally inject them into a browser-backed render review.

```powershell
python -m tools browser workbench-samples --family shield --patch-depth 3
python -m tools browser workbench-samples --family shield --patch-depth 3 --browser-review --host standalone
```

### `python -m tools browser workbench-cleanup`

Explore cleanup-factor candidates for image-derived patch-depth families.

Compares overlap severity, bounds drift, and optional browser-visible gutter risk.

```powershell
python -m tools browser workbench-cleanup --family shield --patch-depth 3
python -m tools browser workbench-cleanup --family shield --patch-depth 3 --browser-review --host standalone
```

### `python -m tools browser smoke-standalone`

Run the standalone smoke test against a prebuilt bundle.

Launches headless Chromium, waits for bootstrap readiness, and fails on unexpected startup errors.

```powershell
python -m tools browser smoke-standalone
python -m tools browser smoke-standalone --format json --output output/standalone-smoke.json
```

## Tests

Run Playwright suites, backend coverage, and standalone build introspection.

### `python -m tools test e2e`

Run Playwright suites through the Python CLI, or run the broader local e2e orchestrator.

Use `--list-suites` to inspect suite names, `--suite` to run a specific suite, or `--orchestrated` to run the old frontend-plus-chunked-playwright workflow.

```powershell
python -m tools test e2e --list-suites
python -m tools test e2e --suite server
python -m tools test e2e --orchestrated
```

### `python -m tools test coverage`

Run backend coverage for the unit suite, API suite, or both.

Mirrors the CI coverage flow and supports XML/HTML outputs plus `--fail-under`.

```powershell
python -m tools test coverage
python -m tools test coverage --suite unit --fail-under 80
```

### `python -m tools test playwright-suites`

Print the public Playwright suite manifest.

Structured replacement for the old manifest-print helper.

```powershell
python -m tools test playwright-suites
python -m tools test playwright-suites --format names
```

### `python -m tools test standalone-build-status`

Print standalone build freshness and provenance status.

Reports whether `output/standalone/` is current for standalone-backed browser workflows.

```powershell
python -m tools test standalone-build-status
python -m tools test standalone-build-status --format summary
```

## Security

Run privacy, secret-scanning, and supply-chain checks.

### `python -m tools security privacy`

Scan tracked repo files for personal-information leaks.

Supports pre-commit filename arguments or full-repo mode with `--all-files`.

```powershell
python -m tools security privacy --all-files
python -m tools security privacy README.md docs/TOOLS.md
```

### `python -m tools security secrets`

Run `detect-secrets` against changed files or the full tracked repo.

Wrapper around the repo baseline with the same changed-file/full-repo split used in pre-commit.

```powershell
python -m tools security secrets --baseline .secrets.baseline --all-files
```

### `python -m tools security supply-chain`

Run the combined Python and npm supply-chain audit.

Runs `pip-audit` plus `npm audit` and can emit summary or JSON findings.

```powershell
python -m tools security supply-chain
python -m tools security supply-chain --severity moderate --format json
```

## Performance

Run engine and topology performance investigations.

### `python -m tools perf bench`

Run engine microbenchmarks across representative rule/topology scenarios.

Benchmarks the optimized engine path against a reference-style helper path.

```powershell
python -m tools perf bench
```

### `python -m tools perf latency`

Profile topology-build, backend-mutation, and browser-roundtrip latency.

Uses a real Playwright browser and server host for end-to-end timing investigations.

```powershell
python -m tools perf latency
```

## Repo

Run repo-level maintenance commands.

### `python -m tools repo processes`

Inspect or clean up repo-scoped helper processes.

Lists or kills server/standalone/browser helper processes and their ports. On Windows, discovery uses PowerShell process and listening-port data instead of procfs.

```powershell
python -m tools repo processes list
python -m tools repo processes kill --stale-browser-hosts
python -m tools repo processes kill --port 5000
```

### `python -m tools repo cleanup`

Clean up stale repo-owned local app/browser host processes.

Shortcut for the common localhost-refused case. With no flags it cleans up stale server and standalone hosts; pass `--port` or `--repo` for a more specific or broader cleanup.

```powershell
python -m tools repo cleanup
python -m tools repo cleanup --port 5000
python -m tools repo cleanup --repo
```

### `python -m tools repo python-style`

Run repo-owned Ruff style commands for Python sources.

Supports `check`, `format-check`, and `format` over the repo Python surface.

```powershell
python -m tools repo python-style check
python -m tools repo python-style format-check
```

### `python -m tools repo tools-docs`

Generate or check `docs/TOOLS.md` from the CLI registry.

Use `--check` in tests/CI and `--write` when intentionally refreshing the generated tools reference.

```powershell
python -m tools repo tools-docs --check
python -m tools repo tools-docs --write
```

### `python -m tools repo generated-check`

Run freshness checks for generated repo-owned files.

Umbrella check for generated surfaces that otherwise require separate commands: tools docs, bootstrap test fixture data, frontend topology fixtures, and reference fixtures. Focused commands remain available for targeted refreshes.

```powershell
python -m tools repo generated-check
python -m tools repo generated-check --only tools-docs
```

### `python -m tools repo release-check`

Check release readiness before publishing and verify publication afterward.

Guards the preview-release handoff so a merged release PR is not mistaken for a published GitHub tag/release. Use `--phase pre-publish` before tagging and `--phase post-publish` after creating the GitHub Release.

```powershell
python -m tools repo release-check --version v0.4.0 --phase pre-publish
python -m tools repo release-check --version v0.4.0 --phase post-publish
```
