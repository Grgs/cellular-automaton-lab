from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import cast

from backend.simulation.reference_specs.types import ReferenceFamilySpec


def _discover_periodic_specs() -> dict[str, ReferenceFamilySpec]:
    discovered: dict[str, ReferenceFamilySpec] = {}
    package_dir = Path(__file__).parent
    for path in sorted(package_dir.glob("*.py")):
        if path.stem == "__init__":
            continue
        module = import_module(f"{__name__}.{path.stem}")
        specs = cast(dict[str, ReferenceFamilySpec] | None, getattr(module, "SPECS", None))
        if specs is None:
            continue
        duplicates = sorted(set(discovered).intersection(specs))
        if duplicates:
            raise ValueError(f"Duplicate periodic reference specs: {duplicates}")
        discovered.update(specs)
    return discovered


PERIODIC_REFERENCE_FAMILY_SPECS = _discover_periodic_specs()

__all__ = ["PERIODIC_REFERENCE_FAMILY_SPECS"]
