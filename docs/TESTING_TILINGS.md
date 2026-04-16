# Testing Tilings

This file is the quick guide for validating tiling work.

## Core Commands

### 1. Geometric sanity

```powershell
py -3 tools/validate_tilings.py
```

Use this first. It tells you whether the catalog tilings build and pass the topology validator.

### 2. Literature verification

```powershell
py -3 tools/verify_reference_tilings.py
```

Use this second. It checks the canonical samples against the source-backed invariants in `backend/simulation/literature_reference_specs.py`.

It now also checks that canonical samples are contiguous in the topology neighbor graph. That means `verify_reference_tilings.py` can fail even when `validate_tilings.py` still passes, because graph contiguity is now treated as a literature-backed invariant rather than only a shared-validator option.

It also now checks that canonical samples do not enclose empty holes in the merged topology surface. That means a tiling can be connected and overlap-free, yet still fail literature verification if it forms a ring of cells around bounded empty gaps.

For periodic families, it also checks periodic-face descriptor semantics, exact interior vertex-star sets/frequencies, and selected reciprocal dual-family invariants. For strengthened substitution families, it can also check exact polygon-area frequencies and rooted local-reference fixtures rather than relying only on counts/signatures.

### 3. Focused verifier unit tests

```powershell
py -3 -m unittest -q tests.unit.test_literature_reference_verification
```

Use this when changing verifier behavior, specs, or signatures.

### 4. Full backend regression sweep

```powershell
py -3 -m unittest discover -s tests/unit -p "test_*.py"
py -3 -m unittest discover -s tests/api -p "test_*.py"
py -3 -m mypy --config-file mypy.ini
```

Use this before committing verifier or generator changes.

### 5. Polygon no-overlap checks

```powershell
py -3 -m unittest -q tests.unit.test_topology_validation
npm run test:frontend
```

Use these when a tiling looks visually stacked or suspicious. The backend test catches topology-space polygon overlap with Shapely, and the frontend suite now includes adapter-space overlap checks using the same transformed polygons the canvas renderer fills.

`recommended_validation_options(...)` now keeps overlap checks globally strict, even for the aperiodic families that still relax other shared-surface checks.

The frontend adapter-space overlap helper is intentionally looser than the backend check: its current positive-area epsilon is `1e-4`, and it now compares overlap area across multiple snapped precisions so known-good exact-path families such as `pinwheel` do not fail on polygon-clipping noise.

Representative render-space overlap checks also dedupe exact rendered duplicate polygons by geometry rather than by `cell.id`, so families such as `robinson-triangles` can be checked cleanly even when the frontend fixture still reuses ids across identical rendered shapes.

### 6. Verification-strength report

```powershell
py -3 tools/report_tiling_verification_strength.py
```

Use this when you want a quick per-family summary of which invariant layers are currently active, such as descriptor checks, local-reference fixtures, exact-path verification, or strict validation.

### 7. Browser-visible geometry sanity

```powershell
npm run test:frontend -- frontend/geometry/polygon-overlap.test.ts frontend/geometry/render-bounds.test.ts
```

Use these when you need a browser-side sanity pass on representative rendered fixtures, not just backend topology-space geometry.

The checked-in representative fixture set now includes `spectre`, `taylor-socolar`, and `sphinx` at depth `3`, so both render-bounds and adapter-space overlap coverage now span the full current aperiodic representative set rather than only the previously strengthened families.

### 8. Reference fixture drift check

```powershell
npm run fixtures:reference:check
```

Use this when generator or verifier changes may affect checked-in rooted local-reference or canonical patch fixtures. It reports fixture drift without rewriting the JSON files. To intentionally update fixtures, run `py -3 tools/regenerate_reference_fixtures.py --all --mode both` and review the resulting git diff.

### 9. Visual review

```powershell
python tools/render_canvas_review.py --list-profiles
python tools/render_canvas_review.py --profile pinwheel-depth-3
python tools/render_canvas_review.py --profile pinwheel-depth-3 --reference .\docs\images\pinwheel-reference.png
python tools/run_browser_check.py --host standalone --render-review --profile pinwheel-depth-3
python tools/run_browser_check.py --host server --unittest tests.e2e.playwright_case_suite.CellularAutomatonUITests.test_pinwheel_topology_switch_renders_aperiodic_patch
python tools/run_browser_check.py --host server --success-artifacts --unittest tests.e2e.playwright_case_suite.CellularAutomatonUITests.test_pinwheel_topology_switch_renders_aperiodic_patch
```

Use these when the open question is visual rather than topological:

- `render_canvas_review.py` is the preferred path for producing a real canvas PNG plus JSON metrics from the browser render path.
- `run_browser_check.py` is the preferred path when you need the same browser review or a targeted Playwright test with owned host startup, cleanup, logs, and a run manifest.
- npm Playwright entrypoints remain the preferred full-suite path when you want broad browser regression coverage rather than one focused diagnosis.

Output locations:

- successful render review: `output/render-review/`
- managed `run_browser_check.py --render-review`: `output/browser-check/<timestamp-mode-host>/`
- direct render-review failure artifacts: `output/render-review-artifacts/`
- managed runner manifests and artifacts: `output/browser-check/<timestamp-mode-host>/`
- managed `run_browser_check.py --unittest --success-artifacts`: `output/browser-check/<timestamp-mode-host>/test-artifacts/`

## How To Read Failures

- `validate_tilings.py` fails
  - likely generator bug
  - possibly topology validation options are too strict or too loose for that family
- `verify_reference_tilings.py` fails
  - generator drift
  - wrong source-backed invariant
  - stale expected signature after an intentional generator change
  - canonical sample is disconnected in the topology graph even though geometry sanity still passes
  - canonical sample leaves enclosed empty holes even though connectivity and overlap checks still pass
- `test_literature_reference_verification` fails
  - spec coverage mismatch
  - verifier behavior changed
  - signature or sample-mode expectation changed
- overlap-focused topology/frontend tests fail
  - real positive-area overlap between polygons
  - geometry adapter transform drift
  - render-space numeric tolerance is too tight for an exact-path family such as `pinwheel`
- render-bounds tests fail
  - rendered geometry is collapsing or stretching relative to the source topology
  - geometry adapter metrics changed in a way that the backend topology validator cannot see

## Recommended Workflow

1. Change generator, verifier, or spec.
2. Run `py -3 tools/validate_tilings.py`.
3. Run `py -3 tools/verify_reference_tilings.py`.
4. If signatures changed intentionally, update the spec and rerun.
5. Run the focused verifier unit test.
6. Run the full backend regression sweep.
7. If a tiling looks stacked or obscured, run the overlap-focused backend/frontend checks too.

## Notes

- Regular and periodic families are verified on canonical `3x3` samples.
- Periodic families now read their canonical sample size from the reference spec; the current shipped catalog still uses `3x3`.
- Aperiodic families are verified on patch-depth samples.
- Several strengthened substitution families also use checked-in rooted local-reference fixtures.
- Pinwheel has an exact-affine verification path and derives contiguity from exact positive-length segment-overlap neighbors, so it should not be treated like the other families when debugging verification failures.
- The strongest “tiles do not obscure each other” check is now split across backend topology-space overlap detection and frontend adapter-space overlap detection.
- Canonical-sample contiguity is now part of literature verification, so a family can be geometrically sane but still blocked if its neighbor graph splits into multiple components.
- Canonical-sample hole freedom is now part of literature verification too, so a family can be connected and overlap-clean but still blocked if it surrounds bounded empty regions.
