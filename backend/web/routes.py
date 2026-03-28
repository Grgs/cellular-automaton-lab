from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from flask import Blueprint, Response, current_app, jsonify, render_template, request

from backend.payload_types import (
    ApiErrorPayload,
    CellTargetPayload,
    CellUpdatePayload,
    JsonObject,
    RulesResponsePayload,
    TopologySpecPatch,
)
from backend.rules import RuleRegistry
from backend.frontend_assets import FrontendAssetManifest
from backend.simulation.coordinator import SimulationCoordinator
from backend.simulation.service import SimulationOperationError
from backend.web.requests import (
    RequestValidationError,
    parse_cell_target,
    get_payload,
    parse_cell_updates,
    parse_optional_float,
    parse_optional_int,
    parse_rule_name,
    parse_state_value,
    parse_topology_spec,
)


page_bp = Blueprint("pages", __name__)
api_bp = Blueprint("api", __name__, url_prefix="/api")

_ExtensionT = TypeVar("_ExtensionT")
JsonRouteResult = Response | tuple[Response, int]


def _require_extension(name: str, expected_type: type[_ExtensionT]) -> _ExtensionT:
    extension = current_app.extensions.get(name)
    if not isinstance(extension, expected_type):
        raise RuntimeError(f"Flask extension '{name}' is not initialized correctly.")
    return extension


def simulation_coordinator() -> SimulationCoordinator:
    return _require_extension("simulation_coordinator", SimulationCoordinator)


def rule_registry() -> RuleRegistry:
    return _require_extension("rule_registry", RuleRegistry)


def frontend_assets() -> FrontendAssetManifest:
    return _require_extension("frontend_assets", FrontendAssetManifest)


def json_error(message: str, status_code: int = 400) -> tuple[Response, int]:
    payload: ApiErrorPayload = {"error": message}
    return jsonify(payload), status_code


def state_response() -> Response:
    return jsonify(simulation_coordinator().get_state().to_dict())


def topology_response() -> Response:
    topology = simulation_coordinator().get_topology()
    return jsonify(topology.to_dict())


def validated_state_action(action: Callable[[JsonObject], None]) -> JsonRouteResult:
    payload = get_payload(request)
    try:
        action(payload)
    except (RequestValidationError, SimulationOperationError) as exc:
        return json_error(str(exc))
    return state_response()


def control_state_action(action: Callable[[], None]) -> Response:
    action()
    return state_response()


def apply_reset_payload(payload: JsonObject) -> None:
    if payload.get("geometry") not in (None, ""):
        raise RequestValidationError("'geometry' must be provided through 'topology_spec'.")
    if payload.get("width") not in (None, "") or payload.get("height") not in (None, ""):
        raise RequestValidationError("'width' and 'height' must be provided through 'topology_spec'.")
    if payload.get("patch_depth") not in (None, ""):
        raise RequestValidationError("'patch_depth' must be provided through 'topology_spec'.")
    topology_spec = parse_topology_spec(payload)
    simulation_coordinator().reset(
        topology_spec=topology_spec,
        rule_name=parse_rule_name(payload, rule_registry()),
        speed=parse_optional_float(payload, "speed"),
        randomize=bool(payload.get("randomize", False)),
    )


def apply_config_payload(payload: JsonObject) -> None:
    if payload.get("geometry") not in (None, ""):
        raise RequestValidationError("'geometry' can only be changed through reset.")
    if payload.get("width") not in (None, "") or payload.get("height") not in (None, ""):
        raise RequestValidationError("'width' and 'height' must be provided through 'topology_spec'.")
    if payload.get("patch_depth") not in (None, ""):
        raise RequestValidationError("'patch_depth' can only be changed through reset.")
    topology_spec = payload.get("topology_spec")
    if topology_spec is not None and not isinstance(topology_spec, dict):
        raise RequestValidationError("'topology_spec' must be an object.")
    disallowed_keys = {"tiling_family", "adjacency_mode", "sizing_mode", "patch_depth"} & set((topology_spec or {}).keys())
    if disallowed_keys:
        disallowed = ", ".join(sorted(disallowed_keys))
        raise RequestValidationError(f"'{disallowed}' can only be changed through reset.")
    topology_patch: TopologySpecPatch = {}
    if topology_spec is not None:
        width = parse_optional_int(topology_spec, "width")
        height = parse_optional_int(topology_spec, "height")
        if width is not None:
            topology_patch["width"] = width
        if height is not None:
            topology_patch["height"] = height
    simulation_coordinator().update_config(
        topology_spec=topology_patch,
        speed=parse_optional_float(payload, "speed"),
        rule_name=parse_rule_name(payload, rule_registry()),
    )


