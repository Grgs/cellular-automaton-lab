from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from backend.simulation.topology_catalog import resolve_geometry_key

DEFAULTS_PATH = Path(__file__).resolve().parents[1] / "config" / "defaults.json"


def _require(mapping: dict[str, Any], key: str) -> Any:
    if key not in mapping:
        raise KeyError(f"Missing required defaults key: {key}")
    return mapping[key]


@lru_cache(maxsize=1)
def load_defaults() -> dict[str, Any]:
    with DEFAULTS_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    simulation = _require(payload, "simulation")
    ui = _require(payload, "ui")
    theme = _require(payload, "theme")

    defaults: dict[str, Any] = {
        "simulation": {
            "topology_spec": {
                "tiling_family": str(_require(_require(simulation, "topology_spec"), "tiling_family")),
                "adjacency_mode": str(_require(_require(simulation, "topology_spec"), "adjacency_mode")),
                "sizing_mode": str(_require(_require(simulation, "topology_spec"), "sizing_mode")),
                "width": int(_require(_require(simulation, "topology_spec"), "width")),
                "height": int(_require(_require(simulation, "topology_spec"), "height")),
                "patch_depth": int(_require(_require(simulation, "topology_spec"), "patch_depth")),
            },
            "speed": float(_require(simulation, "speed")),
            "rule": str(_require(simulation, "rule")),
            "min_grid_size": int(_require(simulation, "min_grid_size")),
            "max_grid_size": int(_require(simulation, "max_grid_size")),
            "min_patch_depth": int(_require(simulation, "min_patch_depth")),
            "max_patch_depth": int(_require(simulation, "max_patch_depth")),
            "min_speed": float(_require(simulation, "min_speed")),
            "max_speed": float(_require(simulation, "max_speed")),
        },
        "ui": {
            "cell_size": int(_require(ui, "cell_size")),
            "min_cell_size": int(_require(ui, "min_cell_size")),
            "max_cell_size": int(_require(ui, "max_cell_size")),
            "storage_key": str(_require(ui, "storage_key")),
        },
        "theme": {
            "default": str(_require(theme, "default")),
            "storage_key": str(_require(theme, "storage_key")),
        },
    }
    return defaults


APP_DEFAULTS = load_defaults()

DEFAULT_WIDTH = APP_DEFAULTS["simulation"]["topology_spec"]["width"]
DEFAULT_HEIGHT = APP_DEFAULTS["simulation"]["topology_spec"]["height"]
DEFAULT_SPEED = APP_DEFAULTS["simulation"]["speed"]
DEFAULT_TILING_FAMILY = APP_DEFAULTS["simulation"]["topology_spec"]["tiling_family"]
DEFAULT_ADJACENCY_MODE = APP_DEFAULTS["simulation"]["topology_spec"]["adjacency_mode"]
DEFAULT_SIZING_MODE = APP_DEFAULTS["simulation"]["topology_spec"]["sizing_mode"]
DEFAULT_GEOMETRY = resolve_geometry_key(DEFAULT_TILING_FAMILY, DEFAULT_ADJACENCY_MODE)
DEFAULT_RULE_NAME = APP_DEFAULTS["simulation"]["rule"]
MIN_GRID_SIZE = APP_DEFAULTS["simulation"]["min_grid_size"]
MAX_GRID_SIZE = APP_DEFAULTS["simulation"]["max_grid_size"]
DEFAULT_PATCH_DEPTH = APP_DEFAULTS["simulation"]["topology_spec"]["patch_depth"]
MIN_PATCH_DEPTH = APP_DEFAULTS["simulation"]["min_patch_depth"]
MAX_PATCH_DEPTH = APP_DEFAULTS["simulation"]["max_patch_depth"]
MIN_SPEED = APP_DEFAULTS["simulation"]["min_speed"]
MAX_SPEED = APP_DEFAULTS["simulation"]["max_speed"]

DEFAULT_CELL_SIZE = APP_DEFAULTS["ui"]["cell_size"]
MIN_CELL_SIZE = APP_DEFAULTS["ui"]["min_cell_size"]
MAX_CELL_SIZE = APP_DEFAULTS["ui"]["max_cell_size"]
UI_STORAGE_KEY = APP_DEFAULTS["ui"]["storage_key"]

DEFAULT_THEME = APP_DEFAULTS["theme"]["default"]
THEME_STORAGE_KEY = APP_DEFAULTS["theme"]["storage_key"]
