from __future__ import annotations

import re
from html import escape
from pathlib import Path
from typing import TypedDict

from backend.payload_types import AppDefaultsPayload, TopologyCatalogEntryPayload


ROOT_DIR = Path(__file__).resolve().parents[1]
SHARED_APP_SHELL_BODY_PATH = ROOT_DIR / "frontend" / "shell" / "app-shell-body.html"
PICKER_GROUP_ORDER = ("Classic", "Periodic Mixed", "Aperiodic")
UNRESOLVED_PLACEHOLDER_PATTERN = re.compile(r"__[A-Z0-9_]+__")


class AppShellRenderValues(TypedDict):
    tiling_family_options: str
    cell_size_min: str
    cell_size_max: str
    cell_size_value: str
    cell_size_label: str
    patch_depth_min: str
    patch_depth_max: str
    patch_depth_value: str
    patch_depth_label: str
    speed_min: str
    speed_max: str
    speed_value: str
    speed_label: str
    adjacency_field_hidden: str
    adjacency_mode_options: str


_STANDALONE_DOCUMENT_TEMPLATE = """<!DOCTYPE html>
<!-- Generated from frontend/shell/app-shell-body.html by tools/render_standalone_shell.py. -->
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cellular Automaton Lab</title>
    <link rel="icon" type="image/svg+xml" href="./favicon.svg">
    <script>
        (function () {
            try {
                var storedTheme = window.localStorage.getItem("cellular-automaton-theme");
                if (storedTheme === "light" || storedTheme === "dark") {
                    document.documentElement.dataset.theme = storedTheme;
                    return;
                }
                document.documentElement.dataset.theme = "light";
            } catch (error) {
                void error;
            }
        }());
    </script>
    <link rel="stylesheet" href="./styles.css">
</head>
<body>
__APP_SHELL__

    <script type="module" src="/frontend/standalone.ts"></script>
</body>
</html>
"""


def load_shared_app_shell_body() -> str:
    return SHARED_APP_SHELL_BODY_PATH.read_text(encoding="utf-8")


def _format_number(value: int | float) -> str:
    numeric_value = float(value)
    if numeric_value.is_integer():
        return str(int(numeric_value))
    return str(value)


def _build_option(value: str, label: str, *, selected: bool = False) -> str:
    selected_attribute = ' selected="selected"' if selected else ""
    return f'<option value="{escape(value, quote=True)}"{selected_attribute}>{escape(label)}</option>'


def _group_topologies(
    topology_catalog: list[TopologyCatalogEntryPayload],
) -> list[tuple[str, list[TopologyCatalogEntryPayload]]]:
    grouped: dict[str, list[TopologyCatalogEntryPayload]] = {
        group_name: []
        for group_name in PICKER_GROUP_ORDER
    }
    extra_group_order: list[str] = []

    for topology in topology_catalog:
        group_name = str(topology.get("picker_group") or "Other")
        if group_name not in grouped:
            grouped[group_name] = []
            extra_group_order.append(group_name)
        grouped[group_name].append(topology)

    ordered_groups = list(PICKER_GROUP_ORDER) + extra_group_order
    return [(group_name, grouped[group_name]) for group_name in ordered_groups]


def build_tiling_family_options_html(
    topology_catalog: list[TopologyCatalogEntryPayload],
    *,
    selected_tiling_family: str | None = None,
) -> str:
    rendered_groups: list[str] = []
    for group_name, topologies in _group_topologies(topology_catalog):
        rendered_options = "\n".join(
            _build_option(
                str(topology["tiling_family"]),
                str(topology["label"]),
                selected=str(topology["tiling_family"]) == str(selected_tiling_family),
            )
            for topology in topologies
        )
        rendered_groups.append(
            "\n".join(
                [
                    f'<optgroup label="{escape(group_name, quote=True)}">',
                    rendered_options,
                    "</optgroup>",
                ]
            ).rstrip()
        )
    return "\n".join(rendered_groups)


def build_adjacency_mode_options_html(
    topology_catalog: list[TopologyCatalogEntryPayload],
    *,
    tiling_family: str | None = None,
    selected_adjacency_mode: str | None = None,
) -> str:
    if not tiling_family:
        return ""

    for topology in topology_catalog:
        if str(topology["tiling_family"]) != str(tiling_family):
            continue
        supported_modes = topology.get("supported_adjacency_modes", [])
        return "\n".join(
            _build_option(
                str(adjacency_mode),
                str(adjacency_mode).capitalize(),
                selected=str(adjacency_mode) == str(selected_adjacency_mode),
            )
            for adjacency_mode in supported_modes
        )

    return ""


