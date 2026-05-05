from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Literal

from backend.simulation.aperiodic_family_manifest import (
    APERIODIC_FAMILY_MANIFEST,
    PENROSE_GEOMETRY,
    PENROSE_VERTEX_GEOMETRY,
)
from backend.simulation.literature_reference_specs import REFERENCE_FAMILY_SPECS
from backend.simulation.topology_catalog import TOPOLOGY_VARIANTS


AperiodicImplementationStatus = Literal[
    "true_substitution",
    "exact_affine",
    "canonical_patch",
    "known_deviation",
]

_DATA_DIR = Path(__file__).with_name("data")
_LOCAL_REFERENCE_FIXTURE_PATH = _DATA_DIR / "reference_patch_local_fixtures.json"
_CANONICAL_REFERENCE_FIXTURE_PATH = _DATA_DIR / "reference_patch_canonical_fixtures.json"


@dataclass(frozen=True)
class AperiodicImplementationContract:
    geometry: str
    implementation_status: AperiodicImplementationStatus
    source_urls: tuple[str, ...]
    public_cell_kinds: tuple[str, ...]
    metadata_fields: tuple[tuple[str, tuple[str, ...]], ...]
    depth_semantics: str
    verification_modes: tuple[str, ...]
    promotion_blocker: str | None = None


def _load_fixture_geometries(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return set(json.loads(path.read_text(encoding="utf-8")))


def _verification_modes(geometry: str) -> tuple[str, ...]:
    spec = REFERENCE_FAMILY_SPECS[geometry]
    modes: list[str] = []
    if spec.depth_expectations:
        modes.append("depth-expectations")
    if spec.required_metadata:
        modes.append("metadata")
    if geometry in _load_fixture_geometries(_LOCAL_REFERENCE_FIXTURE_PATH):
        modes.append("local-reference")
    if geometry in _load_fixture_geometries(_CANONICAL_REFERENCE_FIXTURE_PATH):
        modes.append("canonical-patch")
    if spec.exact_reference_mode is not None:
        modes.append(spec.exact_reference_mode)
    if spec.builder_signals:
        modes.append("builder-signals")
    return tuple(modes)


def _depth_semantics(geometry: str) -> str:
    spec = REFERENCE_FAMILY_SPECS[geometry]
    if spec.sample_mode == "grid":
        return "grid sample"
    if geometry == "pinwheel":
        return "exact affine substitution depth"
    return "substitution patch depth"


def _contract_manifest_geometry(geometry: str) -> str:
    if geometry == PENROSE_VERTEX_GEOMETRY:
        return PENROSE_GEOMETRY
    return geometry


def build_aperiodic_contract(geometry: str) -> AperiodicImplementationContract:
    spec = REFERENCE_FAMILY_SPECS[geometry]
    try:
        manifest_entry = APERIODIC_FAMILY_MANIFEST[_contract_manifest_geometry(geometry)]
    except KeyError as error:
        raise ValueError(f"Missing aperiodic implementation contract for {geometry!r}.") from error
    return AperiodicImplementationContract(
        geometry=geometry,
        implementation_status=manifest_entry.implementation_status,
        source_urls=spec.source_urls,
        public_cell_kinds=manifest_entry.public_cell_kinds,
        metadata_fields=tuple(
            (requirement.kind, requirement.fields) for requirement in spec.required_metadata
        ),
        depth_semantics=_depth_semantics(geometry),
        verification_modes=_verification_modes(geometry),
        promotion_blocker=manifest_entry.promotion_blocker,
    )


APERIODIC_IMPLEMENTATION_CONTRACTS: dict[str, AperiodicImplementationContract] = {
    variant.geometry_key: build_aperiodic_contract(variant.geometry_key)
    for variant in TOPOLOGY_VARIANTS
    if variant.family == "aperiodic"
}


__all__ = [
    "APERIODIC_IMPLEMENTATION_CONTRACTS",
    "AperiodicImplementationContract",
    "AperiodicImplementationStatus",
    "build_aperiodic_contract",
]
