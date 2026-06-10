"""Run Conway's Game of Life on a small square grid and print live counts.

This is the minimum "use the simulation engine as a library" example. It
constructs a 5x5 square topology, seeds a horizontal blinker, and steps the
board through one full oscillation period.

The same loop works for any geometry; swap ``"square"`` for ``"hex"``,
``"pinwheel"``, etc., and pair it with a compatible rule
(``HexLifeRule``, ``LifeB2S23Rule``, ...).

Run from the repo root:

    python examples/simulate_steps.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.rules.conway import ConwayLifeRule
from backend.simulation.engine import SimulationEngine
from backend.simulation.topology import board_from_cells_by_id


def main() -> int:
    # Horizontal 3-cell blinker centered in a 5x5 square grid.
    initial_live_cells = {"c:1:2": 1, "c:2:2": 1, "c:3:2": 1}
    board = board_from_cells_by_id(
        geometry="square",
        width=5,
        height=5,
        cells_by_id=initial_live_cells,
    )

    engine = SimulationEngine()
    rule = ConwayLifeRule()

    print(f"step 0: {sum(board.cell_states)} live cells")
    for step in range(1, 5):
        board = engine.step_board(board, rule)
        live_ids = sorted(
            cell.id
            for cell, state in zip(board.topology.cells, board.cell_states, strict=True)
            if state
        )
        print(f"step {step}: {len(live_ids)} live cells -> {live_ids}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
