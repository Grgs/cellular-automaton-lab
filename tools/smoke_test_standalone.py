"""Smoke-test the standalone bundle: headless load, assert no startup errors, exit.

The standalone build has its own initialization path (Pyodide worker, bundled
bootstrap data) that the full Playwright suite covers, but only as part of an
expensive end-to-end run. This tool is a fast standalone-only gate that:

1. Spins up the same `StandaloneRuntimeHost` the e2e suite uses, serving
   `output/standalone/` over a local HTTP server.
2. Launches headless Chromium, navigates to the standalone URL, and waits for
   the readiness signal that says the bundled bootstrap has hydrated.
3. Captures every console message and page error and fails the run when any
   error-level event landed during startup (with a small allowlist for
   benign favicon-style noise).
4. Reports wall-clock startup time.

Examples:

    py -3 tools/smoke_test_standalone.py
    py -3 tools/smoke_test_standalone.py --timeout-seconds 60
    py -3 tools/smoke_test_standalone.py --output output/standalone-smoke.json
    py -3 tools/smoke_test_standalone.py --no-build-check
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Final

from playwright.sync_api import sync_playwright

# ``tools/`` is reachable without setup, but ``tests.e2e.support_runtime_host``
# is only on sys.path when the project root is. Make the import work whether
# the tool is invoked from the project root or via a fully-qualified path.
ROOT_DIR: Final[Path] = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tests.e2e.support_runtime_host import (  # noqa: E402
    StandaloneRuntimeHost,
    missing_standalone_output_files,
)
from tools.render_review.browser_support.render_review import (  # noqa: E402
    wait_for_page_bootstrapped,
)


# Console messages that match any of these patterns are treated as benign.
# Keep this list very short — the whole point of the smoke test is to catch
# unexpected startup noise. New entries should reference an issue or a clear
# justification in the commit message.
_BENIGN_CONSOLE_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    # Pyodide loader warnings about asyncio: it logs an "experimental" notice
    # under WebAssembly that is not actionable.
    re.compile(r"experimental asyncio support", re.IGNORECASE),
)


@dataclass
class ConsoleEvent:
    kind: str  # "console:<level>" or "pageerror"
    text: str

    @property
    def is_error(self) -> bool:
        if self.kind == "pageerror":
            return True
        if self.kind.startswith("console:"):
            level = self.kind.split(":", 1)[1]
            return level in {"error"}
        return False

    @property
    def is_benign(self) -> bool:
        return any(pattern.search(self.text) for pattern in _BENIGN_CONSOLE_PATTERNS)


@dataclass
class SmokeResult:
    success: bool
    duration_ms: int
    base_url: str
    bootstrap_ms: int
    events: list[ConsoleEvent] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _format_summary(result: SmokeResult) -> str:
    lines: list[str] = []
    status = "PASS" if result.success else "FAIL"
    lines.append(
        f"[{status}] standalone smoke test in {result.duration_ms} ms"
        f" (bootstrap {result.bootstrap_ms} ms) at {result.base_url}"
    )
    if result.notes:
        lines.append("")
        lines.append("Notes:")
        for note in result.notes:
            lines.append(f"  - {note}")
    error_events = [e for e in result.events if e.is_error and not e.is_benign]
    benign_errors = [e for e in result.events if e.is_error and e.is_benign]
    if error_events:
        lines.append("")
        lines.append("Error events:")
        for event in error_events:
            lines.append(f"  {event.kind}: {event.text}")
    if benign_errors:
        lines.append("")
        lines.append(f"Benign error events ({len(benign_errors)} suppressed):")
        for event in benign_errors:
            lines.append(f"  {event.kind}: {event.text}")
    if result.errors:
        lines.append("")
        lines.append("Setup errors:")
        for error in result.errors:
            lines.append(f"  {error}")
    return "\n".join(lines)


def _to_serializable(result: SmokeResult) -> dict[str, object]:
    payload = asdict(result)
    payload["events"] = [asdict(event) for event in result.events]
    return payload


def run_smoke_test(*, timeout_seconds: float, check_build: bool) -> SmokeResult:
    started_at = time.perf_counter()
    events: list[ConsoleEvent] = []
    notes: list[str] = []
    errors: list[str] = []
    bootstrap_ms = 0

    if check_build:
        missing = missing_standalone_output_files(ROOT_DIR / "output" / "standalone")
        if missing:
            return SmokeResult(
                success=False,
                duration_ms=int((time.perf_counter() - started_at) * 1000),
                base_url="",
                bootstrap_ms=0,
                errors=[
                    "standalone bundle is missing required outputs: "
                    + ", ".join(missing)
                    + " — build it first with `npm run build:frontend:standalone`."
                ],
            )

    host = StandaloneRuntimeHost()
    host.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                context = browser.new_context()
                try:
                    page = context.new_page()
                    page.set_default_timeout(int(timeout_seconds * 1000))
                    page.set_default_navigation_timeout(int(timeout_seconds * 1000))

                    page.on(
                        "console",
                        lambda message: events.append(
                            ConsoleEvent(kind=f"console:{message.type}", text=message.text)
                        ),
                    )
                    page.on(
                        "pageerror",
                        lambda error: events.append(
                            ConsoleEvent(kind="pageerror", text=str(error))
                        ),
                    )

                    bootstrap_started = time.perf_counter()
                    page.goto(host.base_url + "/", wait_until="load")
                    wait_for_page_bootstrapped(page, timeout_ms=int(timeout_seconds * 1000))
                    bootstrap_ms = int((time.perf_counter() - bootstrap_started) * 1000)
                finally:
                    context.close()
            finally:
                browser.close()
    except Exception as exc:
        errors.append(f"smoke test raised: {exc!r}")
    finally:
        host.close()

    duration_ms = int((time.perf_counter() - started_at) * 1000)

    error_events = [event for event in events if event.is_error and not event.is_benign]
    success = not errors and not error_events

    if not error_events and any(event.is_error and event.is_benign for event in events):
        notes.append("benign error events were observed but suppressed by the allowlist")

    return SmokeResult(
        success=success,
        duration_ms=duration_ms,
        base_url=host.base_url if not errors else "",
        bootstrap_ms=bootstrap_ms,
        events=events,
        errors=errors,
        notes=notes,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=45.0,
        help="per-step Playwright timeout (default: 45)",
    )
    parser.add_argument(
        "--no-build-check",
        action="store_true",
        help="skip the prebuild-output sanity check (StandaloneRuntimeHost will still verify)",
    )
    parser.add_argument(
        "--format",
        choices=("summary", "json"),
        default="summary",
        help="output format (default: summary)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="write the formatted output to this file as well as stdout",
    )
    args = parser.parse_args(argv)

    result = run_smoke_test(
        timeout_seconds=args.timeout_seconds,
        check_build=not args.no_build_check,
    )

    if args.format == "json":
        rendered = json.dumps(_to_serializable(result), indent=2, sort_keys=True)
    else:
        rendered = _format_summary(result)

    print(rendered)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")

    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
