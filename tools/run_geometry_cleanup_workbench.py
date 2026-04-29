"""CLI entrypoint for the geometry cleanup workbench."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.render_review.geometry_cleanup_workbench import main

__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())
