import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

try:
    from tools.smoke_test_standalone import (
        ConsoleEvent,
        SmokeResult,
        _BENIGN_CONSOLE_PATTERNS,
        _format_summary,
        _to_serializable,
        main,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.smoke_test_standalone import (
        ConsoleEvent,
        SmokeResult,
        _BENIGN_CONSOLE_PATTERNS,
        _format_summary,
        _to_serializable,
        main,
    )


class ConsoleEventClassificationTests(unittest.TestCase):
    def test_pageerror_is_always_treated_as_error(self) -> None:
        event = ConsoleEvent(kind="pageerror", text="ReferenceError: x is not defined")
        self.assertTrue(event.is_error)
        self.assertFalse(event.is_benign)

    def test_console_error_is_an_error(self) -> None:
        self.assertTrue(ConsoleEvent(kind="console:error", text="boom").is_error)

    def test_console_log_and_warn_are_not_errors(self) -> None:
        self.assertFalse(ConsoleEvent(kind="console:log", text="hi").is_error)
        self.assertFalse(ConsoleEvent(kind="console:warn", text="careful").is_error)

    def test_benign_pattern_suppresses_error_classification_in_summary(self) -> None:
        # The benign list must contain at least the asyncio notice; if this
        # changes, the smoke test may surface noisy messages.
        self.assertTrue(
            any(
                pattern.search("experimental asyncio support enabled in WebAssembly")
                for pattern in _BENIGN_CONSOLE_PATTERNS
            )
        )


class FormatSummaryTests(unittest.TestCase):
    def _result(self, **overrides: object) -> SmokeResult:
        defaults: dict[str, object] = {
            "success": True,
            "duration_ms": 1234,
            "base_url": "http://127.0.0.1:5000",
            "bootstrap_ms": 800,
            "events": [],
            "errors": [],
            "notes": [],
        }
        defaults.update(overrides)
        return SmokeResult(**defaults)  # type: ignore[arg-type]

    def test_summary_starts_with_pass_or_fail_marker(self) -> None:
        self.assertIn("[PASS]", _format_summary(self._result(success=True)))
        self.assertIn("[FAIL]", _format_summary(self._result(success=False)))

    def test_summary_lists_only_non_benign_error_events(self) -> None:
        events = [
            ConsoleEvent(kind="console:error", text="real failure"),
            ConsoleEvent(kind="console:error", text="experimental asyncio support"),
            ConsoleEvent(kind="console:log", text="status update"),
        ]
        rendered = _format_summary(self._result(events=events))
        self.assertIn("real failure", rendered)
        self.assertIn("Benign error events (1 suppressed)", rendered)
        # Logs are not errors and should not appear under "Error events".
        self.assertNotIn("status update", rendered)

    def test_summary_includes_setup_errors(self) -> None:
        rendered = _format_summary(self._result(success=False, errors=["host failed to start"]))
        self.assertIn("Setup errors:", rendered)
        self.assertIn("host failed to start", rendered)

    def test_summary_includes_notes(self) -> None:
        rendered = _format_summary(self._result(notes=["benign noise observed"]))
        self.assertIn("benign noise observed", rendered)


class SerializationTests(unittest.TestCase):
    def test_to_serializable_round_trips_through_json(self) -> None:
        result = SmokeResult(
            success=False,
            duration_ms=10,
            base_url="http://example",
            bootstrap_ms=5,
            events=[ConsoleEvent(kind="pageerror", text="boom")],
            errors=["something went wrong"],
            notes=["fyi"],
        )
        payload = _to_serializable(result)
        # Make sure the payload is JSON-serialisable end-to-end.
        rendered = json.dumps(payload)
        decoded = json.loads(rendered)
        self.assertEqual(decoded["events"][0]["kind"], "pageerror")
        self.assertEqual(decoded["errors"], ["something went wrong"])
        self.assertFalse(decoded["success"])


class MainEntrypointTests(unittest.TestCase):
    def _silence(self) -> io.StringIO:
        return io.StringIO()

    def test_main_returns_zero_on_success(self) -> None:
        ok_result = SmokeResult(
            success=True,
            duration_ms=10,
            base_url="http://x",
            bootstrap_ms=5,
        )
        buffer = self._silence()
        with (
            mock.patch("tools.smoke_test_standalone.run_smoke_test", return_value=ok_result),
            redirect_stdout(buffer),
        ):
            self.assertEqual(main([]), 0)

    def test_main_returns_one_on_failure(self) -> None:
        failed_result = SmokeResult(
            success=False,
            duration_ms=10,
            base_url="http://x",
            bootstrap_ms=5,
            errors=["boom"],
        )
        buffer = self._silence()
        with (
            mock.patch("tools.smoke_test_standalone.run_smoke_test", return_value=failed_result),
            redirect_stdout(buffer),
        ):
            self.assertEqual(main([]), 1)
        self.assertIn("boom", buffer.getvalue())

    def test_main_writes_output_file_when_requested(self) -> None:
        import tempfile

        ok_result = SmokeResult(success=True, duration_ms=10, base_url="http://x", bootstrap_ms=5)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "out" / "summary.txt"
            buffer = self._silence()
            with (
                mock.patch("tools.smoke_test_standalone.run_smoke_test", return_value=ok_result),
                redirect_stdout(buffer),
            ):
                rc = main(["--output", str(target)])
            self.assertEqual(rc, 0)
            self.assertTrue(target.exists())
            self.assertIn("[PASS]", target.read_text(encoding="utf-8"))

    def test_main_emits_json_when_requested(self) -> None:
        ok_result = SmokeResult(success=True, duration_ms=10, base_url="http://x", bootstrap_ms=5)
        buffer = self._silence()
        with (
            mock.patch("tools.smoke_test_standalone.run_smoke_test", return_value=ok_result),
            redirect_stdout(buffer),
        ):
            rc = main(["--format", "json"])
        self.assertEqual(rc, 0)
        decoded = json.loads(buffer.getvalue())
        self.assertTrue(decoded["success"])
        self.assertEqual(decoded["base_url"], "http://x")


if __name__ == "__main__":
    unittest.main()
