"""CLI entrypoint for the family sample workbench."""

from tools.render_review.family_sample_workbench import main

__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())
