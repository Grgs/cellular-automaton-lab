from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.export_dodecagonal_square_triangle_contract_generator import (
    DEFAULT_OUTPUT_DIR,
    build_generated_generator_source,
    build_generated_test_source,
    drift_lines,
    main,
)


class ExportDodecagonalSquareTriangleContractGeneratorToolTests(unittest.TestCase):
    def test_generated_sources_match_checked_in_files(self) -> None:
        self.assertEqual(drift_lines(DEFAULT_OUTPUT_DIR), [])

    def test_generated_generator_source_contains_backend_thresholds(self) -> None:
        source = build_generated_generator_source()

        self.assertIn("PATCH_DISTANCE_THRESHOLDS = {", source)
        self.assertIn("0: 4,", source)
        self.assertIn("4: 97,", source)
        self.assertIn("EDGE_PRECISION = 6", source)

    def test_generated_test_source_references_expected_patches(self) -> None:
        source = build_generated_test_source()

        self.assertIn('EXPECTED_PATCHES_DIR = BASE_DIR / "expected-patches"', source)
        self.assertIn("test_expected_patches_match_for_depths_zero_through_four", source)

    def test_main_check_passes_for_checked_in_files(self) -> None:
        self.assertEqual(main(["--check"]), 0)

    def test_main_writes_files_to_temp_directory(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dodecagonal-contract-generator-") as tmpdir:
            tmpdir_path = Path(tmpdir)

            self.assertEqual(main(["--output-dir", str(tmpdir_path)]), 0)
            self.assertTrue((tmpdir_path / "generator.py").exists())
            self.assertTrue((tmpdir_path / "test_generator.py").exists())
            self.assertEqual(drift_lines(tmpdir_path), [])


if __name__ == "__main__":
    unittest.main()
