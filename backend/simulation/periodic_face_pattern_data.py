from __future__ import annotations

import json
from pathlib import Path

from backend.payload_types import RawJsonObject

PERIODIC_FACE_PATTERN_DIRECTORY = Path(__file__).with_name("data") / "periodic_face_patterns"


def load_periodic_face_pattern_payloads(
    directory: Path = PERIODIC_FACE_PATTERN_DIRECTORY,
) -> dict[str, RawJsonObject]:
    """Load independently versioned periodic-face descriptors by geometry key."""
    payloads: dict[str, RawJsonObject] = {}
    for path in sorted(directory.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Periodic face tiling descriptor '{path.name}' is invalid.")

        geometry = payload.get("geometry")
        if not isinstance(geometry, str) or not geometry:
            raise ValueError(f"Periodic face tiling descriptor '{path.name}'.geometry is invalid.")
        if path.stem != geometry:
            raise ValueError(
                f"Periodic face tiling descriptor '{path.name}' must use the geometry key "
                f"'{geometry}' as its filename."
            )
        if geometry in payloads:
            raise ValueError(f"Duplicate periodic face tiling geometry '{geometry}'.")
        payloads[geometry] = payload

    return payloads
