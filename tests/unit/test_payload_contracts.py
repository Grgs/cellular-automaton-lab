import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.payload_contracts import payload_field_contracts


_INTERFACE_PATTERN = re.compile(
    r"export interface (?P<name>[A-Za-z0-9_]+)(?: extends [^{]+)? \{(?P<body>.*?)\n\}",
    re.DOTALL,
)
_FIELD_PATTERN = re.compile(r"^\s*(?P<name>[A-Za-z0-9_]+)\??:", re.MULTILINE)


def _frontend_interface_fields() -> dict[str, set[str]]:
    domain_types = (ROOT / "frontend" / "types" / "domain.d.ts").read_text(encoding="utf-8")
    return {
        match.group("name"): set(_FIELD_PATTERN.findall(match.group("body")))
        for match in _INTERFACE_PATTERN.finditer(domain_types)
    }


class PayloadContractTests(unittest.TestCase):
    def test_frontend_domain_types_cover_backend_payload_fields(self) -> None:
        frontend_interfaces = _frontend_interface_fields()

        for contract in payload_field_contracts():
            with self.subTest(interface=contract.interface_name):
                self.assertIn(contract.interface_name, frontend_interfaces)
                self.assertEqual(
                    frontend_interfaces[contract.interface_name],
                    set(contract.all_fields),
                )


if __name__ == "__main__":
    unittest.main()
