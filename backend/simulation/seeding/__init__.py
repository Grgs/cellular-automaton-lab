"""Cross-topology seed mapping and comparison.

Maps a single seed onto many topologies through a canonical traversal so the
same rule can be compared fairly across radically different tilings. See
:mod:`backend.simulation.seeding.traversal` for the orderings,
:mod:`backend.simulation.seeding.metrics` for the measurement helpers, and
:mod:`backend.simulation.seeding.comparison` for the sweep orchestration.
"""

from __future__ import annotations

from backend.simulation.seeding.comparison import (
    SeedComparison,
    TopologyComparisonResult,
    compare_seed,
)
from backend.simulation.seeding.metrics import (
    classify,
    first_extinction_step,
    hamming,
    population,
)
from backend.simulation.seeding.traversal import (
    DEFAULT_TRAVERSAL,
    TRAVERSALS,
    Traversal,
    bfs_ring_order,
    normalize_bits,
    paint_bits,
    row_major_order,
)

__all__ = [
    "DEFAULT_TRAVERSAL",
    "SeedComparison",
    "TRAVERSALS",
    "TopologyComparisonResult",
    "Traversal",
    "bfs_ring_order",
    "classify",
    "compare_seed",
    "first_extinction_step",
    "hamming",
    "normalize_bits",
    "paint_bits",
    "population",
    "row_major_order",
]
