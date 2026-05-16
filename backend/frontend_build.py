from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_FRONTEND_SOURCE_DIRS = ("frontend",)
_FRONTEND_SOURCE_FILES = ("package.json", "package-lock.json", "vite.config.ts")
_FRONTEND_BUILD_BYPASS_ENV = "ALLOW_STALE_FRONTEND_BUILD"


def _iter_frontend_source_paths(root: Path) -> tuple[Path, ...]:
    paths: list[Path] = []
    for relative_dir in _FRONTEND_SOURCE_DIRS:
        absolute_dir = root / relative_dir
        if not absolute_dir.exists():
            continue
        paths.extend(path for path in absolute_dir.rglob("*") if path.is_file())
    for relative_file in _FRONTEND_SOURCE_FILES:
        absolute_file = root / relative_file
        if absolute_file.exists():
            paths.append(absolute_file)
    return tuple(sorted(dict.fromkeys(paths)))


def _iter_frontend_build_paths(static_folder: Path) -> tuple[Path, ...]:
    dist_dir = static_folder / "dist"
    if not dist_dir.exists():
        return ()
    return tuple(sorted(path for path in dist_dir.rglob("*") if path.is_file()))


def _path_mtime_ns(path: Path) -> int:
    return path.stat().st_mtime_ns


def _newest_path(paths: tuple[Path, ...]) -> Path | None:
    if not paths:
        return None
    return max(paths, key=_path_mtime_ns)


def frontend_server_build_status(root: Path, static_folder: str | Path | None) -> dict[str, Any]:
    if not static_folder:
        return {
            "buildCurrent": False,
            "reason": "static folder is not configured",
            "recommendedBuildCommand": "npm run build:frontend",
        }

    resolved_root = Path(root)
    resolved_static_folder = Path(static_folder)
    manifest_path = resolved_static_folder / "dist" / "manifest.json"
    if not manifest_path.exists():
        return {
            "buildCurrent": False,
            "reason": "frontend build manifest is missing",
            "recommendedBuildCommand": "npm run build:frontend",
            "manifestPath": manifest_path.as_posix(),
        }

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "buildCurrent": False,
            "reason": "frontend build manifest is invalid",
            "recommendedBuildCommand": "npm run build:frontend",
            "manifestPath": manifest_path.as_posix(),
        }
    if not isinstance(manifest, dict):
        return {
            "buildCurrent": False,
            "reason": "frontend build manifest is invalid",
            "recommendedBuildCommand": "npm run build:frontend",
            "manifestPath": manifest_path.as_posix(),
        }

    source_paths = _iter_frontend_source_paths(resolved_root)
    build_paths = _iter_frontend_build_paths(resolved_static_folder)
    newest_source = _newest_path(source_paths)
    newest_build = _newest_path(build_paths)

    if newest_build is None:
        return {
            "buildCurrent": False,
            "reason": "frontend build outputs are missing",
            "recommendedBuildCommand": "npm run build:frontend",
            "manifestPath": manifest_path.as_posix(),
        }

    if newest_source is None:
        return {
            "buildCurrent": True,
            "reason": "frontend build outputs are current",
            "recommendedBuildCommand": "npm run build:frontend",
            "manifestPath": manifest_path.as_posix(),
            "newestBuildPath": newest_build.relative_to(resolved_root).as_posix(),
        }

    source_is_newer = _path_mtime_ns(newest_source) > _path_mtime_ns(newest_build)
    return {
        "buildCurrent": not source_is_newer,
        "reason": (
            "frontend sources are newer than the server bundle"
            if source_is_newer
            else "frontend build outputs are current"
        ),
        "recommendedBuildCommand": "npm run build:frontend",
        "manifestPath": manifest_path.as_posix(),
        "newestSourcePath": newest_source.relative_to(resolved_root).as_posix(),
        "newestBuildPath": newest_build.relative_to(resolved_root).as_posix(),
    }


def require_current_frontend_server_build(
    root: Path,
    static_folder: str | Path | None,
    *,
    allow_stale: bool = False,
) -> None:
    if allow_stale:
        return
    status = frontend_server_build_status(root, static_folder)
    if bool(status.get("buildCurrent")):
        return
    reason = str(status.get("reason") or "frontend build is stale")
    build_command = str(status.get("recommendedBuildCommand") or "npm run build:frontend")
    newest_source = status.get("newestSourcePath")
    newest_build = status.get("newestBuildPath")
    detail = ""
    if isinstance(newest_source, str) and isinstance(newest_build, str):
        detail = f" Newest source: {newest_source}. Newest build output: {newest_build}."
    raise RuntimeError(
        f"Frontend server build is not current: {reason}.{detail} "
        f"Run `{build_command}` or `npm run dev:frontend` before starting the app. "
        f"Set `{_FRONTEND_BUILD_BYPASS_ENV}=1` to bypass this check intentionally."
    )
