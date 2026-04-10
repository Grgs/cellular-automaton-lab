import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.report_tiling_verification_strength import main


class ReportTilingVerificationStrengthToolTests(unittest.TestCase):
    def test_main_prints_expected_strength_tags(self) -> None:
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            exit_code = main()

        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        self.assertIn("geometry\tsample_mode\timplementation_status\tstrength_tags", output)
        self.assertIn("pinwheel\tpatch_depth\texact_affine\t", output)
        self.assertIn("pinwheel\tpatch_depth\texact_affine\tsample-exact,metadata,local-reference,canonical-patch,exact-path,strict-validation", output)
        self.assertIn("archimedean-4-8-8\tgrid\t\tsample-exact,descriptor,vertex-stars,dual-checks,strict-validation", output)
        self.assertIn(
            "archimedean-3-4-6-4\tgrid\t\tsample-exact,descriptor,vertex-stars,dual-candidate-checks,strict-validation",
            output,
        )
        self.assertIn("chair\tpatch_depth\ttrue_substitution\tsample-exact,metadata,local-reference,strict-validation", output)
        self.assertIn("shield\tpatch_depth\tknown_deviation\t", output)


if __name__ == "__main__":
    unittest.main()
