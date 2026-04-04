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

## Recommended Workflow

1. Change generator, verifier, or spec.
2. Run `py -3 tools/validate_tilings.py`.
3. Run `py -3 tools/verify_reference_tilings.py`.
4. If signatures changed intentionally, update the spec and rerun.
5. Run the focused verifier unit test.
6. Run the full backend regression sweep.

## Notes

- Regular and periodic families are verified on canonical `3x3` samples.
- Aperiodic families are verified on patch-depth samples.
- Pinwheel has an exact-affine verification path and should not be treated like the other families when debugging verification failures.
