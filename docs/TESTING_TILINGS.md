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

## How To Read Failures

- `validate_tilings.py` fails
  - likely generator bug
  - possibly topology validation options are too strict or too loose for that family
- `verify_reference_tilings.py` fails
  - generator drift
  - wrong source-backed invariant
  - stale expected signature after an intentional generator change
- `test_literature_reference_verification` fails
  - spec coverage mismatch
  - verifier behavior changed
  - signature or sample-mode expectation changed
- overlap-focused topology/frontend tests fail
  - real positive-area overlap between polygons
  - geometry adapter transform drift
  - render-space numeric tolerance is too tight for an exact-path family such as `pinwheel`

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
- Aperiodic families are verified on patch-depth samples.
- Pinwheel has an exact-affine verification path and should not be treated like the other families when debugging verification failures.
- The strongest “tiles do not obscure each other” check is now split across backend topology-space overlap detection and frontend adapter-space overlap detection.
