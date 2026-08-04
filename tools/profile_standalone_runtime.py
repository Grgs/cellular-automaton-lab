"""Profile standalone cold start and live-fork startup/memory in Chromium."""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import threading
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Final

from playwright.sync_api import CDPSession, Page, ViewportSize, sync_playwright

ROOT_DIR: Final[Path] = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tests.e2e.support_runtime_host import (  # noqa: E402
    load_standalone_build_manifest,
    missing_standalone_output_files,
)
from tools.standalone_runtime_budget import (  # noqa: E402
    DEFAULT_RUNTIME_BUDGET_PATH,
    evaluate_runtime_report,
    load_runtime_budget,
)

DEFAULT_VIEWPORT: Final[ViewportSize] = {"width": 1280, "height": 720}


@dataclass(frozen=True)
class ForkSample:
    fork_id: str
    startup_ms: float
    memory_bytes: int
    incremental_memory_bytes: int


@dataclass(frozen=True)
class RuntimeSample:
    cold_start_ms: float
    browser_baseline_memory_bytes: int
    main_runtime_memory_bytes: int
    forks: list[ForkSample]
    peak_browser_memory_bytes: int
    after_dispose_browser_memory_bytes: int


class _ProfileRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:
        del format, args


class CrossOriginIsolatedStandaloneHost:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        handler = partial(_ProfileRequestHandler, directory=str(output_dir))
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.server.daemon_threads = True
        port = int(self.server.server_address[1])
        self.base_url = f"http://127.0.0.1:{port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> CrossOriginIsolatedStandaloneHost:
        self.thread.start()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        del exc_type, exc, traceback
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def _browser_process_ids(browser_session: CDPSession) -> list[int]:
    payload = browser_session.send("SystemInfo.getProcessInfo")
    process_info = payload.get("processInfo")
    if not isinstance(process_info, list):
        raise RuntimeError(f"invalid Chromium process metadata: {payload!r}")
    process_ids: list[int] = []
    for process in process_info:
        if not isinstance(process, dict):
            continue
        process_id = process.get("id")
        if isinstance(process_id, int) and process_id > 0:
            process_ids.append(process_id)
    if not process_ids:
        raise RuntimeError("Chromium did not report any process ids")
    return process_ids


def _linux_process_rss_bytes(process_id: int) -> int:
    status_path = Path(f"/proc/{process_id}/status")
    try:
        status = status_path.read_text(encoding="utf-8")
    except (FileNotFoundError, ProcessLookupError):
        return 0
    for line in status.splitlines():
        if line.startswith("VmRSS:"):
            fields = line.split()
            if len(fields) >= 2:
                return int(fields[1]) * 1024
    return 0


def _windows_process_rss_bytes(process_ids: list[int]) -> int:
    id_expression = ",".join(str(process_id) for process_id in process_ids)
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            f"(Get-Process -Id {id_expression} -ErrorAction SilentlyContinue | Measure-Object WorkingSet64 -Sum).Sum",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(f"could not read Chromium process memory: {result.stderr.strip()}")
    return int(result.stdout.strip())


