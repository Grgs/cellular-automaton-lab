"""Build a depth-2 pinwheel patch and summarise its cells.

Demonstrates the simplest path to a working aperiodic topology: pass a
geometry key + patch depth to ``build_topology``. The same call shape works
for every aperiodic family in the catalog (try ``shield``, ``hat-monotile``,
``ammann-beenker``, ``robinson-triangles``, ...).

Run from the repo root:

    python examples/build_aperiodic_patch.py
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.topology import build_topology


def main() -> int:
    topology = build_topology("pinwheel", width=0, height=0, patch_depth=2)

    print(f"Geometry:       {topology.geometry}")
    print(f"Cell count:     {topology.cell_count}")
    print(f"Patch bbox:     width={topology.width}, height={topology.height}")

    kind_counts = Counter(cell.kind for cell in topology.cells)
    print(f"Cell kinds:     {dict(kind_counts)}")

    chirality_counts = Counter(
        cell.chirality_token for cell in topology.cells if cell.chirality_token
    )
    print(f"Chiralities:    {dict(chirality_counts)}")

    sample = topology.cells[0]
    print()
    print("First cell:")
    print(f"  id:           {sample.id}")
    print(f"  kind:         {sample.kind}")
    print(f"  vertices:     {len(sample.vertices) if sample.vertices else 0}")
    print(f"  neighbours:   {len(sample.neighbors)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
