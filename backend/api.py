import os
from pathlib import Path

from flask import Flask

from backend.bootstrap_data import describe_aperiodic_families
from backend.defaults import APP_DEFAULTS
from backend.dev_server import APP_NAME
from backend.frontend_assets import FrontendAssetManifest
from backend.payload_types import ServerMetaPayload
from backend.simulation.periodic_face_tilings import describe_periodic_face_tilings
from backend.simulation.bootstrap import register_simulation
from backend.simulation.topology_catalog import describe_topologies
from backend.web.routes import api_bp, page_bp


def create_app(*, instance_path: str | None = None) -> Flask:
    resolved_instance_path = instance_path or os.environ.get("APP_INSTANCE_PATH")
    if resolved_instance_path:
        app = Flask(
            __name__,
            template_folder="../templates",
            static_folder="../static",
            instance_path=resolved_instance_path,
        )
    else:
        app = Flask(
            __name__,
            template_folder="../templates",
            static_folder="../static",
        )
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    app.config["APP_DEFAULTS"] = APP_DEFAULTS
    app.config["TOPOLOGY_CATALOG"] = describe_topologies()
    app.config["PERIODIC_FACE_TILINGS"] = describe_periodic_face_tilings()
    app.config["APERIODIC_FAMILIES"] = describe_aperiodic_families()
    server_meta: ServerMetaPayload = {
        "app_name": APP_NAME,
    }
    app.config["SERVER_META"] = server_meta
    app.extensions["frontend_assets"] = FrontendAssetManifest.load(app.static_folder)

    register_simulation(app)

    app.register_blueprint(page_bp)
    app.register_blueprint(api_bp)
    return app
