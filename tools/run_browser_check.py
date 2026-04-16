from __future__ import annotations

import argparse
import datetime as dt
import os
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tests.e2e.browser_support.artifacts import (
    E2E_CAPTURE_SUCCESS_ARTIFACTS_ENV,
    capture_browser_failure_artifacts,
    create_artifact_dir,
    write_run_manifest,
)
from tests.e2e.support_runtime_host import (
    BrowserRuntimeHost,
    create_runtime_host,
)
from tools.render_canvas_review import (
    parse_cli_args as parse_render_canvas_review_cli_args,
    render_canvas_review,
    resolve_render_review_request,
)

EXTERNAL_RUNTIME_HOST_KIND_ENV = "E2E_EXTERNAL_RUNTIME_HOST_KIND"
EXTERNAL_RUNTIME_BASE_URL_ENV = "E2E_EXTERNAL_RUNTIME_BASE_URL"
EXTERNAL_RUNTIME_STDOUT_PATH_ENV = "E2E_EXTERNAL_RUNTIME_STDOUT_PATH"
EXTERNAL_RUNTIME_STDERR_PATH_ENV = "E2E_EXTERNAL_RUNTIME_STDERR_PATH"
DEFAULT_BROWSER_CHECK_DIR = ROOT_DIR / "output" / "browser-check"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a managed browser-backed check with host lifecycle, artifacts, and cleanup.",
    )
    parser.add_argument(
        "--host",
        choices=("auto", "standalone", "server"),
        default="auto",
        help="Runtime host kind. 'auto' defaults to standalone.",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        help="Optional artifact directory for logs, manifests, and delegated failure bundles.",
    )
    parser.add_argument(
        "--success-artifacts",
        action="store_true",
        help="Preserve browser-style success artifacts for managed --unittest runs.",
    )
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--render-review",
        action="store_true",
        help="Delegate to the render-review tool with the managed host.",
    )
    mode_group.add_argument(
        "--unittest",
        nargs="+",
        metavar="TARGET",
        help="Python unittest targets to run against the managed host.",
    )
    return parser


def resolve_host_kind(requested_kind: str) -> str:
    return "standalone" if requested_kind == "auto" else requested_kind


