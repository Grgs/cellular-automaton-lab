from __future__ import annotations

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


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1 or args[0] not in STYLE_COMMANDS:
        print(
            "Usage: python tools/run_python_style.py [check|format-check|format]", file=sys.stderr
        )
        return 2

    result = subprocess.run(
        [sys.executable, "-m", "ruff", *STYLE_COMMANDS[args[0]], *STYLE_TARGETS],
        cwd=ROOT_DIR,
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
