from __future__ import annotations

import argparse
import ast
import gzip
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from backend.simulation.periodic_face_catalog_data import (
    load_periodic_face_catalog_sources,
)
from tools._common import ROOT_DIR
from tools.add_periodic_tiling import PlannedWrite
from tools.generate_tiling_preview import update_preview_source

_DESCRIPTOR_DIR = Path("backend/simulation/data/periodic_face_patterns")
_METADATA_DIR = Path("backend/simulation/data/periodic_face_catalog")
_AGGREGATE_PATH = Path("backend/simulation/data/periodic_face_catalog.json")
_REFERENCE_DIR = Path("backend/simulation/reference_specs/periodic")
_PALETTE_PATH = Path("frontend/canvas/family-dead-palette-manifest.json")
_PREVIEW_PATH = Path("frontend/controls/tiling-preview-data.ts")
_BOOTSTRAP_PATH = Path("frontend/test-fixtures/bootstrap-data.json")
_BUDGET_PATH = Path("tools/standalone_bundle_budget.json")
_GENERATION_ONLY_FIELDS = frozenset({"palette", "preview_data", "source_urls"})


def _literal_string(node: ast.AST | None) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _reference_records(root: Path) -> dict[str, tuple[str, ...]]:
    records: dict[str, tuple[str, ...]] = {}
    for path in sorted((root / _REFERENCE_DIR).glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            function_name = node.func.id if isinstance(node.func, ast.Name) else None
            if function_name != "ReferenceFamilySpec":
                continue
            keywords = {keyword.arg: keyword.value for keyword in node.keywords if keyword.arg}
            geometry = _literal_string(keywords.get("geometry"))
            urls_node = keywords.get("source_urls")
            if geometry is None:
                continue
            urls = (
                tuple(
                    value for item in urls_node.elts if (value := _literal_string(item)) is not None
                )
                if isinstance(urls_node, (ast.Tuple, ast.List))
                else ()
            )
            if geometry in records:
                raise ValueError(f"Duplicate periodic reference specs for '{geometry}'.")
            records[geometry] = urls
    return records


def _descriptor_payloads(root: Path) -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {}
    for path in sorted((root / _DESCRIPTOR_DIR).glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        geometry = payload.get("geometry")
        if not isinstance(payload, dict) or not isinstance(geometry, str):
            raise ValueError(f"Invalid periodic descriptor: {path}")
        payloads[geometry] = payload
    return payloads


def discover_catalog_sources(root: Path = ROOT_DIR) -> dict[str, dict[str, Any]]:
    descriptors = _descriptor_payloads(root)
    references = _reference_records(root)
    metadata = load_periodic_face_catalog_sources(root / _METADATA_DIR)
    descriptor_keys = set(descriptors)
    metadata_keys = set(metadata)
    reference_keys = set(references)
    problems: list[str] = []
    if missing := sorted(descriptor_keys - metadata_keys):
        problems.append("descriptors missing catalog metadata: " + ", ".join(missing))
    if orphaned := sorted(metadata_keys - descriptor_keys):
        problems.append("catalog metadata missing descriptors: " + ", ".join(orphaned))
    if missing := sorted(descriptor_keys - reference_keys):
        problems.append("descriptors missing reference specs: " + ", ".join(missing))
    if problems:
        raise ValueError("; ".join(problems))
    return metadata


def _aggregate_payload(metadata: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        (
            {key: value for key, value in item.items() if key not in _GENERATION_ONLY_FIELDS}
            for item in metadata.values()
        ),
        key=lambda item: (int(item["picker_order"]), str(item["geometry"])),
    )


def _ordered_metadata(metadata: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        metadata.values(),
        key=lambda item: (int(item["picker_order"]), str(item["geometry"])),
    )


def _render_aggregate(metadata: dict[str, dict[str, Any]]) -> str:
    return json.dumps(_aggregate_payload(metadata), indent=2) + "\n"


def _render_palette_source(
    source: str,
    metadata: dict[str, dict[str, Any]],
) -> str:
    payload = json.loads(source)
    existing = [item for item in payload["families"] if isinstance(item, dict)]
    periodic_keys = set(metadata)
    first_periodic = next(
        (index for index, item in enumerate(existing) if item.get("geometry") in periodic_keys),
        len(existing),
    )
    nonperiodic = [item for item in existing if item.get("geometry") not in periodic_keys]
    insertion_index = sum(
        1 for item in existing[:first_periodic] if item.get("geometry") not in periodic_keys
    )
    periodic_entries = [
        item["palette"]
        for item in _ordered_metadata(metadata)
        if isinstance(item.get("palette"), dict)
    ]
    payload["families"] = (
        nonperiodic[:insertion_index] + periodic_entries + nonperiodic[insertion_index:]
    )
    rendered = json.dumps(payload, indent=2)
    rendered = re.sub(
        r'\{\n\s+"kind": ([^\n]+)\n\s+\}',
        r'{"kind": \1}',
        rendered,
    )
    rendered = re.sub(
        r'\{\n\s+"token": ([^\n]+)\n\s+\}',
        r'{"token": \1}',
        rendered,
    )
    return rendered + "\n"


def _render_preview_source(
    source: str,
    metadata: dict[str, dict[str, Any]],
) -> str:
    rendered = source
    for item in _ordered_metadata(metadata):
        geometry = str(item["geometry"])
        polygon_data = str(item["preview_data"])
        rendered, _ = update_preview_source(rendered, geometry, polygon_data)
    return rendered


def refresh_bootstrap_budget_source(source: str, bootstrap_data: bytes) -> str:
    payload = json.loads(source)
    category = next(item for item in payload["categories"] if item.get("name") == "bootstrap-data")
    actuals = {
        "raw": len(bootstrap_data),
        "gzip": len(gzip.compress(bootstrap_data, mtime=0)),
    }
    increments = {"raw": 5_000, "gzip": 1_000}
    for metric, actual in actuals.items():
        current = int(category[metric])
        if actual * 100 >= current * 85:
            target = math.ceil((actual * 1.15) / increments[metric]) * increments[metric]
            category[metric] = max(current, target)
    pattern = re.compile(
        r'("name"\s*:\s*"bootstrap-data"[^\n]*?"raw"\s*:\s*)\d+'
        r'([^\n]*?"gzip"\s*:\s*)\d+'
    )
    replacement = rf"\g<1>{int(category['raw'])}\g<2>{int(category['gzip'])}"
    refreshed, count = pattern.subn(replacement, source, count=1)
    if count != 1:
        raise ValueError("Bootstrap-data budget entry must remain on one line.")
    return refreshed


def _run(command: list[str], *, root: Path) -> None:
    executable = shutil.which(command[0]) or command[0]
    result = subprocess.run([executable, *command[1:]], cwd=root, check=False)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(command)}")


def _write_with_backup(write: PlannedWrite, backups: dict[Path, bytes | None]) -> None:
    if write.path not in backups:
        backups[write.path] = write.path.read_bytes() if write.path.exists() else None
    write.path.parent.mkdir(parents=True, exist_ok=True)
    write.path.write_text(write.content, encoding="utf-8")


def _planned_catalog_writes(root: Path) -> tuple[PlannedWrite, ...]:
    metadata = discover_catalog_sources(root)
    return (
        PlannedWrite(root / _AGGREGATE_PATH, _render_aggregate(metadata)),
        PlannedWrite(
            root / _PALETTE_PATH,
            _render_palette_source((root / _PALETTE_PATH).read_text(encoding="utf-8"), metadata),
        ),
        PlannedWrite(
            root / _PREVIEW_PATH,
            _render_preview_source(
                (root / _PREVIEW_PATH).read_text(encoding="utf-8"),
                metadata,
            ),
        ),
    )


def regenerate_catalog(root: Path = ROOT_DIR) -> tuple[Path, ...]:
    writes = _planned_catalog_writes(root)
    backups: dict[Path, bytes | None] = {}
    bootstrap_path = root / _BOOTSTRAP_PATH
    budget_path = root / _BUDGET_PATH
    try:
        for write in writes:
            _write_with_backup(write, backups)
        for path in (bootstrap_path, budget_path):
            backups[path] = path.read_bytes() if path.exists() else None
        _run(
            [sys.executable, "-m", "tools", "bootstrap", "export", str(_BOOTSTRAP_PATH)],
            root=root,
        )
        budget_path.write_text(
            refresh_bootstrap_budget_source(
                budget_path.read_text(encoding="utf-8"), bootstrap_path.read_bytes()
            ),
            encoding="utf-8",
        )
        _run(
            ["npm", "exec", "prettier", "--", "--write", str(_PREVIEW_PATH)],
            root=root,
        )
        _run([sys.executable, "-m", "tools", "tilings", "validate"], root=root)
        _run([sys.executable, "-m", "tools", "tilings", "verify"], root=root)
    except Exception:
        for path, content in backups.items():
            if content is None:
                path.unlink(missing_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
        raise
    return tuple(write.path for write in writes) + (bootstrap_path, budget_path)


def check_catalog(root: Path = ROOT_DIR) -> tuple[str, ...]:
    problems: list[str] = []
    for write in _planned_catalog_writes(root):
        if not write.path.exists() or write.path.read_text(encoding="utf-8") != write.content:
            problems.append(f"generated catalog surface is stale: {write.path.relative_to(root)}")
    expected_budget = refresh_bootstrap_budget_source(
        (root / _BUDGET_PATH).read_text(encoding="utf-8"),
        (root / _BOOTSTRAP_PATH).read_bytes(),
    )
    if expected_budget != (root / _BUDGET_PATH).read_text(encoding="utf-8"):
        problems.append("standalone bootstrap budget lacks catalog headroom")
    return tuple(problems)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Deterministically rebuild all periodic catalog surfaces from metadata."
    )
    parser.add_argument("--check", action="store_true", help="Report drift without writing files.")
    parser.add_argument("--dry-run", action="store_true", help="List source metadata and exit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        metadata = discover_catalog_sources(ROOT_DIR)
        if args.dry_run:
            for item in _aggregate_payload(metadata):
                print(item["geometry"])
            return 0
        if args.check:
            problems = check_catalog(ROOT_DIR)
            if problems:
                for problem in problems:
                    print(f"FAIL: {problem}", file=sys.stderr)
                return 1
            print(f"Periodic catalog is current ({len(metadata)} tilings).")
            return 0
        written = regenerate_catalog(ROOT_DIR)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError, SyntaxError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"Regenerated periodic catalog for {len(metadata)} tilings across {len(written)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
