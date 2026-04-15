from __future__ import annotations

import _thread
import os
import threading
import time
import unittest
from collections.abc import Callable, Iterator
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

from tests.e2e.support_runtime_host import BrowserRuntimeHost, create_runtime_host
from tests.e2e.support_server import JsonApiClient
from tests.e2e.browser_support.artifacts import (
    E2E_ARTIFACTS_DIR_ENV,
    capture_browser_failure_artifacts,
    create_artifact_dir,
)
from tests.e2e.browser_support.render_review import wait_for_page_bootstrapped

WaitUntilState = Literal["commit", "domcontentloaded", "load", "networkidle"]


class BrowserAppTestCase(unittest.TestCase):
    page_viewport: ClassVar[ViewportSize | None] = None
    startup_timeout_seconds: ClassVar[float] = 45.0
    runtime_host_kind: ClassVar[str] = "server"
    host: ClassVar[BrowserRuntimeHost]
    api: ClassVar[JsonApiClient | None]
    playwright: ClassVar[Playwright]
    browser: ClassVar[Browser]
    context: BrowserContext
    page: Page

    @classmethod
    @contextmanager
    def _startup_watchdog(
        cls,
        description: str,
        timeout_seconds: float | None = None,
    ) -> Iterator[None]:
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
        cls.host = create_runtime_host(cls.runtime_host_kind)
        with cls._startup_watchdog(f"{cls.runtime_host_kind} browser runtime host"):
            cls.host.start()
        cls.api = cls.host.client()
        with cls._startup_watchdog("Playwright runtime"):
            cls.playwright = sync_playwright().start()
        with cls._startup_watchdog("Chromium browser"):
            cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close()
        cls.playwright.stop()
        cls.host.close()
        super().tearDownClass()

    def setUp(self) -> None:
        super().setUp()
        with self._startup_watchdog(f"{self.runtime_host_kind} host test setup"):
            self.host.before_test()
        type(self).api = self.host.client()
        with self._startup_watchdog("Browser test page context"):
            if self.page_viewport is None:
                self.context = self.browser.new_context(accept_downloads=True)
            else:
                self.context = self.browser.new_context(
                    accept_downloads=True,
                    viewport=self.page_viewport,
                )
            self.context.grant_permissions(
                ["clipboard-read", "clipboard-write"],
                origin=self.host.base_url,
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

    def _artifact_root(self) -> Path | None:
        configured_root = os.environ.get(E2E_ARTIFACTS_DIR_ENV)
        return Path(configured_root) if configured_root else None

    def _create_artifact_dir(self) -> Path:
        return create_artifact_dir(
            name=self.id(),
            root=self._artifact_root(),
            temp_prefix="cellular-automaton-e2e-artifacts-",
        )

    def _capture_failure_artifacts(self) -> Path | None:
        artifact_dir = self._create_artifact_dir()
        try:
            capture_browser_failure_artifacts(
                artifact_dir,
                host=self.host,
                page=self.page,
                console_messages=self.console_messages,
                run_manifest={
                    "baseUrl": self.host.base_url,
                    "exitStatus": "test-failure",
                    "hostKind": self.runtime_host_kind,
                    "testId": self.id(),
                },
            )
        except Exception as exc:
            (artifact_dir / "artifact-capture-error.txt").write_text(str(exc), encoding="utf-8")
        return artifact_dir

    def _wait_for_page_bootstrapped(self, timeout_ms: int = 30_000) -> None:
        wait_for_page_bootstrapped(self.page, timeout_ms=timeout_ms)

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
            target_url = self.page.url or f"{self.host.base_url}/"
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
