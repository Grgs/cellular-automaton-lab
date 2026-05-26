from __future__ import annotations

import hashlib
from pathlib import Path

from tools._common import ROOT_DIR, collect_files, run_command


SOURCE_FINGERPRINT_DIRS = ("frontend",)
SOURCE_FINGERPRINT_FILES = (
    "config/defaults.json",
    "tools/standalone_build.py",
    "package.json",
    "package-lock.json",
)


def read_git_output(root: Path, *args: str) -> str | None:
    try:
        result = run_command(["git", *args], cwd=root, capture_output=True)
    except Exception:
        return None
    if result.returncode != 0:
        return None
    return (result.stdout or "").strip()


def read_git_status_porcelain(root: Path = ROOT_DIR) -> str | None:
    return read_git_output(root, "status", "--porcelain")


def git_dirty_status(root: Path = ROOT_DIR) -> bool | None:
    status = read_git_status_porcelain(root)
    if status is None:
        return None
    return bool(status)


def iter_source_fingerprint_paths(root: Path = ROOT_DIR) -> tuple[str, ...]:
    relative_paths: list[str] = []
    for relative_dir in SOURCE_FINGERPRINT_DIRS:
        absolute_dir = root / relative_dir
        if not absolute_dir.exists():
            continue
        for absolute_path in collect_files(absolute_dir, lambda _: True):
            relative_paths.append(absolute_path.relative_to(root).as_posix())
    for relative_file in SOURCE_FINGERPRINT_FILES:
        absolute_file = root / relative_file
        if absolute_file.exists():
            relative_paths.append(absolute_file.relative_to(root).as_posix())
    return tuple(sorted(dict.fromkeys(relative_paths)))


def compute_source_fingerprint(
    root: Path = ROOT_DIR,
    relative_paths: tuple[str, ...] | None = None,
) -> str:
    hash_object = hashlib.sha256()
    paths = relative_paths if relative_paths is not None else iter_source_fingerprint_paths(root)
    for relative_path in paths:
        absolute_path = root / relative_path
        hash_object.update(relative_path.encode("utf-8"))
        hash_object.update(b"\0")
        hash_object.update(absolute_path.read_bytes())
        hash_object.update(b"\0")
    return hash_object.hexdigest()