def _posix_process_rss_bytes(process_ids: list[int]) -> int:
    result = subprocess.run(
        ["ps", "-o", "rss=", "-p", ",".join(str(process_id) for process_id in process_ids)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in {0, 1}:
        raise RuntimeError(f"could not read Chromium process memory: {result.stderr.strip()}")
    return sum(int(value) * 1024 for value in result.stdout.split())


def _measure_browser_process_memory_bytes(browser_session: CDPSession) -> int:
    process_ids = _browser_process_ids(browser_session)
    if sys.platform.startswith("linux") and Path("/proc").is_dir():
        memory_bytes = sum(_linux_process_rss_bytes(process_id) for process_id in process_ids)
    elif os.name == "nt":
        memory_bytes = _windows_process_rss_bytes(process_ids)
    else:
        memory_bytes = _posix_process_rss_bytes(process_ids)
    if memory_bytes <= 0:
        raise RuntimeError("Chromium process RSS measurement returned no memory")
    return memory_bytes


def _profile_sample(
    page: Page,
    *,
    browser_session: CDPSession,
    browser_baseline_memory_bytes: int,
    base_url: str,
    forks_per_run: int,
    timeout_seconds: float,
) -> tuple[RuntimeSample, dict[str, object]]:
    timeout_ms = int(timeout_seconds * 1000)
    page.set_default_timeout(timeout_ms)
    page.set_default_navigation_timeout(timeout_ms)
    page.goto(base_url + "/", wait_until="load")
    page.wait_for_function(
        """() => window.__appReady === true &&
            window.__sf !== undefined""",
        timeout=timeout_ms,
    )
    page.evaluate(
        """() => {
            const liveForks = window.__sf;
            const activeForks = new Map();
            let nextForkId = 1;
            window.__standaloneRuntimeProfileApi = {
                async startLiveFork() {
                    const maxConcurrent = liveForks.maxConcurrent;
                    if (maxConcurrent !== undefined && activeForks.size >= maxConcurrent) {
                        throw new Error(`Standalone runtime profile is limited to ${maxConcurrent} live forks.`);
                    }
                    const forkId = `profile-${nextForkId++}`;
                    const backend = liveForks.backendFactory(`${liveForks.baseSessionId}-${forkId}`);
                    activeForks.set(forkId, backend);
                    const startedAt = performance.now();
                    try {
                        await backend.getState();
                        return { forkId, startupMs: performance.now() - startedAt };
                    } catch (error) {
                        activeForks.delete(forkId);
                        backend.dispose();
                        throw error;
                    }
                },
                disposeAll() {
                    for (const backend of activeForks.values()) {
                        backend.dispose();
                    }
                    activeForks.clear();
                },
            };
        }"""
    )

    cold_start_ms = page.evaluate("() => window.__standaloneStartupMs")
    if not isinstance(cold_start_ms, (int, float)):
        raise RuntimeError(f"invalid standalone cold-start measurement: {cold_start_ms!r}")

    browser_metadata = page.evaluate(
        """() => ({
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            hardwareConcurrency: navigator.hardwareConcurrency,
            deviceMemoryGiB: navigator.deviceMemory ?? null,
            crossOriginIsolated: window.crossOriginIsolated,
        })"""
    )
    if not isinstance(browser_metadata, dict):
        raise RuntimeError(f"invalid browser metadata: {browser_metadata!r}")

    previous_memory = _measure_browser_process_memory_bytes(browser_session)
    main_runtime_memory = previous_memory - browser_baseline_memory_bytes
    fork_samples: list[ForkSample] = []
    for _ in range(forks_per_run):
        fork_result = page.evaluate("() => window.__standaloneRuntimeProfileApi.startLiveFork()")
        if not isinstance(fork_result, dict):
            raise RuntimeError(f"invalid live-fork profile result: {fork_result!r}")
        fork_id = fork_result.get("forkId")
        startup_ms = fork_result.get("startupMs")
        if not isinstance(fork_id, str) or not isinstance(startup_ms, (int, float)):
            raise RuntimeError(f"invalid live-fork profile result: {fork_result!r}")
        memory_bytes = _measure_browser_process_memory_bytes(browser_session)
        fork_samples.append(
            ForkSample(
                fork_id=fork_id,
                startup_ms=float(startup_ms),
                memory_bytes=memory_bytes,
                incremental_memory_bytes=memory_bytes - previous_memory,
            )
        )
        previous_memory = memory_bytes

    page.evaluate("() => window.__standaloneRuntimeProfileApi.disposeAll()")
    page.wait_for_timeout(250)
    after_dispose_memory = _measure_browser_process_memory_bytes(browser_session)
    return (
        RuntimeSample(
            cold_start_ms=float(cold_start_ms),
            browser_baseline_memory_bytes=browser_baseline_memory_bytes,
            main_runtime_memory_bytes=main_runtime_memory,
            forks=fork_samples,
            peak_browser_memory_bytes=max(
                [previous_memory, *(sample.memory_bytes for sample in fork_samples)]
            ),
            after_dispose_browser_memory_bytes=after_dispose_memory,
        ),
        browser_metadata,
    )


def _median(values: list[float | int]) -> float:
    return float(statistics.median(values))


def summarize_samples(samples: list[RuntimeSample], *, forks_per_run: int) -> dict[str, object]:
    fork_summaries: list[dict[str, object]] = []
    for index in range(forks_per_run):
        fork_summaries.append(
            {
                "ordinal": index + 1,
                "startupMsMedian": _median([sample.forks[index].startup_ms for sample in samples]),
                "startupMsMax": max(sample.forks[index].startup_ms for sample in samples),
                "incrementalMemoryBytesMedian": _median(
                    [sample.forks[index].incremental_memory_bytes for sample in samples]
                ),
                "incrementalMemoryBytesMax": max(
                    sample.forks[index].incremental_memory_bytes for sample in samples
                ),
            }
        )
    return {
        "coldStartMsMedian": _median([sample.cold_start_ms for sample in samples]),
        "coldStartMsMax": max(sample.cold_start_ms for sample in samples),
        "mainRuntimeMemoryBytesMedian": _median(
            [sample.main_runtime_memory_bytes for sample in samples]
        ),
        "browserBaselineMemoryBytesMedian": _median(
            [sample.browser_baseline_memory_bytes for sample in samples]
        ),
        "peakBrowserMemoryBytesMedian": _median(
            [sample.peak_browser_memory_bytes for sample in samples]
        ),
        "peakBrowserMemoryBytesMax": max(sample.peak_browser_memory_bytes for sample in samples),
        "forks": fork_summaries,
    }


def profile_standalone_runtime(
    *,
    repeats: int,
    forks_per_run: int,
    cpu_throttle_rate: float,
    timeout_seconds: float,
    output_dir: Path,
) -> dict[str, object]:
    missing = missing_standalone_output_files(output_dir)
    if missing:
        raise RuntimeError(
            "standalone bundle is missing required outputs: "
            + ", ".join(missing)
            + " — build it first with `python -m tools build standalone`."
        )

    samples: list[RuntimeSample] = []
    browser_metadata: dict[str, object] | None = None
    browser_version = ""
    with CrossOriginIsolatedStandaloneHost(output_dir) as host:
        with sync_playwright() as playwright:
            for _ in range(repeats):
                browser = playwright.chromium.launch(headless=True)
                try:
                    browser_version = browser.version
                    browser_session = browser.new_browser_cdp_session()
                    context = browser.new_context(viewport=DEFAULT_VIEWPORT)
                    try:
                        page = context.new_page()
                        browser_baseline_memory = _measure_browser_process_memory_bytes(
                            browser_session
                        )
                        cdp_session = context.new_cdp_session(page)
                        cdp_session.send(
                            "Emulation.setCPUThrottlingRate", {"rate": cpu_throttle_rate}
                        )
                        sample, current_metadata = _profile_sample(
                            page,
                            browser_session=browser_session,
                            browser_baseline_memory_bytes=browser_baseline_memory,
                            base_url=host.base_url,
                            forks_per_run=forks_per_run,
                            timeout_seconds=timeout_seconds,
                        )
                        samples.append(sample)
                        browser_metadata = current_metadata
                    finally:
                        context.close()
                finally:
                    browser.close()

    if browser_metadata is None:
        raise RuntimeError("standalone runtime profile did not collect browser metadata")
    browser_metadata = {"browserVersion": browser_version, **browser_metadata}
    return {
        "schemaVersion": 1,
        "measuredAt": datetime.now(UTC).isoformat(),
        "profile": {
            "name": "emulated-lower-end-desktop",
            "cpuThrottleRate": cpu_throttle_rate,
            "repeats": repeats,
            "forksPerRun": forks_per_run,
            "viewport": DEFAULT_VIEWPORT,
            "expectation": (
                "Chromium with CPU throttling approximates a lower-end desktop CPU; "
                "memory is unthrottled aggregate Chromium process RSS."
            ),
            "memoryMeasurement": "aggregate-chromium-process-rss",
        },
        "host": {
            "platform": platform.platform(),
            "pythonVersion": platform.python_version(),
        },
        "browser": browser_metadata,
        "standaloneBuild": load_standalone_build_manifest(output_dir),
        "samples": [asdict(sample) for sample in samples],
        "summary": summarize_samples(samples, forks_per_run=forks_per_run),
    }


def _mib(value: float | int) -> str:
    return f"{float(value) / (1024 * 1024):.1f} MiB"


def render_summary(report: dict[str, object]) -> str:
    profile = report["profile"]
    summary = report["summary"]
    if not isinstance(profile, dict) or not isinstance(summary, dict):
        raise ValueError("invalid standalone runtime profile report")
    lines = [
        "Standalone runtime profile",
        (
            f"profile: {profile['name']} | CPU throttle {profile['cpuThrottleRate']}x | "
            f"{profile['repeats']} repeats | {profile['forksPerRun']} forks/run"
        ),
        (
            f"cold start: median {summary['coldStartMsMedian']:.1f} ms | "
            f"max {summary['coldStartMsMax']:.1f} ms"
        ),
        f"main runtime memory: median {_mib(summary['mainRuntimeMemoryBytesMedian'])}",
        (
            f"peak browser RSS: median {_mib(summary['peakBrowserMemoryBytesMedian'])} | "
            f"max {_mib(summary['peakBrowserMemoryBytesMax'])}"
        ),
    ]
    forks = summary.get("forks")
    if isinstance(forks, list):
        for fork in forks:
            if isinstance(fork, dict):
                lines.append(
                    f"fork {fork['ordinal']}: startup median {fork['startupMsMedian']:.1f} ms "
                    f"(max {fork['startupMsMax']:.1f} ms) | incremental memory median "
                    f"{_mib(fork['incrementalMemoryBytesMedian'])}"
                )
    budget_evaluation = report.get("budgetEvaluation")
    if isinstance(budget_evaluation, dict):
        limit = budget_evaluation.get("coldStartLimitMs")
        violations = budget_evaluation.get("violations")
        if isinstance(limit, (int, float)) and isinstance(violations, list):
            status = "PASS" if not violations else "FAIL"
            lines.append(f"cold-start budget: {status} | limit {float(limit):.1f} ms")
            lines.extend(f"  - {violation}" for violation in violations)
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=3, help="fresh browser runs (default: 3)")
    parser.add_argument(
        "--forks",
        type=int,
        choices=(1, 2),
        default=2,
        help="live forks retained per run (default: 2)",
    )
    parser.add_argument(
        "--cpu-throttle-rate",
        type=float,
        default=4.0,
        help="Chromium CPU slowdown multiplier (default: 4)",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=90.0,
        help="per browser operation timeout (default: 90)",
    )
    parser.add_argument(
        "--build-dir",
        type=Path,
        default=ROOT_DIR / "output" / "standalone",
        help="standalone build directory",
    )
    parser.add_argument(
        "--budget",
        type=Path,
        default=DEFAULT_RUNTIME_BUDGET_PATH,
        help="runtime budget policy (default: tools/standalone_runtime_budget.json)",
    )
    parser.add_argument(
        "--check-budget",
        action="store_true",
        help="fail when the report profile or cold-start maximum violates the policy",
    )
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    parser.add_argument("--output", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.repeats < 1:
        parser.error("--repeats must be at least 1")
    if args.cpu_throttle_rate < 1:
        parser.error("--cpu-throttle-rate must be at least 1")
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")

    try:
        budget = load_runtime_budget(args.budget)
        report = profile_standalone_runtime(
            repeats=args.repeats,
            forks_per_run=args.forks,
            cpu_throttle_rate=args.cpu_throttle_rate,
            timeout_seconds=args.timeout_seconds,
            output_dir=args.build_dir.resolve(),
        )
    except Exception as exc:
        parser.exit(1, f"standalone runtime profile failed: {exc}\n")
    violations = evaluate_runtime_report(report, budget)
    report["budget"] = budget.to_report_payload()
    report["budgetEvaluation"] = {
        "coldStartLimitMs": budget.cold_start_limit_ms,
        "passed": not violations,
        "violations": list(violations),
    }
    rendered = (
        json.dumps(report, indent=2, sort_keys=True)
        if args.format == "json"
        else render_summary(report)
    )
    print(rendered)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 1 if args.check_budget and violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
