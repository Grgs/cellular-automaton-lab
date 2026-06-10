from __future__ import annotations

import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Final

ROOT_DIR: Final[Path] = Path(__file__).resolve().parents[1]


def resolve_node_executable() -> str:
    return shutil.which("node") or shutil.which("node.exe") or "node"


def resolve_npm_executable() -> str:
    if sys.platform == "win32":
        return shutil.which("npm.cmd") or shutil.which("npm") or "npm.cmd"
    return shutil.which("npm") or "npm"


def run_command(
    command: list[str],
    *,
    cwd: Path = ROOT_DIR,
    env: dict[str, str] | None = None,
    capture_output: bool = False,
    text: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        capture_output=capture_output,
        text=text,
    )


def read_command_output(command: list[str], *, cwd: Path = ROOT_DIR) -> str | None:
    result = run_command(command, cwd=cwd, capture_output=True)
    if result.returncode != 0:
        return None
    stdout = (result.stdout or "").strip()
    return stdout or None


def collect_files(
    directory: Path,
    predicate: Callable[[Path], bool],
) -> list[Path]:
    bucket: list[Path] = []
    for absolute_path in sorted(directory.rglob("*")):
        if absolute_path.is_file() and predicate(absolute_path):
            bucket.append(absolute_path)
    return bucket
