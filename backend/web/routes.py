from __future__ import annotations

from collections.abc import Callable

from flask import Blueprint, Response, current_app, jsonify, render_template, request
from markupsafe import Markup

from backend.app_shell import render_server_app_shell
from backend.bootstrap_data import build_bootstrap_payload
from backend.frontend_assets import FrontendAssetManifest
from backend.payload_types import (
    ApiErrorPayload,
    RawJsonObject,
    RulesResponsePayload,
)
from backend.rules import RuleRegistry
from backend.simulation.coordinator import SimulationCoordinator
from backend.simulation.seeding import run_compare_request
from backend.simulation.service import SimulationOperationError
from backend.simulation.sessions import (
    DEFAULT_SESSION_ID,
    SimulationSessionError,
    SimulationSessionRegistry,
)
from backend.simulation.topology_preview import build_topology_preview
from backend.web.requests import (
    RequestValidationError,
    get_payload,
)
from backend.web.state_actions import StateActionService

page_bp = Blueprint("pages", __name__)
api_bp = Blueprint("api", __name__, url_prefix="/api")
session_api_bp = Blueprint("session_api", __name__, url_prefix="/api/sessions/<session_id>")

JsonRouteResult = Response | tuple[Response, int]


def _require_extension[ExtensionT](name: str, expected_type: type[ExtensionT]) -> ExtensionT:
    extension = current_app.extensions.get(name)
    if not isinstance(extension, expected_type):
        raise RuntimeError(f"Flask extension '{name}' is not initialized correctly.")
    return extension


def simulation_sessions() -> SimulationSessionRegistry:
    return _require_extension("simulation_sessions", SimulationSessionRegistry)


def simulation_coordinator(session_id: str = DEFAULT_SESSION_ID) -> SimulationCoordinator:
    try:
        return simulation_sessions().get(session_id)
    except SimulationSessionError as exc:
        raise RequestValidationError(str(exc)) from exc


def rule_registry() -> RuleRegistry:
    return _require_extension("rule_registry", RuleRegistry)


def frontend_assets() -> FrontendAssetManifest:
    return _require_extension("frontend_assets", FrontendAssetManifest)


def state_actions(session_id: str = DEFAULT_SESSION_ID) -> StateActionService:
    return StateActionService(simulation_coordinator(session_id), rule_registry())


def json_error(message: str, status_code: int = 400) -> tuple[Response, int]:
    payload: ApiErrorPayload = {"error": message}
    return jsonify(payload), status_code


def state_response(session_id: str = DEFAULT_SESSION_ID) -> JsonRouteResult:
    try:
        coordinator = simulation_coordinator(session_id)
    except RequestValidationError as exc:
        return json_error(str(exc))
    return jsonify(coordinator.get_state().to_dict())


def topology_response(session_id: str = DEFAULT_SESSION_ID) -> JsonRouteResult:
    try:
        coordinator = simulation_coordinator(session_id)
    except RequestValidationError as exc:
        return json_error(str(exc))
    topology = coordinator.get_topology()
    return jsonify(topology.to_dict())


def validated_state_action(
    session_id: str,
    action_factory: Callable[[StateActionService], Callable[[RawJsonObject], None]],
) -> JsonRouteResult:
    payload = get_payload(request)
    try:
        action_factory(state_actions(session_id))(payload)
    except (RequestValidationError, SimulationOperationError) as exc:
        return json_error(str(exc))
    return state_response(session_id)


def control_state_action(
    session_id: str,
    action_factory: Callable[[SimulationCoordinator], Callable[[], None]],
) -> JsonRouteResult:
    try:
        action_factory(simulation_coordinator(session_id))()
    except RequestValidationError as exc:
        return json_error(str(exc))
    return state_response(session_id)


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
        aperiodic_families=current_app.config["APERIODIC_FAMILIES"],
        frontend_script=entry_assets.script_filename,
        frontend_stylesheets=entry_assets.stylesheet_filenames,
    )


