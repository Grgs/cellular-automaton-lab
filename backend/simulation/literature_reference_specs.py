from __future__ import annotations

from backend.simulation.reference_specs.aperiodic import APERIODIC_REFERENCE_FAMILY_SPECS
from backend.simulation.reference_specs.periodic import PERIODIC_REFERENCE_FAMILY_SPECS
from backend.simulation.reference_specs.regular import REGULAR_REFERENCE_FAMILY_SPECS
from backend.simulation.reference_specs.types import (
    BuilderSignalExpectation,
    MetadataRequirement,
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

REFERENCE_FAMILY_SPECS: dict[str, ReferenceFamilySpec] = {
    **REGULAR_REFERENCE_FAMILY_SPECS,
    **PERIODIC_REFERENCE_FAMILY_SPECS,
    **APERIODIC_REFERENCE_FAMILY_SPECS,
}

STAGED_REFERENCE_WAIVERS: frozenset[str] = frozenset()

__all__ = [
    "BuilderSignalExpectation",
    "MetadataRequirement",
    "PeriodicDescriptorExpectation",
    "REFERENCE_FAMILY_SPECS",
    "ReferenceDepthExpectation",
    "ReferenceFamilySpec",
    "STAGED_REFERENCE_WAIVERS",
]
