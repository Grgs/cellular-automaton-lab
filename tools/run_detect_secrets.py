from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

CHUNK_SIZE = 200


def _tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        capture_output=True,
        text=False,
    )
    return [entry.decode("utf-8") for entry in result.stdout.split(b"\x00") if entry]


def _chunked(items: list[str], size: int) -> list[list[str]]:
    return [items[index:index + size] for index in range(0, len(items), size)]


def _resolve_detect_secrets_hook() -> str:
    executable = shutil.which("detect-secrets-hook")
    if executable is None:
        raise RuntimeError("detect-secrets-hook is not available. Install detect-secrets or run through pre-commit.")
    return executable


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run detect-secrets against changed or tracked files.")
    parser.add_argument("--baseline", required=True, help="Path to the detect-secrets baseline file.")
    parser.add_argument("--all-files", action="store_true", help="Scan all tracked files.")
    parser.add_argument("paths", nargs="*", help="File paths supplied by pre-commit.")
    args = parser.parse_args(argv)

    baseline = Path(args.baseline)
    if not baseline.exists():
        print(
            f"Missing detect-secrets baseline: {baseline}. Run 'detect-secrets scan > {baseline.name}' to create it.",
            file=sys.stderr,
        )
        return 1

    files = _tracked_files() if args.all_files or not args.paths else args.paths
    files = [path for path in files if path != baseline.as_posix() and path != str(baseline)]
    if not files:
        return 0

    executable = _resolve_detect_secrets_hook()
    exit_code = 0
    for chunk in _chunked(files, CHUNK_SIZE):
        result = subprocess.run([executable, "--baseline", str(baseline), *chunk], check=False)
        if result.returncode != 0:
            exit_code = result.returncode
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
