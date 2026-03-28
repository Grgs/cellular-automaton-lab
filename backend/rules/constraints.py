from __future__ import annotations

from typing import Any


def rule_requires_square_dimensions(rule_or_name: Any) -> bool:
    _ = rule_or_name
    return False


def normalize_rule_dimensions(
    rule_or_name: Any,
    width: int | None,
    height: int | None,
) -> tuple[int | None, int | None]:
    _ = rule_or_name
    return width, height