def resolve_default_artifact_dir(
    *,
    artifact_dir: Path | None,
    host_kind: str,
    mode_name: str,
) -> Path:
    if artifact_dir is not None:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        return artifact_dir
    timestamp = dt.datetime.now(tz=dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    return create_artifact_dir(
        name=f"{timestamp}-{mode_name}-{host_kind}",
        default_parent=DEFAULT_BROWSER_CHECK_DIR,
    )


def build_run_manifest(
    *,
    host_kind: str,
    mode_name: str,
    artifact_dir: Path,
) -> dict[str, Any]:
    return {
        "artifactDir": str(artifact_dir),
        "hostKind": host_kind,
        "mode": mode_name,
        "startedAt": dt.datetime.now(tz=dt.timezone.utc).isoformat(),
    }


def _host_port(host: BrowserRuntimeHost) -> int | None:
    parsed = urlparse(host.base_url)
    return parsed.port


def _write_host_logs(artifact_dir: Path, *, stdout_text: str, stderr_text: str, stem: str) -> None:
    (artifact_dir / f"{stem}-stdout.log").write_text(stdout_text, encoding="utf-8")
    (artifact_dir / f"{stem}-stderr.log").write_text(stderr_text, encoding="utf-8")


def _render_output_stem(*, family: str, patch_depth: int | None, cell_size: int | None) -> str:
    if patch_depth is not None:
        return f"{family}-depth-{patch_depth}"
    if cell_size is not None:
        return f"{family}-size-{cell_size}"
    return family


def ensure_render_review_outputs(
    review_args: Any,
    *,
    artifact_dir: Path,
) -> Any:
    if review_args.out is not None and review_args.summary_out is not None and (
        review_args.reference is None or review_args.montage_out is not None
    ):
        return review_args
    request = resolve_render_review_request(review_args)
    stem = _render_output_stem(
        family=request.family,
        patch_depth=request.patch_depth,
        cell_size=request.cell_size,
    )
    if review_args.out is None:
        review_args.out = artifact_dir / f"{stem}.png"
    if review_args.summary_out is None:
        review_args.summary_out = artifact_dir / f"{stem}.json"
    if review_args.reference is not None and review_args.montage_out is None:
        review_args.montage_out = artifact_dir / f"{stem}-montage.png"
    return review_args


def run_unittest_with_managed_host(
    *,
    host: BrowserRuntimeHost,
    host_kind: str,
    targets: list[str],
    artifact_dir: Path,
    run_manifest: dict[str, Any],
    success_artifacts: bool = False,
) -> int:
    env = os.environ.copy()
    env[EXTERNAL_RUNTIME_HOST_KIND_ENV] = host_kind
    env[EXTERNAL_RUNTIME_BASE_URL_ENV] = host.base_url
    env[EXTERNAL_RUNTIME_STDOUT_PATH_ENV] = str(getattr(host, "stdout_path", ""))
    env[EXTERNAL_RUNTIME_STDERR_PATH_ENV] = str(getattr(host, "stderr_path", ""))
    env["E2E_ARTIFACTS_DIR"] = str(artifact_dir / "test-artifacts")
    if success_artifacts:
        env[E2E_CAPTURE_SUCCESS_ARTIFACTS_ENV] = "1"
    process = subprocess.Popen(
        [sys.executable, "-m", "unittest", *targets],
        cwd=ROOT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        stdout_text, stderr_text = process.communicate()
    except KeyboardInterrupt:
        process.terminate()
        try:
            process.wait(timeout=5)
        except Exception:
            process.kill()
            process.wait(timeout=5)
        raise
    if stdout_text:
        sys.stdout.write(stdout_text)
    if stderr_text:
        sys.stderr.write(stderr_text)
    _write_host_logs(artifact_dir, stdout_text=stdout_text or "", stderr_text=stderr_text or "", stem="unittest")
    run_manifest["unittestTargets"] = targets
    if success_artifacts:
        run_manifest["successArtifactsRequested"] = True
        run_manifest["testArtifactsDir"] = str(artifact_dir / "test-artifacts")
    return int(process.returncode or 0)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args, remaining = parser.parse_known_args(argv)
    host_kind = resolve_host_kind(str(args.host))
    mode_name = "render-review" if args.render_review else "unittest"
    artifact_dir = resolve_default_artifact_dir(
        artifact_dir=args.artifact_dir,
        host_kind=host_kind,
        mode_name=mode_name,
    )
    run_manifest = build_run_manifest(
        host_kind=host_kind,
        mode_name=mode_name,
        artifact_dir=artifact_dir,
    )
    host: BrowserRuntimeHost | None = None
    exit_status = "failure"
    exit_code = 1
    try:
        host = create_runtime_host(host_kind)
        host.start()
        run_manifest["baseUrl"] = host.base_url
        run_manifest["port"] = _host_port(host)
        if args.render_review:
            review_args = ensure_render_review_outputs(
                parse_render_canvas_review_cli_args(remaining),
                artifact_dir=artifact_dir,
            )
            result = render_canvas_review(
                review_args,
                host=host,
                host_kind=host_kind,
                artifact_dir=artifact_dir,
                run_manifest=run_manifest,
            )
            run_manifest["renderPng"] = str(result.png_path)
            run_manifest["renderSummary"] = str(result.summary_path)
            if result.montage_path is not None:
                run_manifest["renderMontage"] = str(result.montage_path)
            if result.consistency_warnings:
                run_manifest["consistencyWarnings"] = list(result.consistency_warnings)
            exit_code = 0
        else:
            if remaining:
                parser.error(f"unexpected extra arguments for --unittest: {' '.join(remaining)}")
            exit_code = run_unittest_with_managed_host(
                host=host,
                host_kind=host_kind,
                targets=list(args.unittest),
                artifact_dir=artifact_dir,
                run_manifest=run_manifest,
                success_artifacts=bool(args.success_artifacts),
            )
        exit_status = "success" if exit_code == 0 else "failure"
        return exit_code
    except Exception as exc:
        run_manifest["failureReason"] = str(exc)
        if host is not None:
            capture_browser_failure_artifacts(
                artifact_dir,
                host=host,
                page=None,
                console_messages=[],
                run_manifest=run_manifest,
            )
        raise
    finally:
        if host is not None:
            host.close()
        run_manifest["exitStatus"] = exit_status
        run_manifest["stoppedAt"] = dt.datetime.now(tz=dt.timezone.utc).isoformat()
        manifest_path = write_run_manifest(artifact_dir, run_manifest)
        print(f"artifact_dir={artifact_dir}")
        print(f"run_manifest={manifest_path}")


if __name__ == "__main__":
    raise SystemExit(main())
