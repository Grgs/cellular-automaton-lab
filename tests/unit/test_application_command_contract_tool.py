from __future__ import annotations

import unittest
from dataclasses import replace

from backend.application_commands.contracts import COMMAND_SPECS
from tools.application_command_contract import (
    contract_is_current,
    render_application_command_contract,
)


class ApplicationCommandContractToolTests(unittest.TestCase):
    def test_checked_in_contract_matches_the_python_registry(self) -> None:
        self.assertTrue(
            contract_is_current(),
            "Regenerate with `python -m tools repo command-contract --write`.",
        )

    def test_rendered_contract_includes_semantic_and_transport_maps(self) -> None:
        rendered = render_application_command_contract()

        for spec in COMMAND_SPECS:
            with self.subTest(command=spec.command.value):
                self.assertIn(f'"{spec.command.value}": CommandContract<', rendered)
                self.assertIn(
                    f'"{spec.transport_path}": ApplicationCommandMap["{spec.command.value}"]',
                    rendered,
                )

    def test_rendering_rejects_unmapped_frontend_types(self) -> None:
        invalid_spec = replace(COMMAND_SPECS[0], frontend_result="UnmappedResult")

        with self.assertRaisesRegex(ValueError, "UnmappedResult"):
            render_application_command_contract((invalid_spec,))


if __name__ == "__main__":
    unittest.main()
