# Adding Rules

Use this guide when adding a new automaton rule or changing how an existing rule evolves cell state. For broader runtime context, see [ARCHITECTURE.md](ARCHITECTURE.md) and [CODE_MAP.md](CODE_MAP.md).

## What A Rule Owns

A rule owns metadata, paintable states, optional randomization weights, and `next_state(ctx)` behavior. It should not know how the board is rendered or how HTTP requests are handled. The same rule protocol is used across regular grids, mixed periodic tilings, and finite aperiodic patches.

Rules receive a topology-aware `RuleContext`, so they should ask for neighbors through context methods instead of assuming grid coordinates.

## Files To Inspect

- [backend/rules/base.py](../backend/rules/base.py): `AutomatonRule`, `CellStateDefinition`, and the universal rule protocol.
- [backend/rules/conway.py](../backend/rules/conway.py): small binary Life-like example.
- [backend/rules/whirlpool.py](../backend/rules/whirlpool.py): multi-state example.
- [backend/rules/wireworld.py](../backend/rules/wireworld.py): signal/circuit-style example.
- [backend/rules/__init__.py](../backend/rules/__init__.py): rule registry and aliases.
- [backend/simulation/rule_context_queries.py](../backend/simulation/rule_context_queries.py): neighbor and geometry queries available to rules.

## Add A Rule

1. Create a module under [backend/rules](../backend/rules), usually one class that subclasses `AutomatonRule`.
2. Set the rule metadata:
   - `name`: stable machine-readable id, usually lowercase kebab-case.
   - `display_name`: UI-facing name.
   - `description`: short rule description.
   - `states`: tuple of `CellStateDefinition` values.
   - `default_paint_state`: state selected for painting by default.
   - `randomize_weights`: optional state weights for random reset.
3. Implement `next_state(ctx)`.
   - Use `ctx.current_state` for the current cell.
   - Use `ctx.count_live_neighbors()`, `ctx.count_neighbors(...)`, `ctx.neighbor_states()`, or directional helpers for neighbor behavior.
   - Return a valid state value declared in `states`.
4. Add the class to `RULE_TYPES` in [backend/rules/__init__.py](../backend/rules/__init__.py).
5. If a topology should default to the new rule, update the catalog default rule metadata in [backend/simulation/topology_family_manifest.py](../backend/simulation/topology_family_manifest.py).
6. If the rule needs demos or seeds, add presets separately through [ADDING_PRESETS_AND_PATTERNS.md](ADDING_PRESETS_AND_PATTERNS.md).

## Small Example

This is intentionally abbreviated. Use it to check the shape of a rule module, not as a full design pattern for every rule:

```python
from backend.rules.base import AutomatonRule, CellStateDefinition
from backend.simulation.rule_context import RuleContext


class ExamplePulseRule(AutomatonRule):
    name = "example-pulse"
    display_name = "Example Pulse"
    description = "A tiny three-state example for contributor documentation."
    states = (
        CellStateDefinition(0, "Resting", "#f8f1e5"),
        CellStateDefinition(1, "Excited", "#e4572e"),
        CellStateDefinition(2, "Cooling", "#5b8def"),
    )
    default_paint_state = 1
    randomize_weights = {0: 0.92, 1: 0.08}

    def next_state(self, ctx: RuleContext) -> int:
        if ctx.current_state == 1:
            return 2
        if ctx.current_state == 2:
            return 0
        return 1 if ctx.count_neighbors(1) > 0 else 0
```

Then register the rule class:

```python
from backend.rules.example_pulse import ExamplePulseRule

RULE_TYPES: tuple[type[AutomatonRule], ...] = (
    # existing rules...
    ExamplePulseRule,
)
```

For direct transition tests, prefer the existing helpers in [tests/unit/test_simulation_rules.py](../tests/unit/test_simulation_rules.py) when they fit. The important part is to assert behavior through `next_state(ctx)` or through `SimulationEngine.step_board(...)`, not through renderer state:

```python
def test_example_pulse_excites_next_to_excited_neighbor(self) -> None:
    rule = ExamplePulseRule()
    ctx = build_context(
        0,
        neighbor_specs=[make_neighbor_spec(1, neighbor_id="n0")],
    )

    self.assertEqual(rule.next_state(ctx), 1)
```

## Tests To Add Or Update

- Add direct rule tests when the transition logic is not already covered by a generic engine case.
- Extend [tests/unit/test_simulation_engine.py](../tests/unit/test_simulation_engine.py) when optimized stepping should be compared with reference context evaluation.
- Update [tests/api/test_api_state_and_rules.py](../tests/api/test_api_state_and_rules.py) when rule registry metadata, default rules, or reset behavior changes.
- Update frontend tests only when the rule changes presets, palette assumptions, UI metadata, or pattern behavior.
- Add Playwright coverage only for browser-visible flows such as picker behavior, presets, showcase demos, or painting/export behavior.

Useful commands:

```powershell
npm run test:frontend
py -3 -m unittest -q tests.unit.test_simulation_engine
py -3 -m unittest -q tests.api.test_api_state_and_rules
py -3 -m mypy --config-file mypy.ini
```

## Common Pitfalls

- Do not assume a square grid or fixed neighbor count unless the rule is intentionally limited by default-rule assignment and tests.
- Do not return a state that is missing from `states`; export, rendering, and validation paths expect declared state values.
- Keep randomization weights sparse and intentional. A state can be valid without being a random-reset candidate.
- Prefer a new rule id over changing the meaning of an existing id when saved patterns may depend on the old behavior.

## Checklist

- Implementation is in [backend/rules](../backend/rules) and uses `RuleContext` queries for topology-aware behavior.
- Rule metadata declares every returned state and the intended paint/default/randomize behavior.
- Rule is registered in [backend/rules/__init__.py](../backend/rules/__init__.py).
- Defaults, presets, or patterns are updated only when the new rule should affect those flows.
- Focused unit/API/frontend/browser tests were added or intentionally skipped based on the changed surface.
