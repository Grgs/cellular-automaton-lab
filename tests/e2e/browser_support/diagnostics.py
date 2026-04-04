from __future__ import annotations

import re
from dataclasses import dataclass


REGULAR_GRID_SUMMARY_RE = re.compile(r"^\s*(?P<width>\d+)\s*x\s*(?P<height>\d+)\s*$")
APERIODIC_PATCH_DEPTH_SUMMARY_RE = re.compile(r"^\s*Depth\s+(?P<depth>\d+)\b")


@dataclass(frozen=True)
class GridSummary:
    raw: str
    kind: str
    width: int | None = None
    height: int | None = None
    patch_depth: int | None = None


def parse_grid_summary_text(text: str | None) -> GridSummary:
    raw = (text or "").strip()
    regular_match = REGULAR_GRID_SUMMARY_RE.match(raw)
    if regular_match:
        return GridSummary(
            raw=raw,
            kind="regular",
            width=int(regular_match.group("width")),
            height=int(regular_match.group("height")),
        )

    aperiodic_match = APERIODIC_PATCH_DEPTH_SUMMARY_RE.match(raw)
    if aperiodic_match:
        return GridSummary(
            raw=raw,
            kind="aperiodic",
            patch_depth=int(aperiodic_match.group("depth")),
        )

    return GridSummary(raw=raw, kind="unknown")
