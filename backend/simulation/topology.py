from __future__ import annotations

from backend.simulation.topology_catalog import (
    ARCHIMEDEAN_488_GEOMETRY,
    DELTOIDAL_TRIHEXAGONAL_GEOMETRY,
    FLORET_PENTAGONAL_GEOMETRY,
    KAGOME_GEOMETRY,
    PENROSE_GEOMETRY,
    PENROSE_VERTEX_GEOMETRY,
    PRISMATIC_PENTAGONAL_GEOMETRY,
    RHOMBILLE_GEOMETRY,
    SNUB_SQUARE_DUAL_GEOMETRY,
    SPECTRE_GEOMETRY,
    TAYLOR_SOCOLAR_GEOMETRY,
    TETRAKIS_SQUARE_GEOMETRY,
    TRIAKIS_TRIANGULAR_GEOMETRY,
)
from backend.simulation.topology_boards import (
    board_from_cells_by_id,
    board_from_states,
    empty_board,
)
from backend.simulation.topology_builders import build_topology
from backend.simulation.topology_builders import _build_topology_cached, _build_topology_uncached
from backend.simulation.topology_types import (
    REGULAR_CELL_KIND,
    LatticeCell,
    LatticeTopology,
    SimulationBoard,
    parse_regular_cell_id,
    regular_cell_id,
    topology_revision,
)

__all__ = [
    "ARCHIMEDEAN_488_GEOMETRY",
    "DELTOIDAL_TRIHEXAGONAL_GEOMETRY",
    "FLORET_PENTAGONAL_GEOMETRY",
    "KAGOME_GEOMETRY",
    "PENROSE_GEOMETRY",
    "PENROSE_VERTEX_GEOMETRY",
    "PRISMATIC_PENTAGONAL_GEOMETRY",
    "REGULAR_CELL_KIND",
    "RHOMBILLE_GEOMETRY",
    "SPECTRE_GEOMETRY",
    "TAYLOR_SOCOLAR_GEOMETRY",
    "LatticeCell",
    "LatticeTopology",
    "SimulationBoard",
    "SNUB_SQUARE_DUAL_GEOMETRY",
    "TETRAKIS_SQUARE_GEOMETRY",
    "TRIAKIS_TRIANGULAR_GEOMETRY",
    "board_from_cells_by_id",
    "board_from_states",
    "build_topology",
    "empty_board",
    "parse_regular_cell_id",
    "regular_cell_id",
    "topology_revision",
    "_build_topology_cached",
    "_build_topology_uncached",
]
