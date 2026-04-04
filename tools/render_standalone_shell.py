from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app_shell import render_standalone_document


def main() -> int:
    if len(sys.argv) > 2:
        raise SystemExit("Usage: py -3 tools/render_standalone_shell.py [output_path]")

    if len(sys.argv) == 2:
        output_path = Path(sys.argv[1])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_standalone_document(), encoding="utf-8")
    else:
        sys.stdout.write(render_standalone_document())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
