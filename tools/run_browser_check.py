"""CLI entrypoint for managed browser checks."""

from tools.render_review.browser_check import main

__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())
