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


def palette_manifest_path() -> Path:
    return Path(__file__).resolve().parents[3] / "frontend" / "canvas" / "family-dead-palette-manifest.json"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_palette_manifest() -> dict[str, Any]:
    return json.loads(palette_manifest_path().read_text(encoding="utf-8"))


def iter_palette_fixture_cases() -> list[PaletteFixtureCase]:
    manifest = load_palette_manifest()
    families = manifest.get("families")
    if not isinstance(families, list):
        raise AssertionError("Palette manifest was missing a 'families' array.")

    cases: list[PaletteFixtureCase] = []
    for family_entry in families:
        if not isinstance(family_entry, dict):
            continue
        browser_alias_coverage = family_entry.get("browserAliasCoverage")
        if not isinstance(browser_alias_coverage, dict):
            continue
        family = family_entry.get("geometry")
        fixture_path_value = browser_alias_coverage.get("fixturePath")
        selector_fields_value = browser_alias_coverage.get("selectorFields")
        if not isinstance(family, str) or not isinstance(fixture_path_value, str):
            continue
        selector_fields = tuple(
            field
            for field in selector_fields_value
            if isinstance(field, str)
        ) if isinstance(selector_fields_value, list) else ()
        fixture_path = (_repo_root() / fixture_path_value).resolve()
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        topology = payload.get("topology")
        if not isinstance(topology, dict):
            continue
        cases.append(
            {
                "family": family,
                "fixture_name": fixture_path.name,
                "fixture_path": str(fixture_path),
                "selector_fields": selector_fields,
                "topology": topology,
            },
        )
    return cases


def palette_fixture_test_suffix(case: PaletteFixtureCase) -> str:
    return re.sub(r"[^0-9a-z_]+", "_", case["family"].replace("-", "_"))
