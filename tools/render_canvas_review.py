"""CLI entrypoint for browser-backed canvas render review."""

from tools.render_review.review import main

__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())
