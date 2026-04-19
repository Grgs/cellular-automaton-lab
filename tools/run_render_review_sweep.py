"""CLI entrypoint for render-review sweeps."""

from tools.render_review.sweep import main

__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())
