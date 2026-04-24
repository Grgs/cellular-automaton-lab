from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.regenerate_dodecagonal_literature_source import (
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SOURCE_PDF,
    main,
    payload_has_drift,
    regenerate_literature_source_payload,
    write_literature_source,
)


class RegenerateDodecagonalLiteratureSourceToolTests(unittest.TestCase):
    def test_regenerated_payload_matches_checked_in_backend_source(self) -> None:
        regenerated = regenerate_literature_source_payload()
        current = json.loads(DEFAULT_OUTPUT_PATH.read_text(encoding="utf-8"))

        self.assertEqual(regenerated, current)

    def test_main_check_passes_for_checked_in_backend_source(self) -> None:
        self.assertEqual(main(["--check"]), 0)

    def test_write_and_check_work_against_temp_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dodecagonal-literature-source-") as tmpdir:
            output_path = Path(tmpdir) / "dodecagonal_square_triangle_literature_source.json"
            output_path.write_text('{"seed_index": -1, "cells": []}\n', encoding="utf-8")

            self.assertTrue(payload_has_drift(output_path, source_pdf=DEFAULT_SOURCE_PDF))
            self.assertEqual(
                main(["--output", str(output_path), "--check"]),
                1,
            )

            write_literature_source(output_path, source_pdf=DEFAULT_SOURCE_PDF)
            self.assertFalse(payload_has_drift(output_path, source_pdf=DEFAULT_SOURCE_PDF))
            self.assertEqual(
                main(["--output", str(output_path), "--check"]),
                0,
            )


if __name__ == "__main__":
    unittest.main()
