from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path

from backend.app_shell import render_standalone_document
from backend.bootstrap_data import build_bootstrap_payload
from backend.dev_server import APP_NAME
from tools._common import (
    ROOT_DIR,
    collect_files,
    read_command_output,
    resolve_node_executable,
    run_command,
)
from tools.provenance import (
    compute_source_fingerprint as compute_source_fingerprint,
)
from tools.provenance import (
    git_dirty_status as git_dirty_status,
)
from tools.provenance import (
    iter_source_fingerprint_paths as iter_source_fingerprint_paths,
)

OUTPUT_DIR = ROOT_DIR / "output" / "standalone"
STANDALONE_BUILD_INPUT_DIR = ROOT_DIR / "output" / ".standalone-build-input"
STANDALONE_HTML_INPUT_PATH = STANDALONE_BUILD_INPUT_DIR / "standalone.html"


def build_parser(root: Path = ROOT_DIR) -> argparse.ArgumentParser:
    del root
    return argparse.ArgumentParser(
        prog="python -m tools build standalone",
        description="Build the standalone bundle into output/standalone/ and write a build manifest.",
    )


def export_bootstrap_data(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_bootstrap_payload({"app_name": APP_NAME})
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def prepare_standalone_build_input() -> Path:
    shutil.rmtree(STANDALONE_BUILD_INPUT_DIR, ignore_errors=True)
    STANDALONE_BUILD_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    STANDALONE_HTML_INPUT_PATH.write_text(render_standalone_document(), encoding="utf-8")
    shutil.copy2(
        ROOT_DIR / "static" / "css" / "styles.css", STANDALONE_BUILD_INPUT_DIR / "styles.css"
    )
    shutil.copy2(ROOT_DIR / "static" / "favicon.svg", STANDALONE_BUILD_INPUT_DIR / "favicon.svg")
    return STANDALONE_HTML_INPUT_PATH


def build_standalone_frontend(html_entry_path: Path) -> None:
    node_executable = resolve_node_executable()
    vite_path = ROOT_DIR / "node_modules" / "vite" / "bin" / "vite.js"
    env = dict(os.environ, STANDALONE_HTML_ENTRY=str(html_entry_path))
    result = run_command(
        [node_executable, str(vite_path), "build", "--mode", "standalone"],
        env=env,
    )
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def copy_static_assets() -> None:
    nested_standalone_html_path = (
        OUTPUT_DIR / "output" / ".standalone-build-input" / "standalone.html"
    )
    index_html_path = OUTPUT_DIR / "index.html"
    standalone_html_path = OUTPUT_DIR / "standalone.html"
    if standalone_html_path.exists():
        standalone_html_path.unlink()
    if nested_standalone_html_path.exists():
        normalized_html = nested_standalone_html_path.read_text(encoding="utf-8").replace(
            "../../assets/",
            "./assets/",
        )
        index_html_path.write_text(normalized_html, encoding="utf-8")
        shutil.rmtree(OUTPUT_DIR / "output", ignore_errors=True)
    (OUTPUT_DIR / ".nojekyll").write_text("", encoding="utf-8")


def write_python_bundle() -> None:
    source_roots = (ROOT_DIR / "backend", ROOT_DIR / "config")
    files = sorted(
        file_path
        for source_root in source_roots
        for file_path in collect_files(
            source_root,
            lambda absolute_path: absolute_path.suffix in {".py", ".json"},
        )
    )
    bundle_entries = [
        {
            "target_path": f"/app/{absolute_path.relative_to(ROOT_DIR).as_posix()}",
            "contents": absolute_path.read_text(encoding="utf-8"),
        }
        for absolute_path in files
    ]
    shutil.rmtree(OUTPUT_DIR / "py-src", ignore_errors=True)
    (OUTPUT_DIR / "standalone-python-bundle.json").write_text(
        json.dumps({"version": 1, "files": bundle_entries}),
        encoding="utf-8",
    )


def write_build_manifest() -> None:
    source_files = iter_source_fingerprint_paths(ROOT_DIR)
    manifest = {
        "builtAt": datetime.now(tz=UTC).isoformat(),
        "gitHead": read_command_output(["git", "rev-parse", "HEAD"]),
        "gitDirty": git_dirty_status(ROOT_DIR),
        "sourceFingerprint": compute_source_fingerprint(ROOT_DIR, source_files),
        "sourceFiles": list(source_files),
    }
    (OUTPUT_DIR / "build-manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )


def build_standalone() -> int:
    standalone_html_entry = prepare_standalone_build_input()
    try:
        build_standalone_frontend(standalone_html_entry)
        copy_static_assets()
        export_bootstrap_data(OUTPUT_DIR / "standalone-bootstrap.json")
        write_python_bundle()
        write_build_manifest()
    finally:
        shutil.rmtree(STANDALONE_BUILD_INPUT_DIR, ignore_errors=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser(ROOT_DIR)
    parser.parse_args(argv)
    return build_standalone()
