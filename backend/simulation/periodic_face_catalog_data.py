from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DEFAULT_SOURCE_DIR = Path(__file__).with_name("data") / "periodic_face_catalog"
_DEFAULT_AGGREGATE_PATH = Path(__file__).with_name("data") / "periodic_face_catalog.json"


def _load_metadata_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Periodic catalog metadata must be an object: {path}")
    geometry = payload.get("geometry")
    if not isinstance(geometry, str) or not geometry:
        raise ValueError(f"Periodic catalog metadata requires a geometry: {path}")
    if path.stem != geometry:
        raise ValueError(
            f"Periodic catalog metadata filename '{path.name}' must match geometry '{geometry}'."
        )
    required_strings = (
        "label",
        "picker_group",
        "family",
        "viewport_sync_mode",
        "default_rule",
    )
    for field in required_strings:
        if not isinstance(payload.get(field), str) or not payload[field]:
            raise ValueError(f"Periodic catalog metadata requires '{field}': {path}")
    if not isinstance(payload.get("preview_data"), str) or not payload["preview_data"]:
        raise ValueError(f"Periodic catalog metadata requires 'preview_data': {path}")
    for field in ("picker_order", "minimum_grid_dimension"):
        if not isinstance(payload.get(field), int):
            raise ValueError(f"Periodic catalog metadata requires integer '{field}': {path}")
    sizing = payload.get("sizing_policy")
    if not isinstance(sizing, dict) or not all(
        field in sizing for field in ("control", "default", "min", "max")
    ):
        raise ValueError(f"Periodic catalog metadata requires a sizing policy: {path}")
    source_urls = payload.get("source_urls")
    if not isinstance(source_urls, list) or not all(
        isinstance(url, str) and url for url in source_urls
    ):
        raise ValueError(f"Periodic catalog metadata source_urls must be strings: {path}")
    palette = payload.get("palette")
    if palette is not None and (
        not isinstance(palette, dict) or palette.get("geometry") != geometry
    ):
        raise ValueError(f"Periodic catalog palette must match geometry '{geometry}': {path}")
    return payload


def load_periodic_face_catalog_sources(
    directory: Path = _DEFAULT_SOURCE_DIR,
) -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {}
    for path in sorted(directory.glob("*.json")):
        payload = _load_metadata_file(path)
        geometry = str(payload["geometry"])
        if geometry in payloads:
            raise ValueError(f"Duplicate periodic catalog metadata for '{geometry}'.")
        payloads[geometry] = payload
    return payloads


def load_periodic_face_catalog(
    path: Path = _DEFAULT_AGGREGATE_PATH,
) -> tuple[dict[str, Any], ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        raise ValueError("Generated periodic face catalog must be a list of objects.")
    geometries = [item.get("geometry") for item in payload]
    if any(not isinstance(geometry, str) or not geometry for geometry in geometries):
        raise ValueError("Generated periodic face catalog entries require geometry keys.")
    if len(geometries) != len(set(geometries)):
        raise ValueError("Generated periodic face catalog contains duplicate geometries.")
    return tuple(payload)
