"""Walk any topology's cells, kinds, and neighbour graph.

Useful as a "what does this geometry actually look like in memory?" probe.
Pass any geometry key from the catalog as the first argument; defaults to
``shield`` if none given.

Run from the repo root:

    python examples/inspect_topology.py
    python examples/inspect_topology.py hat-monotile
    python examples/inspect_topology.py archimedean-4-8-8
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.topology import build_topology
from backend.simulation.topology_catalog import (
    default_patch_depth_for_tiling_family,
    get_topology_variant_for_geometry,
)


def main(argv: list[str]) -> int:
    geometry = argv[1] if len(argv) > 1 else "shield"
    variant = get_topology_variant_for_geometry(geometry)
    if variant.sizing_mode == "patch_depth":
        topology = build_topology(
            geometry,
            width=0,
            height=0,
            patch_depth=default_patch_depth_for_tiling_family(variant.tiling_family),
        )
    else:
        topology = build_topology(geometry, width=4, height=4, patch_depth=None)

    print(f"Geometry:        {topology.geometry}")
    print(f"Cell count:      {topology.cell_count}")
    print(f"Bounding box:    {topology.width} x {topology.height}")
    print()

    kind_counts = Counter(cell.kind for cell in topology.cells)
    print(f"Cell kinds:      {dict(kind_counts)}")

    neighbor_counts = Counter(len(cell.neighbors) for cell in topology.cells)
    print(f"Neighbour degree histogram: {dict(sorted(neighbor_counts.items()))}")

    isolated = [cell.id for cell in topology.cells if not cell.neighbors]
    print(f"Isolated cells:  {len(isolated)}")

    print()
    print("First 3 cells:")
    for cell in topology.cells[:3]:
        print(
            f"  {cell.id:30s} kind={cell.kind:20s}"
            f" neighbours={len(cell.neighbors):2d}"
            f" vertices={len(cell.vertices) if cell.vertices else 0}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
