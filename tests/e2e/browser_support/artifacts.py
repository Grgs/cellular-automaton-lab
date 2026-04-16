from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

from playwright.sync_api import Page

from tests.e2e.browser_support.render_review import canvas_visual_summary

if TYPE_CHECKING:
    from tests.e2e.support_runtime_host import BrowserRuntimeHost


E2E_ARTIFACTS_DIR_ENV = "E2E_ARTIFACTS_DIR"
E2E_CAPTURE_SUCCESS_ARTIFACTS_ENV = "E2E_CAPTURE_SUCCESS_ARTIFACTS"
DEFAULT_BROWSER_ARTIFACTS_DIRNAME = "browser-artifacts"


def resolve_artifact_root() -> Path | None:
    configured_root = os.environ.get(E2E_ARTIFACTS_DIR_ENV)
    if not configured_root:
        return None
    artifact_root = Path(configured_root)
    artifact_root.mkdir(parents=True, exist_ok=True)
    return artifact_root


def sanitize_artifact_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", name).strip(".-") or "unnamed"


def create_artifact_dir(
    *,
    name: str,
    root: Path | None = None,
    default_parent: Path | None = None,
    temp_prefix: str = "cellular-automaton-browser-artifacts-",
) -> Path:
    sanitized_name = sanitize_artifact_name(name)
    artifact_root = root or resolve_artifact_root()
    if artifact_root is None:
        if default_parent is not None:
            artifact_dir = default_parent / sanitized_name
            if artifact_dir.exists():
                shutil.rmtree(artifact_dir)
            artifact_dir.mkdir(parents=True, exist_ok=True)
            return artifact_dir
        return Path(tempfile.mkdtemp(prefix=temp_prefix))
    artifact_dir = artifact_root / sanitized_name
    if artifact_dir.exists():
        shutil.rmtree(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    return artifact_dir


def write_run_manifest(artifact_dir: Path, manifest: dict[str, Any]) -> Path:
    path = artifact_dir / "run-manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return path


def capture_browser_artifacts(
    artifact_dir: Path,
    *,
    host: BrowserRuntimeHost,
    page: Page | None,
    console_messages: list[str] | None,
    run_manifest: dict[str, Any] | None = None,
) -> None:
    if not artifact_dir.exists():
        artifact_dir.mkdir(parents=True, exist_ok=True)
    if page is not None and not page.is_closed():
        page.screenshot(path=str(artifact_dir / "page.png"), full_page=True)
        (artifact_dir / "page.html").write_text(page.content(), encoding="utf-8")
        try:
            page.locator("#grid").screenshot(path=str(artifact_dir / "canvas.png"))
        except Exception as exc:
            (artifact_dir / "canvas-error.txt").write_text(str(exc), encoding="utf-8")
        try:
            summary = canvas_visual_summary(page)
            (artifact_dir / "render-summary.json").write_text(
                json.dumps(summary, indent=2, sort_keys=True),
                encoding="utf-8",
            )
        except Exception as exc:
            (artifact_dir / "render-summary-error.txt").write_text(str(exc), encoding="utf-8")
    (artifact_dir / "console.txt").write_text(
        "\n".join(console_messages) if console_messages else "(no console messages)",
        encoding="utf-8",
    )
    if run_manifest is not None:
        write_run_manifest(artifact_dir, run_manifest)
    host.capture_failure_artifacts(artifact_dir, page)


def capture_browser_failure_artifacts(
    artifact_dir: Path,
    *,
    host: BrowserRuntimeHost,
    page: Page | None,
    console_messages: list[str] | None,
    run_manifest: dict[str, Any] | None = None,
) -> None:
    capture_browser_artifacts(
        artifact_dir,
        host=host,
        page=page,
        console_messages=console_messages,
        run_manifest=run_manifest,
    )
