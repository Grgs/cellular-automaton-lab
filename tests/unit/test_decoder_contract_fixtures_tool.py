from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

try:
    from tools.regenerate_decoder_contract_fixtures import (
        DEFAULT_FIXTURE_PATH,
        FIXED_STATE_EPOCH,
        build_fixture_document,
        fixture_drift_detail,
        main,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.regenerate_decoder_contract_fixtures import (
        DEFAULT_FIXTURE_PATH,
        FIXED_STATE_EPOCH,
        build_fixture_document,
        fixture_drift_detail,
        main,
    )


class DecoderContractFixtureToolTests(unittest.TestCase):
    def test_checked_in_fixture_matches_regenerated_runtime_responses(self) -> None:
        # The frontend contract test consumes this file verbatim, so any
        # backend payload change must regenerate it. Byte drift means someone
        # changed a payload without running `python -m tools fixtures
        # decoder-contract`.
        self.assertIsNone(fixture_drift_detail())

    def test_document_pins_state_epochs_and_covers_delta_payloads(self) -> None:
        document = build_fixture_document()
        responses = document["responses"]

        delta = responses["http-cell-delta"]["response"]
        self.assertEqual(delta["state_epoch"], FIXED_STATE_EPOCH)
        self.assertNotIn("ok", delta)
        self.assertEqual(
            {key for key, value in responses["cells-set-many"]["response"].items() if key != "ok"},
            set(delta),
        )

        snapshot = responses["state"]["response"]["snapshot"]
        self.assertEqual(snapshot["state_epoch"], FIXED_STATE_EPOCH)

        decoders = {entry["decoder"] for entry in responses.values()}
        self.assertEqual(decoders, {"init", "request", "tick", "delta"})

    def test_check_mode_flags_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            stale_path = Path(tmp) / "worker-responses.json"
            stale_payload = json.loads(DEFAULT_FIXTURE_PATH.read_text(encoding="utf-8"))
            stale_payload["responses"].pop("rules")
            stale_path.write_text(json.dumps(stale_payload), encoding="utf-8")

            self.assertEqual(main(["--check", "--path", str(stale_path)]), 1)
            self.assertEqual(main(["--path", str(stale_path)]), 0)
            self.assertEqual(main(["--check", "--path", str(stale_path)]), 0)


if __name__ == "__main__":
    unittest.main()
