from __future__ import annotations

from dataclasses import dataclass

from backend.simulation.topology_family_manifest import TOPOLOGY_FAMILY_MANIFEST


FRONTEND_TOPOLOGY_FAMILY_METADATA_PATH = "frontend/topology-family-metadata.ts"


@dataclass(frozen=True)
class TopologyFrontendFamilyContract:
    tiling_family: str
    label: str
    picker_group: str
    picker_order: int
    family: str
    sizing_mode: str
    viewport_sync_mode: str


FRONTEND_TOPOLOGY_FAMILY_CONTRACTS: tuple[TopologyFrontendFamilyContract, ...] = tuple(
    TopologyFrontendFamilyContract(
        tiling_family=tiling_family,
        label=entry.label,
        picker_group=entry.picker_group,
        picker_order=entry.picker_order,
        family=entry.family,
        sizing_mode=entry.sizing_mode,
        viewport_sync_mode=entry.viewport_sync_mode,
    )
    for tiling_family, entry in TOPOLOGY_FAMILY_MANIFEST.items()
)


def topology_frontend_family_contracts() -> tuple[TopologyFrontendFamilyContract, ...]:
    return FRONTEND_TOPOLOGY_FAMILY_CONTRACTS

