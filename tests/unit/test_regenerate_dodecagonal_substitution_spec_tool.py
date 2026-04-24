from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.regenerate_dodecagonal_substitution_spec import (
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SOURCE_IMAGE,
    main,
    payload_has_drift,
    regenerate_substitution_spec_payload,
    write_substitution_spec,
)


class RegenerateDodecagonalSubstitutionSpecToolTests(unittest.TestCase):
    def test_regenerated_payload_matches_checked_in_backend_spec(self) -> None:
        regenerated = regenerate_substitution_spec_payload()
        current = json.loads(DEFAULT_OUTPUT_PATH.read_text(encoding="utf-8"))

        self.assertEqual(regenerated, current)

    def test_main_check_passes_for_checked_in_backend_spec(self) -> None:
        self.assertEqual(main(["--check"]), 0)

    def test_write_and_check_work_against_temp_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dodecagonal-substitution-spec-") as tmpdir:
            output_path = Path(tmpdir) / "dodecagonal_square_triangle_substitution_spec.json"
            output_path.write_text('{"rules": {}}\n', encoding="utf-8")

            self.assertTrue(payload_has_drift(output_path, source_image=DEFAULT_SOURCE_IMAGE))
            self.assertEqual(
                main(["--output", str(output_path), "--check"]),
                1,
            )

            write_substitution_spec(output_path, source_image=DEFAULT_SOURCE_IMAGE)
            self.assertFalse(payload_has_drift(output_path, source_image=DEFAULT_SOURCE_IMAGE))
            self.assertEqual(
                main(["--output", str(output_path), "--check"]),
                0,
            )


if __name__ == "__main__":
    unittest.main()
