import re
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.payload_contracts import payload_field_contracts, payload_type_union_contracts


_INTERFACE_PATTERN = re.compile(
    r"export interface (?P<name>[A-Za-z0-9_]+)(?: extends (?P<extends>[^{]+))? \{(?P<body>.*?)\n\}",
    re.DOTALL,
)
_FIELD_PATTERN = re.compile(r"^\s*(?P<name>[A-Za-z0-9_]+)\??:", re.MULTILINE)
_PROPERTY_TYPE_PATTERN = re.compile(r"^\s*(?P<name>[A-Za-z0-9_]+)\??:\s*(?P<type>[^;]+);", re.MULTILINE)
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


def _split_union_members(type_body: str) -> set[str]:
    return {
        member.strip()
        for member in re.sub(r"\s+", " ", type_body).split("|")
        if member.strip()
    }


def _parse_frontend_interfaces(relative_paths: list[str]) -> dict[str, _FrontendInterfaceDefinition]:
    definitions: dict[str, _FrontendInterfaceDefinition] = {}
    for relative_path in relative_paths:
        for match in _INTERFACE_PATTERN.finditer(_load_text(relative_path)):
            body = match.group("body")
            raw_extends = match.group("extends")
            extends = tuple(
                parent.strip()
                for parent in (raw_extends or "").split(",")
                if parent.strip()
            )
            property_types = {
                property_match.group("name"): property_match.group("type").strip()
                for property_match in _PROPERTY_TYPE_PATTERN.finditer(body)
            }
            definitions[match.group("name")] = _FrontendInterfaceDefinition(
                fields=set(_FIELD_PATTERN.findall(body)),
                extends=extends,
                property_types=property_types,
            )
    return definitions


def _resolve_interface_fields(
    definitions: dict[str, _FrontendInterfaceDefinition],
    interface_name: str,
) -> set[str]:
    try:
        definition = definitions[interface_name]
    except KeyError as error:
        raise AssertionError(f"Missing frontend interface {interface_name!r}.") from error

    resolved = set(definition.fields)
    for parent in definition.extends:
        resolved.update(_resolve_interface_fields(definitions, parent))
    return resolved


def _parse_type_aliases(relative_path: str) -> dict[str, str]:
    return {
        match.group("name"): re.sub(r"\s+", " ", match.group("body")).strip()
        for match in _TYPE_ALIAS_PATTERN.finditer(_load_text(relative_path))
    }


class PayloadContractTests(unittest.TestCase):
    def test_frontend_types_cover_backend_payload_fields(self) -> None:
        frontend_paths = sorted({contract.frontend_path for contract in payload_field_contracts()})
        frontend_interfaces = _parse_frontend_interfaces(frontend_paths)
        interfaces_by_path = {
            path: _parse_frontend_interfaces([path])
            for path in frontend_paths
        }

        for contract in payload_field_contracts():
            with self.subTest(interface=contract.interface_name):
                self.assertIn(contract.interface_name, interfaces_by_path[contract.frontend_path])
                self.assertEqual(
                    _resolve_interface_fields(frontend_interfaces, contract.interface_name),
                    set(contract.all_fields),
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
