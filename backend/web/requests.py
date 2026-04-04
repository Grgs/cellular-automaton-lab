from __future__ import annotations

from flask import Request

from backend.contract_validation import (
    ContractValidationError,
    parse_cell_id,
    parse_cell_target,
    parse_cell_updates,
    parse_optional_float,
    parse_optional_int,
    parse_required_int,
    parse_rule_name,
    parse_state_value,
    parse_topology_spec,
)
from backend.payload_types import RawJsonObject


RequestValidationError = ContractValidationError
__all__ = [
    "RequestValidationError",
    "get_payload",
    "parse_cell_id",
    "parse_cell_target",
    "parse_cell_updates",
    "parse_optional_float",
    "parse_optional_int",
    "parse_required_int",
    "parse_rule_name",
    "parse_state_value",
    "parse_topology_spec",
]


def get_payload(request: Request) -> RawJsonObject:
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else {}
