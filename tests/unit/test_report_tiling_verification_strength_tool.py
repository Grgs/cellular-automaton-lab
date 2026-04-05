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
        self.assertIn("geometry\tsample_mode\tstrength_tags", output)
        self.assertIn("pinwheel\tpatch_depth\t", output)
        self.assertIn("pinwheel\tpatch_depth\tsample-exact,metadata,local-reference,canonical-patch,exact-path,strict-validation", output)
        self.assertIn("archimedean-4-8-8\tgrid\tsample-exact,descriptor,vertex-stars,dual-checks,strict-validation", output)
        self.assertIn(
            "archimedean-3-4-6-4\tgrid\tsample-exact,descriptor,vertex-stars,dual-candidate-checks,strict-validation",
            output,
        )
        self.assertIn("chair\tpatch_depth\tsample-exact,metadata,local-reference,strict-validation", output)


if __name__ == "__main__":
    unittest.main()
