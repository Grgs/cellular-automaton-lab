from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    get_aperiodic_family_manifest_entry,
)


def _reference_label(geometry: str) -> str:
    return get_aperiodic_family_manifest_entry(geometry).reference_label


def _public_cell_kinds(geometry: str) -> tuple[str, ...]:
    return get_aperiodic_family_manifest_entry(geometry).public_cell_kinds
