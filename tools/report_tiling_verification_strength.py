from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.literature_reference_specs import REFERENCE_FAMILY_SPECS
from backend.simulation.topology_validation import recommended_validation_options


_LOCAL_REFERENCE_FIXTURE_PATH = (
    ROOT / "backend" / "simulation" / "data" / "reference_patch_local_fixtures.json"
)


@lru_cache(maxsize=1)
def _load_local_reference_geometries() -> set[str]:
    payload = json.loads(_LOCAL_REFERENCE_FIXTURE_PATH.read_text(encoding="utf-8"))
    return set(payload)


def _strength_tags(geometry: str) -> tuple[str, ...]:
    spec = REFERENCE_FAMILY_SPECS[geometry]
    tags: list[str] = []
    if any(
        expectation.exact_total_cells is not None or expectation.expected_signature is not None
        for expectation in spec.depth_expectations.values()
    ):
        tags.append("sample-exact")
    if spec.required_metadata:
        tags.append("metadata")
    if spec.periodic_descriptor is not None:
        tags.extend(("descriptor", "vertex-stars"))
        if spec.periodic_descriptor.expected_dual_geometry is not None:
            tags.append("dual-checks")
    if any(
        expectation.expected_polygon_area_frequencies_by_kind is not None
        for expectation in spec.depth_expectations.values()
    ):
        tags.append("area-hierarchy")
    if geometry in _load_local_reference_geometries():
        tags.append("local-reference")
    if spec.exact_reference_mode is not None:
        tags.append("exact-path")
    if all(recommended_validation_options(geometry).values()):
        tags.append("strict-validation")
    return tuple(tags)


def main() -> int:
    print("geometry\tsample_mode\tstrength_tags")
    for geometry in sorted(REFERENCE_FAMILY_SPECS):
        spec = REFERENCE_FAMILY_SPECS[geometry]
        print(
            f"{geometry}\t{spec.sample_mode}\t{','.join(_strength_tags(geometry))}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
