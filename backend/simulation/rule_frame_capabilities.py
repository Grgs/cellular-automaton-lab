from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleFrameCapabilities:
    spatial: bool = False
    directional: bool = False


ADJACENCY_FRAME_CAPABILITIES = RuleFrameCapabilities()
DIRECTIONAL_FRAME_CAPABILITIES = RuleFrameCapabilities(spatial=True, directional=True)
