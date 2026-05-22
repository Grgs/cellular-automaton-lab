"""Run the literature-reference verifier against one family.

The verifier compares a computed patch's cell counts, kind frequencies, and
adjacency invariants against a hand-curated ``ReferenceFamilySpec`` (sourced
from the literature). This is the same path ``tools/verify_reference_tilings.py``
uses for the whole catalog; here we drive it for a single family so you can
see the output shape.

Pass any catalog geometry key as the first argument; defaults to ``sphinx``.

Run from the repo root:

    python examples/verify_against_spec.py
    python examples/verify_against_spec.py pinwheel-2-1
    python examples/verify_against_spec.py shield
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.literature_reference_specs import REFERENCE_FAMILY_SPECS
from backend.simulation.literature_reference_verification import (
    verify_all_reference_families,
)


def main(argv: list[str]) -> int:
    geometry = argv[1] if len(argv) > 1 else "sphinx"
    if geometry not in REFERENCE_FAMILY_SPECS:
        print(f"Unknown geometry: {geometry!r}", file=sys.stderr)
        print(f"Available: {sorted(REFERENCE_FAMILY_SPECS)}", file=sys.stderr)
        return 1

    spec = REFERENCE_FAMILY_SPECS[geometry]
    print(f"Family:        {spec.geometry} ({spec.display_name})")
    print(f"Source URLs:   {spec.source_urls}")
    print(f"Seed policy:   {spec.canonical_root_seed_policy}")
    print(f"Public kinds:  {spec.allowed_public_cell_kinds}")
    print(f"Depths probed: {sorted(spec.depth_expectations)}")
    print()

    results = verify_all_reference_families()
    family_result = next((r for r in results if r.geometry == geometry), None)
    if family_result is None:
        print(f"No verifier result for {geometry!r}", file=sys.stderr)
        return 1

    if family_result.is_success:
        print(f"PASS {geometry}: all checks satisfied")
    else:
        print(f"FAIL {geometry}: {len(family_result.failures)} check(s) failed")
        for failure in family_result.failures[:10]:
            print(f"  - {failure.code}: {failure.message}")
    return 0 if family_result.is_success else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
