"""Convert a topology patch to plain SVG on stdout.

No canvas, no browser, no Vite -- just walk the cells, emit ``<polygon>``
elements, and print. Pipe the output to a file to view in a browser:

    python examples/render_patch_svg.py pinwheel 2 > pinwheel.svg

Defaults: ``shield`` family at the default patch depth.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.topology import build_topology
from backend.simulation.topology_catalog import (
    default_patch_depth_for_tiling_family,
    get_topology_variant_for_geometry,
)

# A small fixed palette keyed by cell kind -> fill colour.
_PALETTE = (
    "#f4c2c2",
    "#c2d4f4",
    "#d4f4c2",
    "#f4ecc2",
    "#e2c2f4",
    "#c2f4f0",
    "#f4d0a8",
    "#a8d8f4",
    "#f4a8c8",
    "#b8c8a8",
)


def _kind_colour_map(cells: tuple) -> dict[str, str]:
    return {
        kind: _PALETTE[index % len(_PALETTE)]
        for index, kind in enumerate(sorted({cell.kind for cell in cells}))
    }


def main(argv: list[str]) -> int:
    geometry = argv[1] if len(argv) > 1 else "shield"
    depth = int(argv[2]) if len(argv) > 2 else None

    variant = get_topology_variant_for_geometry(geometry)
    if variant.sizing_mode == "patch_depth":
        resolved_depth = (
            depth
            if depth is not None
            else default_patch_depth_for_tiling_family(variant.tiling_family)
        )
        topology = build_topology(geometry, width=0, height=0, patch_depth=resolved_depth)
    else:
        topology = build_topology(geometry, width=4, height=4, patch_depth=None)

    colours = _kind_colour_map(topology.cells)
    xs = [v[0] for cell in topology.cells for v in (cell.vertices or ())]
    ys = [v[1] for cell in topology.cells for v in (cell.vertices or ())]
    if not xs:
        print(f"<!-- {geometry} has no polygon cells; nothing to render -->", file=sys.stderr)
        return 1
    min_x, min_y = min(xs), min(ys)
    width = max(xs) - min_x + 2
    height = max(ys) - min_y + 2

    print(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{min_x - 1} {min_y - 1} {width} {height}">'
    )
    print(f"  <!-- {geometry}: {topology.cell_count} cells -->")
    for cell in topology.cells:
        if not cell.vertices:
            continue
        points = " ".join(f"{x:.4f},{y:.4f}" for x, y in cell.vertices)
        fill = colours.get(cell.kind, "#ccc")
        print(f'  <polygon points="{points}" fill="{fill}" stroke="#333" stroke-width="0.05" />')
    print("</svg>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
