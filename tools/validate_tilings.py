from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path
from typing import TypedDict


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.topology_catalog import (
    TOPOLOGY_VARIANTS,
    is_aperiodic_geometry,
)
from backend.simulation.topology import build_topology
from backend.simulation.topology_validation import (
    TopologyValidationResult,
    recommended_validation_options,
    validate_topology,
)


class ValidationParameters(TypedDict):
    width: int
    height: int
    patch_depth: int | None


def iter_validation_targets() -> Iterator[tuple[str, ValidationParameters]]:
    for definition in TOPOLOGY_VARIANTS:
        if definition.family == "mixed":
            yield definition.geometry_key, {"width": 3, "height": 3, "patch_depth": None}
        elif is_aperiodic_geometry(definition.geometry_key):
            yield definition.geometry_key, {"width": 0, "height": 0, "patch_depth": 3}


def validate_manifest_tilings() -> tuple[tuple[str, TopologyValidationResult], ...]:
    results = []
    for geometry, parameters in iter_validation_targets():
        topology = build_topology(
            geometry,
            parameters["width"],
            parameters["height"],
            parameters["patch_depth"],
        )
        results.append(
            (
                geometry,
                validate_topology(topology, **recommended_validation_options(geometry)),
            )
        )
    return tuple(results)


def main() -> int:
    results = validate_manifest_tilings()
    all_valid = True
    for geometry, result in results:
        if result.is_valid:
            print(f"PASS {geometry} ({result.checked_cell_count} cells)")
            continue
        all_valid = False
        for line in result.summary_lines():
            print(line)
    print("INFO full-catalog literature verification: py -3 tools/verify_reference_tilings.py")
    return 0 if all_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
