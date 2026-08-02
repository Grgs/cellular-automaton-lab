from __future__ import annotations

from flask import Blueprint, Response, current_app, jsonify, render_template, request
from markupsafe import Markup

from backend.app_shell import render_server_app_shell
from backend.application_commands import (
    ApplicationCommand,
    ApplicationCommandDispatcher,
    CoordinatorCommandTarget,
)
from backend.bootstrap_data import build_bootstrap_payload
from backend.frontend_assets import FrontendAssetManifest
from backend.public_errors import PublicApiError
from backend.rules import RuleRegistry
from backend.simulation.coordinator import SimulationCoordinator
from backend.simulation.sessions import DEFAULT_SESSION_ID, SimulationSessionRegistry
from backend.simulation.topology_builders import TopologyCellBudgetExceeded
from backend.web.requests import get_payload

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
    return simulation_sessions().get(session_id)


def rule_registry() -> RuleRegistry:
    return _require_extension("rule_registry", RuleRegistry)


def frontend_assets() -> FrontendAssetManifest:
    return _require_extension("frontend_assets", FrontendAssetManifest)


def command_dispatcher(session_id: str = DEFAULT_SESSION_ID) -> ApplicationCommandDispatcher:
    return ApplicationCommandDispatcher(
        CoordinatorCommandTarget(simulation_coordinator(session_id), rule_registry())
    )


def dispatch_command(
    command: ApplicationCommand,
    session_id: str = DEFAULT_SESSION_ID,
    *,
    payload: dict[str, object] | None = None,
) -> dict[str, object]:
    return dict(command_dispatcher(session_id).dispatch(command, payload).payload)


@api_bp.app_errorhandler(TopologyCellBudgetExceeded)
def handle_topology_cell_budget_error(
    exc: TopologyCellBudgetExceeded,
) -> tuple[Response, int]:
    return jsonify(exc.to_payload()), 400


# Invalid session ids, request-contract violations, and rejected simulation
# operations are all client errors reported as a 400 with a JSON body. One
# app-wide handler for their shared public-error base lets every route resolve
# a coordinator and apply its action directly without repeating try/except.
@api_bp.app_errorhandler(PublicApiError)
def handle_api_request_error(exc: PublicApiError) -> tuple[Response, int]:
    return jsonify(exc.to_payload()), 400


def state_response(session_id: str = DEFAULT_SESSION_ID) -> Response:
    return jsonify(dispatch_command(ApplicationCommand.STATE_GET, session_id))


def topology_response(session_id: str = DEFAULT_SESSION_ID) -> Response:
    return jsonify(simulation_coordinator(session_id).get_topology().to_dict())


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
def get_state(session_id: str = DEFAULT_SESSION_ID) -> Response:
    return state_response(session_id)


@api_bp.get("/rules")
@session_api_bp.get("/rules")
def get_rules(session_id: str = DEFAULT_SESSION_ID) -> Response:
    return jsonify(dispatch_command(ApplicationCommand.RULES_LIST, session_id))


@api_bp.get("/topology")
@session_api_bp.get("/topology")
def get_topology(session_id: str = DEFAULT_SESSION_ID) -> Response:
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
    return jsonify(
        dispatch_command(
            ApplicationCommand.COMPARE_RUN,
            session_id,
            payload=get_payload(request),
        )
    )


@api_bp.post("/compare/filmstrip")
@session_api_bp.post("/compare/filmstrip")
def compare_filmstrip(session_id: str = DEFAULT_SESSION_ID) -> JsonRouteResult:
    return jsonify(
        dispatch_command(
            ApplicationCommand.FILMSTRIP_RUN,
            session_id,
            payload=get_payload(request),
        )
    )


@api_bp.post("/topology/preview")
@session_api_bp.post("/topology/preview")
def topology_preview(session_id: str = DEFAULT_SESSION_ID) -> JsonRouteResult:
    return jsonify(
        dispatch_command(
            ApplicationCommand.TOPOLOGY_PREVIEW,
            session_id,
            payload=get_payload(request),
        )
    )


@api_bp.post("/control/start")
@session_api_bp.post("/control/start")
def start(session_id: str = DEFAULT_SESSION_ID) -> Response:
    return jsonify(dispatch_command(ApplicationCommand.SIMULATION_START, session_id))


@api_bp.post("/control/pause")
@session_api_bp.post("/control/pause")
def pause(session_id: str = DEFAULT_SESSION_ID) -> Response:
    return jsonify(dispatch_command(ApplicationCommand.SIMULATION_PAUSE, session_id))


@api_bp.post("/control/resume")
@session_api_bp.post("/control/resume")
def resume(session_id: str = DEFAULT_SESSION_ID) -> Response:
    return jsonify(dispatch_command(ApplicationCommand.SIMULATION_RESUME, session_id))


@api_bp.post("/control/step")
@session_api_bp.post("/control/step")
def step(session_id: str = DEFAULT_SESSION_ID) -> Response:
    return jsonify(dispatch_command(ApplicationCommand.SIMULATION_STEP, session_id))


@api_bp.post("/control/reset")
@session_api_bp.post("/control/reset")
def reset(session_id: str = DEFAULT_SESSION_ID) -> Response:
    return jsonify(
        dispatch_command(
            ApplicationCommand.SIMULATION_RESET,
            session_id,
            payload=get_payload(request),
        )
    )


@api_bp.post("/config")
@session_api_bp.post("/config")
def update_config(session_id: str = DEFAULT_SESSION_ID) -> Response:
    return jsonify(
        dispatch_command(
            ApplicationCommand.SIMULATION_CONFIGURE,
            session_id,
            payload=get_payload(request),
        )
    )


@api_bp.post("/cells/toggle")
@session_api_bp.post("/cells/toggle")
def toggle_cell(session_id: str = DEFAULT_SESSION_ID) -> Response:
    return jsonify(
        dispatch_command(
            ApplicationCommand.CELL_TOGGLE,
            session_id,
            payload=get_payload(request),
        )
    )


@api_bp.post("/cells/set")
@session_api_bp.post("/cells/set")
def set_cell(session_id: str = DEFAULT_SESSION_ID) -> Response:
    return jsonify(
        dispatch_command(
            ApplicationCommand.CELL_SET,
            session_id,
            payload=get_payload(request),
        )
    )


@api_bp.post("/cells/set-many")
@session_api_bp.post("/cells/set-many")
def set_cells(session_id: str = DEFAULT_SESSION_ID) -> Response:
    return jsonify(
        dispatch_command(
            ApplicationCommand.CELLS_SET_MANY,
            session_id,
            payload=get_payload(request),
        )
    )
