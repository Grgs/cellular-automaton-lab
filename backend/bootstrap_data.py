from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from backend.contract_validation import SNAPSHOT_VERSION
from backend.defaults import APP_DEFAULTS
from backend.payload_types import (
    AperiodicFamilyBootstrapPayload,
    AppBootstrapPayload,
    ServerMetaPayload,
)
from backend.simulation.aperiodic_family_manifest import (
    APERIODIC_FAMILY_IDS,
    APERIODIC_FAMILY_MANIFEST,
)
from backend.simulation.periodic_face_tilings import describe_periodic_face_tilings
from backend.simulation.topology_catalog import describe_topologies


class BootstrapDataProvider(Protocol):
    def get_payload(self) -> AppBootstrapPayload: ...


@dataclass(frozen=True)
class StaticBootstrapDataProvider:
    server_meta: ServerMetaPayload

    def get_payload(self) -> AppBootstrapPayload:
        return {
            "app_defaults": APP_DEFAULTS,
            "topology_catalog": describe_topologies(),
            "periodic_face_tilings": describe_periodic_face_tilings(),
            "aperiodic_families": describe_aperiodic_families(),
            "server_meta": self.server_meta,
            "snapshot_version": SNAPSHOT_VERSION,
        }


def describe_aperiodic_families() -> list[AperiodicFamilyBootstrapPayload]:
    return [
        {
            "tiling_family": geometry,
            "label": APERIODIC_FAMILY_MANIFEST[geometry].catalog_label,
            "experimental": APERIODIC_FAMILY_MANIFEST[geometry].experimental,
            "implementation_status": APERIODIC_FAMILY_MANIFEST[geometry].implementation_status,
            "promotion_blocker": APERIODIC_FAMILY_MANIFEST[geometry].promotion_blocker,
            "public_cell_kinds": list(APERIODIC_FAMILY_MANIFEST[geometry].public_cell_kinds),
        }
        for geometry in APERIODIC_FAMILY_IDS
    ]


def build_bootstrap_payload(server_meta: ServerMetaPayload) -> AppBootstrapPayload:
    return StaticBootstrapDataProvider(server_meta=server_meta).get_payload()
