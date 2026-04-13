import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.validate_tilings import iter_validation_targets, main, validate_manifest_tilings


class ValidateTilingsToolTests(unittest.TestCase):
    def test_iter_validation_targets_covers_mixed_and_penrose_geometries(self) -> None:
        targets = dict(iter_validation_targets())

        self.assertIn("archimedean-4-8-8", targets)
        self.assertIn("trihexagonal-3-6-3-6", targets)
        self.assertIn("rhombille", targets)
        self.assertIn("floret-pentagonal", targets)
        self.assertIn("deltoidal-hexagonal", targets)
        self.assertIn("spectre", targets)
        self.assertIn("taylor-socolar", targets)
        self.assertIn("chair", targets)
        self.assertIn("robinson-triangles", targets)
        self.assertIn("hat-monotile", targets)
        self.assertIn("tuebingen-triangle", targets)
        self.assertIn("dodecagonal-square-triangle", targets)
        self.assertIn("shield", targets)
        self.assertIn("pinwheel", targets)
        self.assertIn("penrose-p3-rhombs", targets)
        self.assertIn("penrose-p3-rhombs-vertex", targets)
        self.assertEqual(targets["archimedean-4-8-8"]["width"], 3)
        self.assertEqual(targets["penrose-p3-rhombs"]["patch_depth"], 3)
        self.assertEqual(targets["spectre"]["patch_depth"], 3)
        self.assertEqual(targets["taylor-socolar"]["patch_depth"], 3)
        self.assertEqual(targets["chair"]["patch_depth"], 3)
        self.assertEqual(targets["robinson-triangles"]["patch_depth"], 3)
        self.assertEqual(targets["hat-monotile"]["patch_depth"], 3)
        self.assertEqual(targets["tuebingen-triangle"]["patch_depth"], 3)
        self.assertEqual(targets["dodecagonal-square-triangle"]["patch_depth"], 3)
        self.assertEqual(targets["shield"]["patch_depth"], 3)
        self.assertEqual(targets["pinwheel"]["patch_depth"], 3)

    def test_validate_manifest_tilings_returns_valid_results(self) -> None:
        results = validate_manifest_tilings()

        self.assertTrue(results)
        self.assertTrue(all(result.is_valid for _, result in results))

    def test_main_returns_success_when_all_target_validations_pass(self) -> None:
        self.assertEqual(main(), 0)


if __name__ == "__main__":
    unittest.main()
