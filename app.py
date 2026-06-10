import os
import sys
from pathlib import Path

from backend.api import create_app
from backend.dev_server import prepare_dev_server, resolve_replace_existing
from backend.frontend_build import require_current_frontend_server_build

app = create_app()


if __name__ == "__main__":
    root_dir = Path(__file__).resolve().parent
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    replace_existing = resolve_replace_existing(os.environ.get("DEV_REPLACE_SERVER"))
    allow_stale_frontend_build = str(
        os.environ.get("ALLOW_STALE_FRONTEND_BUILD", "")
    ).strip().lower() in {"1", "true", "yes", "on"}
    require_current_frontend_server_build(
        root_dir,
        app.static_folder,
        allow_stale=allow_stale_frontend_build,
    )
    try:
        replaced_listener = prepare_dev_server(
            host=host,
            port=port,
            app_entrypoint=Path(__file__).resolve(),
            replace_existing=replace_existing,
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from None

    if replaced_listener is not None and replaced_listener.pid is not None:
        print(f"Replaced stale dev server on port {port} (pid {replaced_listener.pid}).")

    app.run(
        host=host,
        port=port,
        debug=True,
        use_reloader=False,
    )