def dispatch_single_cell_target(
    target: CellTargetPayload,
    *,
    by_id: Callable[[str], None],
) -> None:
    by_id(str(target["id"]))


def dispatch_cell_updates(parsed_cells: list[CellUpdatePayload]) -> None:
    id_cells = [
        (cell["id"], cell["state"])
        for cell in parsed_cells
    ]
    if id_cells:
        simulation_coordinator().set_cells_by_id(id_cells)


def apply_toggle_cell_payload(payload: JsonObject) -> None:
    dispatch_single_cell_target(
        parse_cell_target(payload),
        by_id=simulation_coordinator().toggle_cell_by_id,
    )


def apply_set_cell_payload(payload: JsonObject) -> None:
    state = parse_state_value(payload, simulation_coordinator().get_rule())
    dispatch_single_cell_target(
        parse_cell_target(payload),
        by_id=lambda cell_id: simulation_coordinator().set_cell_state_by_id(
            cell_id=cell_id,
            state=state,
        ),
    )


def apply_set_cells_payload(payload: JsonObject) -> None:
    dispatch_cell_updates(parse_cell_updates(payload, simulation_coordinator().get_rule()))


@page_bp.get("/")
def index() -> str:
    entry_assets = frontend_assets().entry_assets("frontend/app.ts")
    return render_template(
        "index.html",
        app_defaults=current_app.config["APP_DEFAULTS"],
        topology_catalog=current_app.config["TOPOLOGY_CATALOG"],
        periodic_face_tilings=current_app.config["PERIODIC_FACE_TILINGS"],
        frontend_script=entry_assets.script_filename,
        frontend_stylesheets=entry_assets.stylesheet_filenames,
    )


@api_bp.get("/state")
def get_state() -> Response:
    return state_response()


@api_bp.get("/rules")
def get_rules() -> Response:
    payload: RulesResponsePayload = {"rules": rule_registry().describe_rules()}
    return jsonify(payload)


@api_bp.get("/topology")
def get_topology() -> Response:
    return topology_response()


@api_bp.get("/meta")
def get_meta() -> Response:
    return jsonify(current_app.config["SERVER_META"])


@api_bp.post("/control/start")
def start() -> Response:
    return control_state_action(simulation_coordinator().start)


@api_bp.post("/control/pause")
def pause() -> Response:
    return control_state_action(simulation_coordinator().pause)


@api_bp.post("/control/resume")
def resume() -> Response:
    return control_state_action(simulation_coordinator().resume)


@api_bp.post("/control/step")
def step() -> Response:
    return control_state_action(simulation_coordinator().step)


@api_bp.post("/control/reset")
def reset() -> JsonRouteResult:
    return validated_state_action(apply_reset_payload)


@api_bp.post("/config")
def update_config() -> JsonRouteResult:
    return validated_state_action(apply_config_payload)


@api_bp.post("/cells/toggle")
def toggle_cell() -> JsonRouteResult:
    return validated_state_action(apply_toggle_cell_payload)


@api_bp.post("/cells/set")
def set_cell() -> JsonRouteResult:
    return validated_state_action(apply_set_cell_payload)


@api_bp.post("/cells/set-many")
def set_cells() -> JsonRouteResult:
    return validated_state_action(apply_set_cells_payload)
