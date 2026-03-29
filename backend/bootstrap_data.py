from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from backend.defaults import APP_DEFAULTS
from backend.payload_types import AppBootstrapPayload, ServerMetaPayload
from backend.simulation.periodic_face_tilings import describe_periodic_face_tilings
from backend.simulation.persistence import SNAPSHOT_VERSION
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
            "server_meta": self.server_meta,
            "snapshot_version": SNAPSHOT_VERSION,
        }


def build_bootstrap_payload(server_meta: ServerMetaPayload) -> AppBootstrapPayload:
    return StaticBootstrapDataProvider(server_meta=server_meta).get_payload()
