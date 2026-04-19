from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, TypedDict


class PaletteFixtureCase(TypedDict):
    family: str
    fixture_name: str
    fixture_path: str
    selector_fields: tuple[str, ...]
    topology: dict[str, Any]


PALETTE_ALIAS_BROWSER_FAMILIES = frozenset({
    "chair",
    "dodecagonal-square-triangle",
    "hat-monotile",
    "pinwheel",
    "robinson-triangles",
    "shield",
    "tuebingen-triangle",
})


def _fixture_root() -> Path:
    return Path(__file__).resolve().parents[3] / "frontend" / "test-fixtures" / "topologies"


def _unique_non_empty_values(cells: list[dict[str, Any]], field: str) -> set[str]:
    values: set[str] = set()
    for cell in cells:
        value = cell.get(field)
        if isinstance(value, str) and value:
            values.add(value)
    return values


def infer_palette_selector_fields(cells: list[dict[str, Any]]) -> tuple[str, ...]:
    selector_fields: list[str] = []
    if len(_unique_non_empty_values(cells, "kind")) > 1:
        selector_fields.append("kind")
    if len(_unique_non_empty_values(cells, "chirality_token")) > 1:
        selector_fields.append("chirality_token")
    if not selector_fields and len(_unique_non_empty_values(cells, "orientation_token")) > 1:
        selector_fields.append("orientation_token")
    return tuple(selector_fields)


def iter_palette_fixture_cases() -> list[PaletteFixtureCase]:
    cases: list[PaletteFixtureCase] = []
    for fixture_path in sorted(_fixture_root().glob("*.json")):
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        topology = payload.get("topology")
        if not isinstance(topology, dict):
            continue
        topology_spec = topology.get("topology_spec")
        cells = topology.get("cells")
        if not isinstance(topology_spec, dict) or not isinstance(cells, list):
            continue
        family = topology_spec.get("tiling_family")
        if not isinstance(family, str) or not family:
            continue
        if family not in PALETTE_ALIAS_BROWSER_FAMILIES:
            continue
        typed_cells = [cell for cell in cells if isinstance(cell, dict)]
        if not typed_cells:
            continue
        cases.append(
            {
                "family": family,
                "fixture_name": fixture_path.name,
                "fixture_path": str(fixture_path),
                "selector_fields": infer_palette_selector_fields(typed_cells),
                "topology": topology,
            },
        )
    return cases


def palette_fixture_test_suffix(case: PaletteFixtureCase) -> str:
    return re.sub(r"[^0-9a-z_]+", "_", case["family"].replace("-", "_"))
