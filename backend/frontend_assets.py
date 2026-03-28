from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FrontendEntryAssets:
    script_filename: str
    stylesheet_filenames: tuple[str, ...] = ()


class FrontendAssetManifest:
    def __init__(self, manifest_path: Path, manifest: dict[str, dict[str, Any]]) -> None:
        self._manifest_path = manifest_path
        self._manifest = manifest

    @classmethod
    def load(cls, static_folder: str | None) -> "FrontendAssetManifest":
        if not static_folder:
            raise RuntimeError("Frontend assets could not be resolved because Flask static_folder is not configured.")

        manifest_path = Path(static_folder) / "dist" / "manifest.json"
        if not manifest_path.exists():
            raise RuntimeError(
                "Frontend build manifest is missing at "
                f"{manifest_path}. Run 'npm run build:frontend' before starting the app."
            )

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise RuntimeError(f"Frontend build manifest at {manifest_path} is invalid.")

        return cls(manifest_path=manifest_path, manifest=manifest)

    def entry_assets(self, entry_name: str) -> FrontendEntryAssets:
        record = self._resolve_record(entry_name)
        script_filename = record.get("file")
        if not isinstance(script_filename, str) or not script_filename:
            raise RuntimeError(
                f"Frontend manifest entry '{entry_name}' in {self._manifest_path} does not define a script file."
            )

        stylesheet_filenames = tuple(
            f"dist/{stylesheet}"
            for stylesheet in record.get("css", [])
            if isinstance(stylesheet, str) and stylesheet
        )
        return FrontendEntryAssets(
            script_filename=f"dist/{script_filename}",
            stylesheet_filenames=stylesheet_filenames,
        )

    def _resolve_record(self, entry_name: str) -> dict[str, Any]:
        if entry_name in self._manifest:
            return self._manifest[entry_name]

        for manifest_key, manifest_value in self._manifest.items():
            if not isinstance(manifest_value, dict):
                continue
            if manifest_value.get("src") == entry_name:
                return manifest_value
            if manifest_key.endswith(entry_name):
                return manifest_value

        raise RuntimeError(
            f"Frontend entry '{entry_name}' was not found in manifest {self._manifest_path}."
        )
