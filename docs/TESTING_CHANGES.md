# Testing Changes

Use this guide to choose focused tests for a change. The broader testing strategy lives in [TESTING.md](TESTING.md), and tiling-specific validation lives in [TESTING_TILINGS.md](TESTING_TILINGS.md).

## Baseline Checks

For most code changes, run the narrow checks that match the touched area plus any broader integration check needed for confidence.

Common baseline commands:

```powershell
npm run typecheck:frontend
npm run test:frontend
py -3 -m mypy --config-file mypy.ini
py -3 -m unittest discover -s tests/unit -p "test_*.py"
py -3 -m unittest discover -s tests/api -p "test_*.py"
```

Before release-oriented changes, also run the release-confidence commands in [README.md](../README.md) and [MAINTENANCE.md](MAINTENANCE.md).

## Example Test Choices

Use the smallest test set that proves the changed contract, then broaden when the change crosses a boundary:

```text
Change: add a pure rule with no UI preset
Run:    rule unit tests, simulation engine comparison, API rule metadata tests

Change: add a topology picker option
Run:    topology validation, registry tests, catalog/API tests, frontend geometry tests, Playwright picker flow

Change: change pattern import validation
Run:    parser tests, pattern import runtime tests, pattern IO tests, Playwright import/export flow
```

When adding a test, make the assertion describe the contract that could regress. For example, rule tests should assert transition behavior, not incidental canvas output:

```python
def test_rule_births_from_required_neighbor_count(self) -> None:
    rule = ExampleRule()
    ctx = build_context(
        0,
        neighbor_specs=[make_neighbor_spec(1, neighbor_id=f"n{index}") for index in range(3)],
    )

    self.assertEqual(rule.next_state(ctx), 1)
```

## If You Change A Rule

Run or update:

- direct unit tests for the rule behavior
- [tests/unit/test_simulation_engine.py](../tests/unit/test_simulation_engine.py)
- [tests/api/test_api_state_and_rules.py](../tests/api/test_api_state_and_rules.py) when metadata, defaults, randomization, or reset behavior changes
- frontend preset and pattern tests when presets or exported rule payloads change
- Playwright rule/picker or showcase tests when the browser flow changes

Suggested commands:

```powershell
py -3 -m unittest -q tests.unit.test_simulation_engine
py -3 -m unittest -q tests.api.test_api_state_and_rules
npm run test:frontend
npm run test:e2e:playwright:server
```

## If You Change A Topology

Run or update:

- topology construction and validation tests
- topology implementation registry tests
- catalog/API tests for default rule, sizing, adjacency, and patch-depth behavior
- tiling descriptor validation
- literature/reference verification when source-backed invariants exist
- frontend geometry, overlap, render-bounds, and fixture tests
- Playwright topology/persistence coverage for user-visible families

Suggested commands:

```powershell
py -3 tools\validate_tilings.py
py -3 tools\verify_reference_tilings.py
npm run fixtures:reference:check
npm run test:frontend -- frontend/geometry/polygon-overlap.test.ts frontend/geometry/render-bounds.test.ts
py -3 -m unittest -q tests.unit.test_topology_validation
py -3 -m unittest -q tests.api.test_api_state_and_rules
npm run test:e2e:playwright:server
```

## If You Change Presets Or Patterns

Run or update:

- preset listing and seed tests
- pattern parser/import/export tests
- pattern import runtime tests
- browser pattern/showcase tests when the visible flow changes

Suggested commands:

```powershell
npm run test:frontend -- frontend/presets.test.ts frontend/pattern-io.test.ts frontend/actions/pattern-import-runtime.test.ts
py -3 -m unittest -q tests.e2e.test_playwright_pattern_and_showcase
```

## If You Change Frontend UI Or Controls

Run or update:

- TypeScript type checking
- frontend unit tests for control models, bindings, session state, actions, and parsers
- Playwright tests for rendered workflows that jsdom cannot prove
- bundle-size checks when shell markup, CSS, or standalone output grows

Suggested commands:

```powershell
npm run typecheck:frontend
npm run test:frontend
npm run build:frontend
npm run build:frontend:standalone
py -3 tools\check_bundle_size.py
npm run test:e2e:playwright:server
```

## If You Change Backend HTTP Or Persistence

Run or update:

- request model and payload contract tests
- API tests
- persistence, restore, transition planner, service, and coordinator tests
- browser tests when the visible workflow depends on the route behavior

Suggested commands:

```powershell
py -3 -m mypy --config-file mypy.ini
py -3 -m unittest discover -s tests/unit -p "test_*request*.py"
py -3 -m unittest discover -s tests/api -p "test_*.py"
npm run test:e2e:playwright:server
```

## If You Change Standalone Runtime Or Build Output

Run or update:

- standalone build
- standalone smoke test
- bundle-size check
- standalone Playwright suite
- provenance-related tests when build manifests or runtime metadata change

Suggested commands:

```powershell
npm run build:frontend:standalone
npm run smoke:standalone
py -3 tools\check_bundle_size.py
npm run test:e2e:playwright:standalone
```

## Updating Tests

- Prefer the cheapest test layer that proves the behavior.
- Keep tests close to the boundary they protect: pure logic in unit tests, HTTP contracts in API tests, real interaction flows in Playwright.
- Update expected fixtures only through repo-owned regeneration tools.
- When changing a test because UI structure moved, confirm the new selector describes the intended user-visible control.
- If a known limitation changes, update the relevant docs in the same change.

## Checklist

- The test layer matches the changed contract: unit for pure logic, API for payloads, Playwright for browser workflows.
- Expected fixtures were regenerated with repo-owned commands, not edited by hand.
- Selectors describe stable user-visible controls when browser tests change.
- Docs for known limitations, release notes, or developer workflows changed with the behavior they describe.
- The commands run locally are recorded in the final change summary or PR description.
