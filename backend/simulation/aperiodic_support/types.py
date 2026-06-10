"""Type aliases and dataclasses shared across aperiodic-support submodules.

Pure declarations -- no imports from sibling modules of ``aperiodic_support``
so the dependency graph stays acyclic.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Literal, NotRequired, TypedDict

COORDINATE_PRECISION = 6

Affine = tuple[float, float, float, float, float, float]
AFFINE_IDENTITY: Affine = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0)
AFFINE_REFLECT_X: Affine = (-1.0, 0.0, 0.0, 0.0, 1.0, 0.0)


@dataclass(frozen=True)
class AperiodicPatchCell:
    id: str
    kind: str
    center: tuple[float, float]
    vertices: tuple[tuple[float, float], ...]
    neighbors: tuple[str, ...]
    tile_family: str | None = None
    orientation_token: str | None = None
    chirality_token: str | None = None
    decoration_tokens: tuple[str, ...] | None = None


@dataclass(frozen=True)
class AperiodicPatch:
    patch_depth: int
    width: int
    height: int
    cells: tuple[AperiodicPatchCell, ...]


@dataclass(frozen=True)
class Vec:
    x: float
    y: float

    def __add__(self, other: Vec) -> Vec:
        return Vec(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vec) -> Vec:
        return Vec(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vec:
        return Vec(self.x * scalar, self.y * scalar)


class PatchRecord(TypedDict):
    id: str
    kind: str
    center: tuple[float, float]
    vertices: tuple[tuple[float, float], ...]
    tile_family: NotRequired[str | None]
    orientation_token: NotRequired[str | None]
    chirality_token: NotRequired[str | None]
    decoration_tokens: NotRequired[tuple[str, ...] | None]


class ExactPatchRecord(TypedDict):
    id: str
    kind: str
    vertices: tuple[tuple[Fraction, Fraction], ...]
    tile_family: NotRequired[str | None]
    orientation_token: NotRequired[str | None]
    chirality_token: NotRequired[str | None]
    decoration_tokens: NotRequired[tuple[str, ...] | None]


ExactNeighborMode = Literal["full_edge", "segment_overlap"]
NeighborMode = Literal["full_edge", "segment_overlap"]
