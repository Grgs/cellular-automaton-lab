"""CLI entrypoint for the geometry cleanup workbench."""

from tools.render_review.geometry_cleanup_workbench import main

__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())