def _render_shared_app_shell(render_values: AppShellRenderValues) -> str:
    rendered = load_shared_app_shell_body()
    replacements = {
        "__TILING_FAMILY_OPTIONS__": render_values["tiling_family_options"],
        "__CELL_SIZE_MIN__": render_values["cell_size_min"],
        "__CELL_SIZE_MAX__": render_values["cell_size_max"],
        "__CELL_SIZE_VALUE__": render_values["cell_size_value"],
        "__CELL_SIZE_LABEL__": render_values["cell_size_label"],
        "__PATCH_DEPTH_MIN__": render_values["patch_depth_min"],
        "__PATCH_DEPTH_MAX__": render_values["patch_depth_max"],
        "__PATCH_DEPTH_VALUE__": render_values["patch_depth_value"],
        "__PATCH_DEPTH_LABEL__": render_values["patch_depth_label"],
        "__SPEED_MIN__": render_values["speed_min"],
        "__SPEED_MAX__": render_values["speed_max"],
        "__SPEED_VALUE__": render_values["speed_value"],
        "__SPEED_LABEL__": render_values["speed_label"],
        "__ADJACENCY_FIELD_HIDDEN__": render_values["adjacency_field_hidden"],
        "__ADJACENCY_MODE_OPTIONS__": render_values["adjacency_mode_options"],
    }
    for token, value in replacements.items():
        rendered = rendered.replace(token, value)

    unresolved_placeholders = sorted(set(UNRESOLVED_PLACEHOLDER_PATTERN.findall(rendered)))
    if unresolved_placeholders:
        unresolved = ", ".join(unresolved_placeholders)
        raise ValueError(f"App shell template contains unresolved placeholders: {unresolved}")
    return rendered


def _default_adjacency_hidden_attribute(
    *,
    tiling_family: str,
    adjacency_mode: str,
) -> str:
    if adjacency_mode == "edge" and tiling_family != "penrose-p3-rhombs":
        return "hidden"
    return ""


def render_server_app_shell(
    app_defaults: AppDefaultsPayload,
    topology_catalog: list[TopologyCatalogEntryPayload],
) -> str:
    simulation_defaults = app_defaults["simulation"]
    topology_spec = simulation_defaults["topology_spec"]
    selected_tiling_family = str(topology_spec["tiling_family"])
    selected_adjacency_mode = str(topology_spec["adjacency_mode"])
    cell_size_value = _format_number(app_defaults["ui"]["cell_size"])
    patch_depth_value = _format_number(topology_spec["patch_depth"])
    speed_value = _format_number(simulation_defaults["speed"])
    render_values: AppShellRenderValues = {
        "tiling_family_options": build_tiling_family_options_html(
            topology_catalog,
            selected_tiling_family=selected_tiling_family,
        ),
        "cell_size_min": _format_number(app_defaults["ui"]["min_cell_size"]),
        "cell_size_max": _format_number(app_defaults["ui"]["max_cell_size"]),
        "cell_size_value": cell_size_value,
        "cell_size_label": f"{cell_size_value}px",
        "patch_depth_min": _format_number(simulation_defaults["min_patch_depth"]),
        "patch_depth_max": _format_number(simulation_defaults["max_patch_depth"]),
        "patch_depth_value": patch_depth_value,
        "patch_depth_label": f"Depth {patch_depth_value}",
        "speed_min": _format_number(simulation_defaults["min_speed"]),
        "speed_max": _format_number(simulation_defaults["max_speed"]),
        "speed_value": speed_value,
        "speed_label": f"{speed_value} gen/s",
        "adjacency_field_hidden": _default_adjacency_hidden_attribute(
            tiling_family=selected_tiling_family,
            adjacency_mode=selected_adjacency_mode,
        ),
        "adjacency_mode_options": build_adjacency_mode_options_html(
            topology_catalog,
            tiling_family=selected_tiling_family,
            selected_adjacency_mode=selected_adjacency_mode,
        ),
    }

    return _render_shared_app_shell(render_values)


def render_standalone_app_shell() -> str:
    render_values: AppShellRenderValues = {
        "tiling_family_options": "",
        "cell_size_min": "4",
        "cell_size_max": "24",
        "cell_size_value": "12",
        "cell_size_label": "12px",
        "patch_depth_min": "0",
        "patch_depth_max": "6",
        "patch_depth_value": "0",
        "patch_depth_label": "Depth 0",
        "speed_min": "1",
        "speed_max": "30",
        "speed_value": "5",
        "speed_label": "5 gen/s",
        "adjacency_field_hidden": "hidden",
        "adjacency_mode_options": "",
    }
    return _render_shared_app_shell(render_values)


def render_standalone_document() -> str:
    return _STANDALONE_DOCUMENT_TEMPLATE.replace("__APP_SHELL__", render_standalone_app_shell())
