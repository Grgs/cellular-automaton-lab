from __future__ import annotations

import _thread
import json
import tempfile
import threading
import time
import unittest
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, ClassVar, Literal

from playwright.sync_api import (
    Browser,
    BrowserContext,
    ConsoleMessage,
    Error as PlaywrightError,
    Page,
    Playwright,
    Response,
    TimeoutError as PlaywrightTimeoutError,
    ViewportSize,
    sync_playwright,
)

from tests.e2e.support_server import AppServer, JsonApiClient

WaitUntilState = Literal["commit", "domcontentloaded", "load", "networkidle"]


class BrowserAppTestCase(unittest.TestCase):
    page_viewport: ClassVar[ViewportSize | None] = None
    startup_timeout_seconds: ClassVar[float] = 45.0
    server: ClassVar[AppServer]
    api: ClassVar[JsonApiClient]
    playwright: ClassVar[Playwright]
    browser: ClassVar[Browser]
    context: BrowserContext
    page: Page

    @classmethod
    @contextmanager
    def _startup_watchdog(cls, description: str, timeout_seconds: float | None = None):
        deadline_seconds = timeout_seconds or cls.startup_timeout_seconds
        timer = threading.Timer(deadline_seconds, _thread.interrupt_main)
        timer.daemon = True
        timer.start()
        try:
            yield
        except KeyboardInterrupt as exc:
            raise AssertionError(
                f"{description} did not start within {deadline_seconds:.0f}s."
            ) from exc
        finally:
            timer.cancel()

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.server = AppServer()
        with cls._startup_watchdog("Browser test server"):
            cls.server.start()
        cls.api = cls.server.client
        with cls._startup_watchdog("Playwright runtime"):
            cls.playwright = sync_playwright().start()
        with cls._startup_watchdog("Chromium browser"):
            cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close()
        cls.playwright.stop()
        cls.server.close()
        super().tearDownClass()

    def setUp(self) -> None:
        super().setUp()
        with self._startup_watchdog("Browser test page context"):
            if self.page_viewport is None:
                self.context = self.browser.new_context(accept_downloads=True)
            else:
                self.context = self.browser.new_context(
                    accept_downloads=True,
                    viewport=self.page_viewport,
                )
            self.page = self.context.new_page()
        self.page.set_default_timeout(20_000)
        self.page.set_default_navigation_timeout(20_000)
        self.console_messages: list[str] = []
        self.page.on("console", self._record_console_message)
        self.page.on("pageerror", self._record_page_error)

    def tearDown(self) -> None:
        if self._current_test_failed():
            artifact_dir = self._capture_failure_artifacts()
            if artifact_dir is not None:
                print(f"E2E failure artifacts: {artifact_dir}")
        self.page.close()
        self.context.close()
        super().tearDown()

    def _record_console_message(self, message: ConsoleMessage) -> None:
        self.console_messages.append(f"[console:{message.type}] {message.text}")

    def _record_page_error(self, error: object) -> None:
        self.console_messages.append(f"[pageerror] {error}")

    def _current_test_failed(self) -> bool:
        outcome = getattr(self, "_outcome", None)
        if outcome is None:
            return False

        result = getattr(outcome, "result", None)
        if result is not None:
            failures = list(getattr(result, "failures", [])) + list(getattr(result, "errors", []))
            for test_case, _ in failures:
                if test_case is self:
                    return True

        for _, error in getattr(outcome, "errors", []):
            if error:
                return True

        return False

    def _capture_failure_artifacts(self) -> Path | None:
        artifact_dir = Path(tempfile.mkdtemp(prefix="cellular-automaton-e2e-artifacts-"))
        try:
            if not self.page.is_closed():
                self.page.screenshot(path=str(artifact_dir / "page.png"), full_page=True)
                (artifact_dir / "page.html").write_text(self.page.content(), encoding="utf-8")

            (artifact_dir / "console.txt").write_text(
                "\n".join(self.console_messages) if self.console_messages else "(no console messages)",
                encoding="utf-8",
            )

            try:
                backend_state = self.server.client.get_state()
                (artifact_dir / "backend-state.json").write_text(
                    json.dumps(backend_state, indent=2),
                    encoding="utf-8",
                )
            except Exception as exc:
                (artifact_dir / "backend-state-error.txt").write_text(str(exc), encoding="utf-8")

            try:
                backend_topology = self.server.client.get_topology()
                (artifact_dir / "backend-topology.json").write_text(
                    json.dumps(backend_topology, indent=2),
                    encoding="utf-8",
                )
            except Exception as exc:
                (artifact_dir / "backend-topology-error.txt").write_text(str(exc), encoding="utf-8")

            stdout_text = self.server.read_stdout()
            stderr_text = self.server.read_stderr()
            if stdout_text:
                (artifact_dir / "server-stdout.log").write_text(stdout_text, encoding="utf-8")
            if stderr_text:
                (artifact_dir / "server-stderr.log").write_text(stderr_text, encoding="utf-8")
            (artifact_dir / "server-log-paths.txt").write_text(
                f"stdout={self.server.stdout_path}\nstderr={self.server.stderr_path}\n",
                encoding="utf-8",
            )
        except Exception as exc:
            (artifact_dir / "artifact-capture-error.txt").write_text(str(exc), encoding="utf-8")
        return artifact_dir

    def _wait_for_page_bootstrapped(self, timeout_ms: int = 30_000) -> None:
        self.page.wait_for_selector("#grid", timeout=timeout_ms)
        self.page.wait_for_function("() => document.readyState === 'complete'", timeout=timeout_ms)
        self.page.wait_for_function(
            """() => {
                const grid = document.getElementById('grid');
                const statusText = document.getElementById('status-text');
                const gridSizeText = document.getElementById('grid-size-text')?.textContent?.trim() || '';
                const renderCellSize = Number(grid?.dataset.renderCellSize || 0);
                return Boolean(grid)
                    && Boolean(statusText)
                    && typeof statusText.textContent === 'string'
                    && statusText.textContent.trim().length > 0
                    && (
                        window.__appReady === true
                        || renderCellSize > 0
                        || (gridSizeText.length > 0 && gridSizeText !== '-- x --')
                    );
            }""",
            timeout=timeout_ms,
        )

    def _run_navigation_with_retry(
        self,
        navigate: Callable[[], Response | None],
        *,
        retries: int = 3,
    ) -> Response | None:
        last_error: PlaywrightError | PlaywrightTimeoutError | None = None
        for attempt in range(retries):
            try:
                return navigate()
            except (PlaywrightError, PlaywrightTimeoutError) as error:
                last_error = error
                if attempt == retries - 1:
                    raise
                time.sleep(0.2 * (attempt + 1))
        if last_error is not None:
            raise last_error
        raise AssertionError("navigation retry failed without an underlying Playwright error")

    def goto_page(
        self,
        url: str,
        *,
        wait_until: WaitUntilState | None = None,
        timeout: float | None = None,
    ) -> Response | None:
        return self._run_navigation_with_retry(
            lambda: self._goto_and_wait(url, wait_until=wait_until, timeout=timeout)
        )

    def reload_page(
        self,
        *,
        wait_until: WaitUntilState | None = None,
        timeout: float | None = None,
    ) -> Response | None:
        try:
            return self._run_navigation_with_retry(
                lambda: self._reload_and_wait(wait_until=wait_until, timeout=timeout)
            )
        except PlaywrightError:
            target_url = self.page.url or f"{self.server.client.base_url}/"
            return self.goto_page(target_url, wait_until=wait_until, timeout=timeout)

    def _goto_and_wait(
        self,
        url: str,
        *,
        wait_until: WaitUntilState | None = None,
        timeout: float | None = None,
    ) -> Response | None:
        with self._startup_watchdog(f"Navigation to {url!r}"):
            response = self.page.goto(url, wait_until=wait_until, timeout=timeout)
            self._wait_for_page_bootstrapped()
        return response

    def _reload_and_wait(
        self,
        *,
        wait_until: WaitUntilState | None = None,
        timeout: float | None = None,
    ) -> Response | None:
        with self._startup_watchdog("Page reload"):
            response = self.page.reload(wait_until=wait_until, timeout=timeout)
            self._wait_for_page_bootstrapped()
        return response
