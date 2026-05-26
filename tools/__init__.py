"""Repo-owned developer tooling package."""

from __future__ import annotations

from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    from tools.cli import main as cli_main

    return cli_main(list(argv) if argv is not None else None)


__all__ = ("main",)
