from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import TypedDict

from backend.payload_types import JsonObject, TopologySpecPayload
from backend.simulation.topology_catalog import resolve_geometry_key

DEFAULTS_PATH = Path(__file__).resolve().parents[1] / "config" / "defaults.json"


class SimulationDefaultsPayload(TypedDict):
    topology_spec: TopologySpecPayload
    speed: float
    rule: str
    min_grid_size: int
    max_grid_size: int
    min_patch_depth: int
    max_patch_depth: int
    min_speed: float
    max_speed: float


class UiDefaultsPayload(TypedDict):
    cell_size: int
    min_cell_size: int
    max_cell_size: int
    storage_key: str


class ThemeDefaultsPayload(TypedDict):
    default: str
    storage_key: str


class AppDefaultsPayload(TypedDict):
    simulation: SimulationDefaultsPayload
    ui: UiDefaultsPayload
    theme: ThemeDefaultsPayload


def _require(mapping: JsonObject, key: str) -> object:
    if key not in mapping:
        raise KeyError(f"Missing required defaults key: {key}")
    return mapping[key]


def _require_str(mapping: JsonObject, key: str) -> str:
    return str(_require(mapping, key))


def _require_int(mapping: JsonObject, key: str) -> int:
    value = _require(mapping, key)
    if isinstance(value, (str, bytes, bytearray, int, float)):
        return int(value)
    raise ValueError(f"Defaults key '{key}' must be numeric.")


def _require_float(mapping: JsonObject, key: str) -> float:
    value = _require(mapping, key)
    if isinstance(value, (str, bytes, bytearray, int, float)):
        return float(value)
    raise ValueError(f"Defaults key '{key}' must be numeric.")


@lru_cache(maxsize=1)
def load_defaults() -> AppDefaultsPayload:
    with DEFAULTS_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Defaults payload at {DEFAULTS_PATH} must be a JSON object.")

    simulation = _require(payload, "simulation")
    ui = _require(payload, "ui")
    theme = _require(payload, "theme")
    if not isinstance(simulation, dict) or not isinstance(ui, dict) or not isinstance(theme, dict):
        raise ValueError(f"Defaults payload at {DEFAULTS_PATH} is invalid.")

    topology_spec = _require(simulation, "topology_spec")
    if not isinstance(topology_spec, dict):
        raise ValueError(f"Defaults payload at {DEFAULTS_PATH} is invalid.")

    defaults: AppDefaultsPayload = {
        "simulation": {
            "topology_spec": {
                "tiling_family": _require_str(topology_spec, "tiling_family"),
                "adjacency_mode": _require_str(topology_spec, "adjacency_mode"),
                "sizing_mode": _require_str(topology_spec, "sizing_mode"),
                "width": _require_int(topology_spec, "width"),
                "height": _require_int(topology_spec, "height"),
                "patch_depth": _require_int(topology_spec, "patch_depth"),
            },
            "speed": _require_float(simulation, "speed"),
            "rule": _require_str(simulation, "rule"),
            "min_grid_size": _require_int(simulation, "min_grid_size"),
            "max_grid_size": _require_int(simulation, "max_grid_size"),
            "min_patch_depth": _require_int(simulation, "min_patch_depth"),
            "max_patch_depth": _require_int(simulation, "max_patch_depth"),
            "min_speed": _require_float(simulation, "min_speed"),
            "max_speed": _require_float(simulation, "max_speed"),
        },
        "ui": {
            "cell_size": _require_int(ui, "cell_size"),
            "min_cell_size": _require_int(ui, "min_cell_size"),
            "max_cell_size": _require_int(ui, "max_cell_size"),
            "storage_key": _require_str(ui, "storage_key"),
        },
        "theme": {
            "default": _require_str(theme, "default"),
            "storage_key": _require_str(theme, "storage_key"),
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
