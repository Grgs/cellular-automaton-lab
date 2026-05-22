# Onboarding

Decision tree for first-time contributors. Find the row that matches what you
want to do; follow the link.

| I want to... | Start here |
|---|---|
| **Run the app locally** | [§ Run locally](#run-locally) |
| **Try the topology library from Python** | [`examples/`](../examples/README.md) |
| **Add a new tiling family** | [`docs/ADDING_TOPOLOGIES.md`](ADDING_TOPOLOGIES.md) |
| **Add a new automaton rule** | [`docs/ADDING_RULES.md`](ADDING_RULES.md) |
| **Add a preset or pattern** | [`docs/ADDING_PRESETS_AND_PATTERNS.md`](ADDING_PRESETS_AND_PATTERNS.md) |
| **Verify a tiling against a literature spec** | [`examples/verify_against_spec.py`](../examples/verify_against_spec.py) + [`docs/TILING_VERIFICATION_STATUS.md`](TILING_VERIFICATION_STATUS.md) |
| **Understand the architecture** | [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) |
| **Find a specific file** | [`docs/CODE_MAP.md`](CODE_MAP.md) |
| **Run / debug tests** | [`docs/TESTING.md`](TESTING.md) |
| **Maintain the repo (releases, fixtures, CI)** | [`docs/MAINTENANCE.md`](MAINTENANCE.md) |

The rest of this document gives the shortest possible path through each of
the most common scenarios.

---

## Run locally

You need Python 3.13+ and Node 22+. From the repo root:

```
# one-time setup
python -m venv .venv
.venv/Scripts/activate                       # Windows: .venv\Scripts\activate.bat
pip install -r requirements-dev.txt
npm install

# every time
npm run build:frontend                       # build the Vite bundle
python app.py                                # start Flask on http://127.0.0.1:5000
```

For active frontend work, run `npm run dev:frontend` in a second terminal --
it rebuilds the bundle on change while `python app.py` serves the latest
artifact.

Want to skip the local server and just see the app? Open the
[live standalone demo](https://grgs.github.io/cellular-automaton-lab/).

## Use the topology library from Python

The catalog of 37 tilings + the simulation engine work as a plain Python
library; you don't need Flask or the frontend to drive them.

```python
from backend.simulation.topology import build_topology, board_from_cells_by_id
from backend.simulation.engine import SimulationEngine
from backend.rules import ConwayLifeRule

# any catalog geometry works the same way -- "hex", "pinwheel", "shield", ...
board = board_from_cells_by_id("square", width=5, height=5,
                                cells_by_id={"c:1:2": 1, "c:2:2": 1, "c:3:2": 1})

engine = SimulationEngine()
rule = ConwayLifeRule()
for _ in range(10):
    board = engine.step_board(board, rule)
print(sum(board.cell_states), "live cells")
```

Every script in [`examples/`](../examples/README.md) is a complete,
self-contained variation of this pattern. Read those first if you want to
poke at one specific subsystem (geometry, simulation, verification,
rendering) in isolation.

## Add a new tiling family

After recent refactoring this is roughly a 5-file change. The walkthrough is
[`docs/ADDING_TOPOLOGIES.md`](ADDING_TOPOLOGIES.md). High-level shape:

1. Generator: `backend/simulation/aperiodic_<family>.py` (or extend an
   existing one) -- pure function from depth to cell records.
2. Manifest entry: `backend/simulation/aperiodic_family_manifest.py`.
3. Registry: `backend/simulation/aperiodic_registry.py` -- wire the generator
   to the geometry key.
4. Reference spec: a file in `backend/simulation/reference_specs/aperiodic/`
   -- depth/kind expectations + literature URLs.
5. Palette entry: `frontend/canvas/family-dead-palette-manifest.json`.

Then regenerate fixtures + bootstrap data:

```
python tools/regenerate_reference_fixtures.py --mode canonical --geometry <name> --depth 1
python tools/regenerate_reference_fixtures.py --mode canonical --geometry <name> --depth 3
python tools/regenerate_frontend_topology_fixtures.py --fixture <name>-depth-3
python tools/export_bootstrap_data.py frontend/test-fixtures/bootstrap-data.json
python tools/generate_tiling_preview.py --aperiodic --geometry <name>  # paste into tiling-preview-data.ts
```

Final check: `python tools/validate_tilings.py` and `python tools/verify_reference_tilings.py`.

## Add a new automaton rule

Most rules subclass `backend.rules.base.AutomatonRule` and implement
`next_state(ctx) -> int`. The walkthrough is in
[`docs/ADDING_RULES.md`](ADDING_RULES.md); examples in `backend/rules/conway.py`
and `backend/rules/hexlife.py` are the closest reference.

## Run tests

| | Command |
|---|---|
| Backend unit tests | `python -m pytest tests/unit` |
| Backend API tests | `python -m pytest tests/api` |
| Frontend unit tests | `npm run test:frontend` |
| Frontend lint suite | `npm run lint:frontend` |
| Linkinator + doc links | `npm run check:doc-links` |
| Mypy | `python -m mypy --config-file mypy.ini` |
| Full reference verification | `python tools/verify_reference_tilings.py` |
| Tiling validation | `python tools/validate_tilings.py` |
| Playwright (browser) | `npm run test:e2e:playwright` |

[`docs/TESTING.md`](TESTING.md) covers the per-suite conventions in detail.

## What I shouldn't do unless I've read more

- **Don't edit the bootstrap-data.json directly** -- it's generated; regenerate
  with `python tools/export_bootstrap_data.py frontend/test-fixtures/bootstrap-data.json`.
- **Don't edit the canonical reference fixtures by hand** -- same; use
  `tools/regenerate_reference_fixtures.py`.
- **Don't promote an aperiodic family out of `Experimental` without manual
  visual review** against the published substitution. The pinwheel and
  pinwheel-2-1 entries are intentionally gated this way; see
  [`docs/TILING_KNOWN_DEVIATIONS.md`](TILING_KNOWN_DEVIATIONS.md).

## Asking for more

- [`docs/CODE_QUALITY_ROADMAP.md`](CODE_QUALITY_ROADMAP.md) -- what *not* to
  refactor (and why) plus current cleanup priorities.
- [`docs/TILING_KNOWN_DEVIATIONS.md`](TILING_KNOWN_DEVIATIONS.md) -- where the
  app intentionally falls short of the strongest literature target.
- [`TODO.md`](../TODO.md) -- active product / release follow-up.
