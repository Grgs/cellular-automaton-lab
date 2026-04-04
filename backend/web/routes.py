from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from flask import Blueprint, Response, current_app, jsonify, render_template, request
from markupsafe import Markup

from backend.app_shell import render_server_app_shell
from backend.bootstrap_data import build_bootstrap_payload
from backend.payload_types import (
    ApiErrorPayload,
    RawJsonObject,
    RulesResponsePayload,
)
from backend.rules import RuleRegistry
from backend.frontend_assets import FrontendAssetManifest
from backend.simulation.coordinator import SimulationCoordinator
from backend.simulation.service import SimulationOperationError
from backend.web.state_actions import StateActionService
from backend.web.requests import (
    RequestValidationError,
    get_payload,
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


def state_actions() -> StateActionService:
    return StateActionService(simulation_coordinator(), rule_registry())


def json_error(message: str, status_code: int = 400) -> tuple[Response, int]:
    payload: ApiErrorPayload = {"error": message}
    return jsonify(payload), status_code


def state_response() -> Response:
    return jsonify(simulation_coordinator().get_state().to_dict())


def topology_response() -> Response:
    topology = simulation_coordinator().get_topology()
    return jsonify(topology.to_dict())


def validated_state_action(action: Callable[[RawJsonObject], None]) -> JsonRouteResult:
    payload = get_payload(request)
    try:
        action(payload)
    except (RequestValidationError, SimulationOperationError) as exc:
        return json_error(str(exc))
    return state_response()


def control_state_action(action: Callable[[], None]) -> Response:
    action()
    return state_response()


@page_bp.get("/")
def index() -> str:
    entry_assets = frontend_assets().entry_assets("frontend/server-entry.ts")
    return render_template(
        "index.html",
        app_defaults=current_app.config["APP_DEFAULTS"],
        app_shell=Markup(
            render_server_app_shell(
                current_app.config["APP_DEFAULTS"],
                current_app.config["TOPOLOGY_CATALOG"],
            )
        ),
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


@api_bp.get("/bootstrap")
def get_bootstrap() -> Response:
    return jsonify(build_bootstrap_payload(current_app.config["SERVER_META"]))


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
    return validated_state_action(state_actions().apply_reset_payload)


@api_bp.post("/config")
def update_config() -> JsonRouteResult:
    return validated_state_action(state_actions().apply_config_payload)


@api_bp.post("/cells/toggle")
def toggle_cell() -> JsonRouteResult:
    return validated_state_action(state_actions().apply_toggle_cell_payload)


@api_bp.post("/cells/set")
def set_cell() -> JsonRouteResult:
    return validated_state_action(state_actions().apply_set_cell_payload)


@api_bp.post("/cells/set-many")
def set_cells() -> JsonRouteResult:
    return validated_state_action(state_actions().apply_set_cells_payload)
