from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from backend.payload_types import FrontendManifestPayload, FrontendManifestRecord, JsonObject


@dataclass(frozen=True)
class FrontendEntryAssets:
    script_filename: str
    stylesheet_filenames: tuple[str, ...] = ()


class FrontendAssetManifest:
    def __init__(self, manifest_path: Path, manifest: FrontendManifestPayload) -> None:
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

        normalized_manifest: FrontendManifestPayload = {}
        for entry_name, record in manifest.items():
            if not isinstance(entry_name, str) or not isinstance(record, dict):
                raise RuntimeError(f"Frontend build manifest at {manifest_path} is invalid.")
            normalized_manifest[entry_name] = cls._normalize_record(record)

        return cls(manifest_path=manifest_path, manifest=normalized_manifest)

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

    @staticmethod
    def _normalize_record(record: JsonObject) -> FrontendManifestRecord:
        normalized_record: FrontendManifestRecord = {}

        file_value = record.get("file")
        if isinstance(file_value, str):
            normalized_record["file"] = file_value

        src_value = record.get("src")
        if isinstance(src_value, str):
            normalized_record["src"] = src_value

        is_entry_value = record.get("isEntry")
        if isinstance(is_entry_value, bool):
            normalized_record["isEntry"] = is_entry_value

        css_value = record.get("css")
        if isinstance(css_value, list):
            normalized_record["css"] = [
                stylesheet
                for stylesheet in css_value
                if isinstance(stylesheet, str) and stylesheet
            ]

        return normalized_record

    def _resolve_record(self, entry_name: str) -> FrontendManifestRecord:
        if entry_name in self._manifest:
            return self._manifest[entry_name]

        for manifest_key, manifest_value in self._manifest.items():
            if manifest_value.get("src") == entry_name:
                return manifest_value
            if manifest_key.endswith(entry_name):
                return manifest_value

        raise RuntimeError(
            f"Frontend entry '{entry_name}' was not found in manifest {self._manifest_path}."
        )