@api_bp.get("/state")
@session_api_bp.get("/state")
def get_state(session_id: str = DEFAULT_SESSION_ID) -> JsonRouteResult:
    return state_response(session_id)


@api_bp.get("/rules")
@session_api_bp.get("/rules")
def get_rules(session_id: str = DEFAULT_SESSION_ID) -> Response:
    payload: RulesResponsePayload = {"rules": rule_registry().describe_rules()}
    return jsonify(payload)


@api_bp.get("/topology")
@session_api_bp.get("/topology")
def get_topology(session_id: str = DEFAULT_SESSION_ID) -> JsonRouteResult:
    return topology_response(session_id)


@api_bp.get("/meta")
def get_meta() -> Response:
    return jsonify(current_app.config["SERVER_META"])


@api_bp.get("/bootstrap")
def get_bootstrap() -> Response:
    return jsonify(build_bootstrap_payload(current_app.config["SERVER_META"]))


@api_bp.post("/compare")
@session_api_bp.post("/compare")
def compare(session_id: str = DEFAULT_SESSION_ID) -> JsonRouteResult:
    payload = get_payload(request)
    try:
        comparison = run_compare_request(payload)
    except (RequestValidationError, ValueError) as exc:
        return json_error(str(exc))
    return jsonify({"comparison": comparison})


@api_bp.post("/topology/preview")
@session_api_bp.post("/topology/preview")
def topology_preview(session_id: str = DEFAULT_SESSION_ID) -> JsonRouteResult:
    payload = get_payload(request)
    try:
        topology = build_topology_preview(payload)
    except (RequestValidationError, ValueError) as exc:
        return json_error(str(exc))
    return jsonify({"topology_preview": topology})


@api_bp.post("/control/start")
@session_api_bp.post("/control/start")
def start(session_id: str = DEFAULT_SESSION_ID) -> JsonRouteResult:
    return control_state_action(session_id, lambda coordinator: coordinator.start)


@api_bp.post("/control/pause")
@session_api_bp.post("/control/pause")
def pause(session_id: str = DEFAULT_SESSION_ID) -> JsonRouteResult:
    return control_state_action(session_id, lambda coordinator: coordinator.pause)


@api_bp.post("/control/resume")
@session_api_bp.post("/control/resume")
def resume(session_id: str = DEFAULT_SESSION_ID) -> JsonRouteResult:
    return control_state_action(session_id, lambda coordinator: coordinator.resume)


@api_bp.post("/control/step")
@session_api_bp.post("/control/step")
def step(session_id: str = DEFAULT_SESSION_ID) -> JsonRouteResult:
    return control_state_action(session_id, lambda coordinator: coordinator.step)


@api_bp.post("/control/reset")
@session_api_bp.post("/control/reset")
def reset(session_id: str = DEFAULT_SESSION_ID) -> JsonRouteResult:
    return validated_state_action(session_id, lambda actions: actions.apply_reset_payload)


@api_bp.post("/config")
@session_api_bp.post("/config")
def update_config(session_id: str = DEFAULT_SESSION_ID) -> JsonRouteResult:
    return validated_state_action(session_id, lambda actions: actions.apply_config_payload)


@api_bp.post("/cells/toggle")
@session_api_bp.post("/cells/toggle")
def toggle_cell(session_id: str = DEFAULT_SESSION_ID) -> JsonRouteResult:
    return validated_state_action(session_id, lambda actions: actions.apply_toggle_cell_payload)


@api_bp.post("/cells/set")
@session_api_bp.post("/cells/set")
def set_cell(session_id: str = DEFAULT_SESSION_ID) -> JsonRouteResult:
    return validated_state_action(session_id, lambda actions: actions.apply_set_cell_payload)


@api_bp.post("/cells/set-many")
@session_api_bp.post("/cells/set-many")
def set_cells(session_id: str = DEFAULT_SESSION_ID) -> JsonRouteResult:
    return validated_state_action(session_id, lambda actions: actions.apply_set_cells_payload)
