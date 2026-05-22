# Examples

Self-contained scripts demonstrating each major part of the codebase. Each
script is a runnable smoke test you can execute from the repo root with the
project venv activated:

```
.venv/Scripts/python.exe examples/build_aperiodic_patch.py     # Windows
python examples/build_aperiodic_patch.py                       # Unix
```

| Script | What it shows | Imports |
|---|---|---|
| `build_aperiodic_patch.py` | Build a depth-2 pinwheel patch and summarise its cells | `backend.simulation.topology` |
| `simulate_steps.py` | Run a Conway-Life blinker on a 5x5 square grid for a few steps | `backend.simulation.engine`, `backend.rules` |
| `inspect_topology.py` | Walk any topology's cells, kinds, and neighbour graph | `backend.simulation.topology` |
| `render_patch_svg.py` | Convert a topology patch to plain SVG on stdout | `backend.simulation.topology` |
| `verify_against_spec.py` | Run the literature verifier against one family | `backend.simulation.literature_reference_verification` |

These exist to:

- give you a working starting point you can copy-paste, edit, and iterate on
- exercise just the library surface (no Flask, no Vite, no browser)
- be small enough that a fresh-eyes reader can scan the whole thing in under a
  minute

If you're trying to do something a different way, see
[`docs/ONBOARDING.md`](../docs/ONBOARDING.md) for the full decision tree.
