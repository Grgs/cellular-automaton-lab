from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.literature_reference_verification import (
    ReferenceVerificationResult,
    verify_all_reference_families,
)


def _print_result(result: ReferenceVerificationResult) -> None:
    waiver_suffix = " [waived]" if result.waived and result.status != "PASS" else ""
    print(f"{result.status} {result.geometry}{waiver_suffix}")
    for observation in result.observations:
        sample_label = (
            f"grid {observation.depth}x{observation.depth}"
            if observation.sample_mode == "grid"
            else f"depth {observation.depth}"
        )
        print(
            "  "
            + (
                f"{sample_label}: cells={observation.total_cells} "
                f"orientations={observation.unique_orientation_tokens} "
                f"chirality={observation.unique_chirality_tokens} "
                f"signature={observation.signature}"
            )
        )
    for failure in result.failures:
        prefix = f"  {failure.code}"
        if failure.depth is not None:
            prefix += f"[d{failure.depth}]"
        print(f"{prefix}: {failure.message}")


def main() -> int:
    results = verify_all_reference_families()
    blocking_failures = False
    for result in results:
        _print_result(result)
        if result.blocking:
            blocking_failures = True
    return 1 if blocking_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
