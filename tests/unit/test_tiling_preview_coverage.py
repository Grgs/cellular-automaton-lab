"""Verify that every non-regular tiling picker card has a polygon thumbnail entry.

The tiling picker renders preview thumbnails from pre-computed polygon data stored
in frontend/controls/tiling-preview-data.ts. If a topology is missing from that
file, the picker silently falls back to a generic square preview. This test catches
that regression by cross-checking the backend topology catalog against the frontend
data file.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from backend.simulation.topology_catalog import TOPOLOGY_CATALOG

_PREVIEW_DATA_PATH = (
    Path(__file__).resolve().parents[2] / "frontend" / "controls" / "tiling-preview-data.ts"
)
_PALETTE_MANIFEST_PATH = (
    Path(__file__).resolve().parents[2]
    / "frontend"
    / "canvas"
    / "family-dead-palette-manifest.json"
)

# The three regular tilings have hard-coded inline render logic in
# tiling-preview.ts and do not need a POLYGON_PREVIEW_DATA entry.
_INLINE_PREVIEW_KEYS = frozenset({"square", "hex", "triangle"})

_ENTRY_PATTERN = re.compile(
    r'^\s{4}(?:"([a-z][a-z0-9-]*)"|([a-z][a-z0-9]+)):\s*(?:\n\s*)?"([^"]*)",',
    re.MULTILINE,
)


def _preview_data_entries() -> dict[str, str]:
    """Return geometry key -> polygon data entries from tiling-preview-data.ts."""
    content = _PREVIEW_DATA_PATH.read_text(encoding="utf-8")
    return {a or b: payload for a, b, payload in _ENTRY_PATTERN.findall(content)}


def _preview_data_keys() -> frozenset[str]:
    """Return the set of geometry keys defined in tiling-preview-data.ts."""
    return frozenset(_preview_data_entries())


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


def _polygon_fills(polygon_data: str) -> list[str]:
    return [
        polygon_payload.split(":", 1)[0]
        for polygon_payload in polygon_data.split(";")
        if ":" in polygon_payload
    ]


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
            f"Run `python -m tools tilings preview --geometry <key>` "
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

    def test_palette_backed_previews_use_named_fill_tokens(self) -> None:
        """Canvas palette-backed thumbnail data should not use generic numeric fills."""
        entries = _preview_data_entries()
        manifest = json.loads(_PALETTE_MANIFEST_PATH.read_text(encoding="utf-8"))
        palette_backed_keys = [
            family["geometry"] for family in manifest["families"] if family["geometry"] in entries
        ]

        self.assertGreater(len(palette_backed_keys), 20)
        offenders = {
            key: sorted({fill for fill in _polygon_fills(entries[key]) if fill.isdigit()})
            for key in palette_backed_keys
        }
        offenders = {key: fills for key, fills in offenders.items() if fills}
        self.assertFalse(
            offenders,
            f"Palette-backed tiling thumbnails must use named fill tokens: {offenders}",
        )

    def test_kagome_preview_uses_per_kind_palette_tones(self) -> None:
        """Kagome registers its hexagon and two triangle orientations in the
        catalog palette, so its preview uses those tones, not legacy dead/deadAlt."""
        fills = set(_polygon_fills(_preview_data_entries()["trihexagonal-3-6-3-6"]))

        self.assertEqual(fills, {"toneCream", "toneTan", "toneStone"})


if __name__ == "__main__":
    unittest.main()
