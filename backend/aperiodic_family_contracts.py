from __future__ import annotations

from dataclasses import dataclass

from backend.simulation.aperiodic_family_manifest import APERIODIC_FAMILY_IDS, APERIODIC_FAMILY_MANIFEST


FRONTEND_APERIODIC_METADATA_PATH = "frontend/aperiodic-family-metadata.ts"


@dataclass(frozen=True)
class AperiodicFrontendFamilyContract:
    geometry: str
    label: str
    public_cell_kinds: tuple[str, ...]
    experimental: bool


FRONTEND_APERIODIC_FAMILY_CONTRACTS: tuple[AperiodicFrontendFamilyContract, ...] = tuple(
    AperiodicFrontendFamilyContract(
        geometry=geometry,
        label=APERIODIC_FAMILY_MANIFEST[geometry].catalog_label,
        public_cell_kinds=APERIODIC_FAMILY_MANIFEST[geometry].public_cell_kinds,
        experimental=APERIODIC_FAMILY_MANIFEST[geometry].experimental,
    )
    for geometry in APERIODIC_FAMILY_IDS
)


def aperiodic_frontend_family_contracts() -> tuple[AperiodicFrontendFamilyContract, ...]:
    return FRONTEND_APERIODIC_FAMILY_CONTRACTS


__all__ = [
    "AperiodicFrontendFamilyContract",
    "FRONTEND_APERIODIC_FAMILY_CONTRACTS",
    "FRONTEND_APERIODIC_METADATA_PATH",
    "aperiodic_frontend_family_contracts",
]
