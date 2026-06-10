from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
STYLE_TARGETS = (
    "app.py",
    "backend",
    "tests",
    "tools",
)

STYLE_COMMANDS = {
    "check": ["check", "--config", "ruff.toml"],
    "format-check": ["format", "--check", "--config", "ruff.toml"],
    "format": ["format", "--config", "ruff.toml"],
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run repo-owned Ruff style commands against the Python source surface."
    )
    parser.add_argument("command", choices=tuple(STYLE_COMMANDS))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    namespace = build_parser().parse_args(args)

    result = subprocess.run(
        [sys.executable, "-m", "ruff", *STYLE_COMMANDS[str(namespace.command)], *STYLE_TARGETS],
        cwd=ROOT_DIR,
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
