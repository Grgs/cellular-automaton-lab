import re
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.payload_contracts import (
    frontend_property_type_contracts,
    frontend_type_alias_contracts,
    payload_field_contracts,
    payload_type_union_contracts,
)


_INTERFACE_HEADER_PATTERN = re.compile(
    r"export interface (?P<name>[A-Za-z0-9_]+)(?: extends (?P<extends>[^{]+))? \{"
)
_FIELD_PATTERN = re.compile(r"^\s*(?P<name>[A-Za-z0-9_]+)\??:", re.MULTILINE)
_PROPERTY_TYPE_PATTERN = re.compile(
    r"^\s*(?P<name>[A-Za-z0-9_]+)\??:\s*(?P<type>[^;]+);", re.MULTILINE
)
_TYPE_ALIAS_PATTERN = re.compile(
    r"export type (?P<name>[A-Za-z0-9_]+)\s*=\s*(?P<body>.*?);",
    re.DOTALL,
)


@dataclass(frozen=True)
class _FrontendInterfaceDefinition:
    fields: set[str]
    extends: tuple[str, ...]
    property_types: dict[str, str]


def _load_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _normalize_ts_type(type_text: str) -> str:
    return re.sub(r"\s+", " ", type_text).strip()


def _split_union_members(type_body: str) -> set[str]:
    return {member.strip() for member in _normalize_ts_type(type_body).split("|") if member.strip()}


def _parse_frontend_interfaces(
    relative_paths: list[str],
) -> dict[str, _FrontendInterfaceDefinition]:
    definitions: dict[str, _FrontendInterfaceDefinition] = {}
    for relative_path in relative_paths:
        text = _load_text(relative_path)
        cursor = 0
        while True:
            match = _INTERFACE_HEADER_PATTERN.search(text, cursor)
            if match is None:
                break
            body_start = match.end()
            depth = 1
            index = body_start
            while index < len(text) and depth > 0:
                char = text[index]
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                index += 1
            body = text[body_start : index - 1]
            raw_extends = match.group("extends")
            extends = tuple(
                parent.strip() for parent in (raw_extends or "").split(",") if parent.strip()
            )
            property_types = {
                property_match.group("name"): _normalize_ts_type(property_match.group("type"))
                for property_match in _PROPERTY_TYPE_PATTERN.finditer(body)
            }
            definitions[match.group("name")] = _FrontendInterfaceDefinition(
                fields=set(_FIELD_PATTERN.findall(body)),
                extends=extends,
                property_types=property_types,
            )
            cursor = index
    return definitions


def _resolve_interface_fields(
    definitions: dict[str, _FrontendInterfaceDefinition],
    type_aliases: dict[str, str],
    interface_name: str,
) -> set[str]:
    definition = definitions.get(interface_name)
    if definition is None:
        aliased_type = type_aliases.get(interface_name)
        if aliased_type is not None:
            return _resolve_interface_fields(definitions, type_aliases, aliased_type)
        raise AssertionError(f"Missing frontend interface or type alias {interface_name!r}.")

    resolved = set(definition.fields)
    for parent in definition.extends:
        resolved.update(_resolve_interface_fields(definitions, type_aliases, parent))
    return resolved


def _resolve_interface_property_types(
    definitions: dict[str, _FrontendInterfaceDefinition],
    interface_name: str,
) -> dict[str, str]:
    try:
        definition = definitions[interface_name]
    except KeyError as error:
        raise AssertionError(f"Missing frontend interface {interface_name!r}.") from error

    resolved: dict[str, str] = {}
    for parent in definition.extends:
        resolved.update(_resolve_interface_property_types(definitions, parent))
    resolved.update(definition.property_types)
    return resolved


def _parse_type_aliases(relative_path: str) -> dict[str, str]:
    return {
        match.group("name"): _normalize_ts_type(match.group("body"))
        for match in _TYPE_ALIAS_PATTERN.finditer(_load_text(relative_path))
    }


class PayloadContractTests(unittest.TestCase):
    def test_frontend_types_cover_backend_payload_fields(self) -> None:
        frontend_paths = sorted({contract.frontend_path for contract in payload_field_contracts()})
        frontend_interfaces = _parse_frontend_interfaces(frontend_paths)
        frontend_type_aliases = {
            type_name: type_body
            for path in frontend_paths
            for type_name, type_body in _parse_type_aliases(path).items()
        }
        interfaces_by_path = {path: _parse_frontend_interfaces([path]) for path in frontend_paths}
        type_aliases_by_path = {path: _parse_type_aliases(path) for path in frontend_paths}

        for contract in payload_field_contracts():
            with self.subTest(interface=contract.interface_name):
                self.assertTrue(
                    contract.interface_name in interfaces_by_path[contract.frontend_path]
                    or contract.interface_name in type_aliases_by_path[contract.frontend_path]
                )
                self.assertEqual(
                    _resolve_interface_fields(
                        frontend_interfaces,
                        frontend_type_aliases,
                        contract.interface_name,
                    ),
                    set(contract.all_fields),
                )

    def test_frontend_property_types_match_canonical_contracts(self) -> None:
        frontend_paths = sorted(
            {contract.frontend_path for contract in frontend_property_type_contracts()}
        )
        frontend_interfaces = _parse_frontend_interfaces(frontend_paths)

        for contract in frontend_property_type_contracts():
            with self.subTest(interface=contract.interface_name, property=contract.property_name):
                property_types = _resolve_interface_property_types(
                    frontend_interfaces, contract.interface_name
                )
                self.assertEqual(
                    property_types.get(contract.property_name),
                    _normalize_ts_type(contract.property_type),
                )

    def test_frontend_type_aliases_match_canonical_contracts(self) -> None:
        frontend_paths = sorted(
            {contract.frontend_path for contract in frontend_type_alias_contracts()}
        )
        type_aliases_by_path = {path: _parse_type_aliases(path) for path in frontend_paths}

        for contract in frontend_type_alias_contracts():
            with self.subTest(type_name=contract.type_name):
                self.assertEqual(
                    type_aliases_by_path[contract.frontend_path].get(contract.type_name),
                    _normalize_ts_type(contract.type_body),
                )

    def test_frontend_worker_request_payload_union_matches_backend_contract(self) -> None:
        for contract in payload_type_union_contracts():
            with self.subTest(type_name=contract.type_name):
                interfaces = _parse_frontend_interfaces([contract.frontend_path])
                type_aliases = _parse_type_aliases(contract.frontend_path)

                self.assertIn(contract.type_name, type_aliases)
                self.assertEqual(
                    _split_union_members(type_aliases[contract.type_name]),
                    set(contract.members),
                )
                if contract.host_interface_name is None or contract.host_property_name is None:
                    continue
                self.assertIn(contract.host_interface_name, interfaces)
                self.assertEqual(
                    interfaces[contract.host_interface_name].property_types.get(
                        contract.host_property_name
                    ),
                    contract.type_name,
                )


if __name__ == "__main__":
    unittest.main()
