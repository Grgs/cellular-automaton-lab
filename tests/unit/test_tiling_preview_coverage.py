"""Verify that every non-regular tiling picker card has a polygon thumbnail entry.

The tiling picker renders preview thumbnails from pre-computed polygon data stored
in frontend/controls/tiling-preview-data.ts. If a topology is missing from that
file, the picker silently falls back to a generic square preview. This test catches
that regression by cross-checking the backend topology catalog against the frontend
data file.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from backend.simulation.topology_catalog import TOPOLOGY_CATALOG

_PREVIEW_DATA_PATH = (
    Path(__file__).resolve().parents[2] / "frontend" / "controls" / "tiling-preview-data.ts"
)

# The three regular tilings have hard-coded inline render logic in
# tiling-preview.ts and do not need a POLYGON_PREVIEW_DATA entry.
_INLINE_PREVIEW_KEYS = frozenset({"square", "hex", "triangle"})

# Keys are either "quoted-with-dashes" or unquoted (no dashes).
_KEY_PATTERN = re.compile(r'"([a-z][a-z0-9-]*)":|([a-z][a-z0-9]+):')


def _preview_data_keys() -> frozenset[str]:
    """Return the set of geometry keys defined in tiling-preview-data.ts."""
    content = _PREVIEW_DATA_PATH.read_text(encoding="utf-8")
    keys = {a or b for a, b in _KEY_PATTERN.findall(content)}
    return frozenset(keys)


def _required_preview_keys() -> frozenset[str]:
    """Return the picker preview key for every non-regular tiling family.

    Each topology family appears once in the picker. The preview key is the
    geometry key for the family's default adjacency mode.
    """
    return frozenset(
        d.geometry_keys[d.default_adjacency_mode]
        for d in TOPOLOGY_CATALOG
        if d.geometry_keys[d.default_adjacency_mode] not in _INLINE_PREVIEW_KEYS
    )


class TilingPreviewCoverageTests(unittest.TestCase):
    def test_all_picker_topologies_have_thumbnail_entries(self) -> None:
        """Every non-regular tiling family must have an entry in POLYGON_PREVIEW_DATA.

        Without an entry the picker silently displays a generic square preview
        instead of the actual tiling geometry.
        """
        required = _required_preview_keys()
        available = _preview_data_keys()
        missing = sorted(required - available)
        self.assertFalse(
            missing,
            f"Topologies registered in the catalog but missing from "
            f"frontend/controls/tiling-preview-data.ts: {missing}\n"
            f"Run `py -3 tools/generate_tiling_preview.py --geometry <key>` "
            f"to generate the polygon data.",
        )

    def test_preview_data_has_no_unregistered_entries(self) -> None:
        """Every entry in POLYGON_PREVIEW_DATA should correspond to a known
        topology. Orphaned entries accumulate bundle weight silently."""
        required = _required_preview_keys()
        inline = _INLINE_PREVIEW_KEYS
        available = _preview_data_keys()
        orphaned = sorted(available - required - inline)
        self.assertFalse(
            orphaned,
            f"Entries in tiling-preview-data.ts with no corresponding topology "
            f"in the catalog: {orphaned}",
        )


if __name__ == "__main__":
    unittest.main()
